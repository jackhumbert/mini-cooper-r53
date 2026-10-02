"""Offline tests: PRG parsing, safety policy, decoding, and the CLI against a replay fixture.

    python -m unittest discover tests
"""
import io
import os
import json
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from r53diag import cli, config, decode, kb, prg
from r53diag.backends import ReplayBackend, make_backend

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic-not-bridged.jsonl"
HAVE_EDIABAS = Path(r"C:\EDIABAS\Ecu\EMS2K.prg").exists()


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(["--no-record", "--compact", *argv])
    text = out.getvalue().strip()
    return rc, (json.loads(text) if text and not text.startswith("{\"t\"") else text)


@unittest.skipUnless(HAVE_EDIABAS, "needs C:\\EDIABAS\\Ecu")
class PrgTests(unittest.TestCase):
    def test_ems2k(self):
        s = prg.load(prg.find("EMS2K"))
        self.assertIn("FS_LESEN", s.jobs)
        self.assertEqual(len(s.tables["FORTTEXTE"]), 250)
        self.assertEqual(s.tables["ACTUATOR_TEST"][1]["NAME"], "FUEL_PUMP")

    def test_group(self):
        s = prg.load(prg.find("D_0080"))
        self.assertTrue(s.is_group)
        self.assertIn("KOMBI50F", " ".join(s.header.get("ECUCOMMENT", [])).upper())


class SafetyTests(unittest.TestCase):
    DANGEROUS = ["C_FG_AUFTRAG", "FLASH_SCHREIBEN", "WRITE_MEMORY", "LEARN_IMOB_SEED", "ISN_LESEN",
                 "SEED_KEY", "GWSZ_RESET", "IDENT_VIN_SCHREIBEN", "SWITCH_TO_BOOT", "SCHL_DATEN_LESEN",
                 "PASSWORT_LESEN", "LENKWINKEL_DSC_ABGLEICHEN", "START_DIAGNOSTIC_SESSION", "SOME_NEW_JOB"]

    def test_blocked(self):
        for j in self.DANGEROUS:
            self.assertEqual(kb.classify("EMS2K", j)[0], kb.BLOCKED, j)

    def test_tiers(self):
        self.assertEqual(kb.classify("EMS2K", "FS_LESEN")[0], kb.READ)
        self.assertEqual(kb.classify("EMS2K", "STATUS_ANA_ENGINE4")[0], kb.READ)
        self.assertEqual(kb.classify("EMS2K", "FS_LOESCHEN")[0], kb.CONFIRM)
        self.assertEqual(kb.classify("EMS2K", "STEUERN_ACTUATOR")[0], kb.CONFIRM)

    def test_catalog_has_no_unclassified_jobs(self):
        for f in (kb.KB / "catalog").glob("*.json"):
            cat = json.loads(f.read_text(encoding="utf-8"))
            for name in cat["jobs"]:
                tier, why = kb.classify(cat["sgbd"], name)
                self.assertFalse(why.startswith("unclassified"), f"{cat['sgbd']}.{name}")

    def test_every_write_is_blocked(self):
        for f in (kb.KB / "catalog").glob("*.json"):
            cat = json.loads(f.read_text(encoding="utf-8"))
            for name in cat["jobs"]:
                if re.search(r"SCHREIBEN|WRITE|FLASH|AUFTRAG", name):
                    self.assertEqual(kb.classify(cat["sgbd"], name)[0], kb.BLOCKED, name)

    def test_runner_refuses_blocked_even_with_confirm(self):
        rc, res = run_cli("--replay", str(FIXTURE), "run", "dme", "WRITE_MEMORY", "--confirm")
        self.assertEqual(rc, 2)
        self.assertIn("blocked", res["refused"])

    def test_confirm_needed(self):
        rc, res = run_cli("--replay", str(FIXTURE), "clear", "dme")
        self.assertEqual(rc, 2)


class DecodeTests(unittest.TestCase):
    def setUp(self):
        self.rb = ReplayBackend(FIXTURE)

    def test_faults(self):
        f = decode.faults(self.rb.job("EMS2K", "FS_LESEN"), "EMS2K")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["code"], "0x113C")
        self.assertEqual(f[0]["count"], 3)
        self.assertEqual(len(f[0]["types"]), 1)          # "--" placeholder dropped
        self.assertEqual(f[0]["environment"][0]["unit"], "1/min")

    def test_values(self):
        v = decode.values(self.rb.job("EMS2K", "STATUS_UBATT"), "EMS2K")
        self.assertEqual(v[0]["name"], "STAT_UBATT")
        self.assertEqual(v[0]["value"], 12.62)
        self.assertEqual(v[0]["unit"], "V")


class CliReplayTests(unittest.TestCase):
    def test_scan_hints_bridge(self):
        rc, res = run_cli("--replay", str(FIXTURE), "scan")
        self.assertEqual(rc, 0)
        self.assertEqual(res["responding"]["dme"]["sgbd"], "EMS2K")
        self.assertIn("kombi", [m["module"] for m in res["not_responding"]])
        self.assertTrue(any("7+8" in h for h in res["hints"]))

    def test_status(self):
        rc, res = run_cli("--replay", str(FIXTURE), "status", "dme", "STATUS_UBATT")
        self.assertEqual(rc, 0)
        self.assertEqual(res["values"][0]["value"], 12.62)


class BackendConfigTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_ediabaslib_init_config(self):
        os.environ["R53_COM_PORT"] = "com9"
        os.environ["R53_ECU_PATH"] = r"D:\sgbd"
        cfg = dict(kv.split("=", 1) for kv in config.ediabaslib_init_config(Path(r"C:\t")).split(";"))
        self.assertEqual(cfg["ObdComPort"], "COM9")
        self.assertEqual(cfg["EcuPath"], r"D:\sgbd")
        self.assertEqual(cfg["Interface"], "STD:OBD")
        self.assertEqual(cfg["TracePath"], r"C:\t")
        self.assertEqual(cfg["IfhTrace"], "3")

    def test_missing_ediabaslib_is_reported(self):
        os.environ["R53_EDIABASLIB"] = r"C:\nonexistent\Api64.dll"
        with self.assertRaises(FileNotFoundError):
            make_backend("ediabaslib")
        rc, res = run_cli("--backend", "ediabaslib", "status", "dme", "STATUS_UBATT")
        self.assertEqual(rc, 1)
        self.assertIn("install_ediabaslib", res["error"])

    def test_backend_env_default(self):
        os.environ["R53_BACKEND"] = "ediabaslib"
        self.assertEqual(config.default_backend(), "ediabaslib")
        os.environ["R53_BACKEND"] = "bogus"
        self.assertEqual(config.default_backend(), "ediabas")


if __name__ == "__main__":
    unittest.main()

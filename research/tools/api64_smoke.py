import ctypes, time
from ctypes import c_uint, c_int, c_char_p, c_ushort, byref, create_string_buffer
api = ctypes.WinDLL(r"C:\EDIABAS\Bin\api64.dll")
h = c_uint(0)
ok = api.__apiInit(byref(h)); print("apiInit", ok, h.value)
api.__apiJob(h, b"EMS2K", b"_JOBS", b"", b"")
t=time.time()
while api.__apiState(h) == 0 and time.time()-t < 15: time.sleep(0.05)
st = api.__apiState(h); print("state", st)
if st == 3:
    buf = create_string_buffer(256); api.__apiErrorText(h, buf, 256); print("err", api.__apiErrorCode(h), buf.value)
sets = c_ushort(0); api.__apiResultSets(h, byref(sets)); print("sets", sets.value)
buf = create_string_buffer(256)
names=[]
for s in range(1, sets.value+1):
    if api.__apiResultText(h, buf, b"JOBNAME", c_ushort(s), b""): names.append(buf.value.decode('latin1'))
print(len(names), names[:12])
api.__apiEnd(h)

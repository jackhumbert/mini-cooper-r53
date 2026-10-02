import sys,re
d=open(sys.argv[1],'rb').read()
x=bytes(b^0xF7 for b in d)
for blob in (d,x):
    for m in re.finditer(rb'[\x20-\x7e\xc0-\xff]{4,}',blob):
        s=m.group().decode('latin1')
        print(s)

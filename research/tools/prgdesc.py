import struct,sys
def dec(b): return bytes(x^0xF7 for x in b)
f=sys.argv[1]; d=open(f,'rb').read()
p=struct.unpack_from('<I',d,0x90)[0]
n=struct.unpack_from('<I',d,p)[0]
t=dec(d[p+4:p+4+n]).decode('latin1')
print(t)

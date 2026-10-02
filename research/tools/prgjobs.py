import struct,sys,re
def dec(b): return bytes(x^0xF7 for x in b)
def jobs(d):
    p=struct.unpack_from('<I',d,0x88)[0]
    n=struct.unpack('<i',d[p:p+4])[0]
    return [dec(d[p+4+i*0x44:p+4+i*0x44+0x40]).split(b'\0')[0].decode('latin1') for i in range(n)]
def info(d):
    p=struct.unpack_from('<I',d,0x90)[0]
    t=dec(d[p+4:p+4000]).split(b'\0')[0].decode('latin1')
    return t
if __name__=='__main__':
    for f in sys.argv[1:]:
        d=open(f,'rb').read()
        inf=info(d); keep=[l for l in inf.split('\n') if re.match(r'(ECU|ORIGIN|REVISION|PACKAGE|SPRACHE|COMMENT|ECUCOMMENT|LANGUAGE):',l)]
        j=jobs(d)
        print('##',f.split('/')[-1],'|',' ; '.join(keep[:6]).replace('\r',''),'| jobs=%d'%len(j)); print(' '.join(j)); print()

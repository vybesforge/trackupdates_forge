"""Integrate zw_ext.kn5: trim zwiss Berm (highway_SUB1) where the new ground band takes over, add model + surfaces entries."""
import sys,os,struct,re,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'));import kn5patch as K
ROOT=os.path.join(os.path.dirname(__file__),'..','..');Z=f'{ROOT}/vf_i29_speedway';SRC='/workspace/rpotm/backup/zw_rpm.kn5.pre_north'
d=bytearray(open(SRC,'rb').read());_,nodes=K.scan(SRC);n=0
for name,o,l,c in nodes:
    if c==2 and name=='highway_SUB1':
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d),'<f4',nv*11,q+4).reshape(nv,11);q+=4+nv*44
        ni,=struct.unpack_from('<I',d,q);I=np.frombuffer(bytes(d),'<u2',ni,q+4).reshape(-1,3).copy()
        cz=V[I][:,:,2].mean(1);cx=V[I][:,:,0].mean(1);cut=(cz<-2632)|((cx<-335)&(cz<-2500)&(cx>-1000));I[cut]=I[cut][:,[0]];n=int(cut.sum());d[q+4:q+4+ni*2]=I.astype('<u2').tobytes()
open(f'{Z}/vf_i29_speedway.kn5','wb').write(bytes(d));print('Berm tris hidden (north of z -2632 + US-34 berm in drivable band):',n)
for lay in('main','short'):
    p=f'{Z}/models_{lay}.ini';s=open(p,'rb').read().decode()
    if 'zw_ext.kn5' not in s:
        k=max(int(x) for x in re.findall(r'\[MODEL_(\d+)\]',s))+1
        s=s.rstrip('\r\n')+f'\r\n\r\n[MODEL_{k}]\r\nFILE=zw_ext.kn5\r\nPOSITION=0,0,0\r\nROTATION=0,0,0\r\n'
        open(p,'wb').write(s.encode())
    p=f'{Z}/{lay}/data/surfaces.ini';s=open(p,'rb').read().decode()
    if 'KEY=XROAD' not in s:
        k=max(int(x) for x in re.findall(r'\[SURFACE_(\d+)\]',s))+1;add=''
        for key,fr,com in(('XROAD',0.97,'public roads of the north extension (190th St, 188th St, US-34 crossing)'),('XLOT',0.95,'fuel-station / business lots')):
            add+=f'\r\n; --- added north extension: {com}. Drivable, off-course: not valid track, no black flag\r\n[SURFACE_{k}]\r\nKEY={key}\r\nFRICTION={fr}\r\nDAMPING=0\r\nWAV=\r\nWAV_PITCH=0\r\nFF_EFFECT=NULL\r\nDIRT_ADDITIVE=0\r\nIS_VALID_TRACK=0\r\nBLACK_FLAG_TIME=0\r\nSIN_HEIGHT=0\r\nSIN_LENGTH=0\r\nIS_PITLANE=0\r\nVIBRATION_GAIN=0\r\nVIBRATION_LENGTH=0\r\n';k+=1
        open(p,'wb').write((s.rstrip('\r\n')+'\r\n'+add).encode())
print(open(f'{Z}/models_main.ini').read())

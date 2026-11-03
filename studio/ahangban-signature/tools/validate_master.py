"""Validate the immutable source artwork and exact 12-frame final composite."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageOps,ImageChops

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    d=json.loads((ROOT/'environment-lock.json').read_text())
    path=ROOT/d['master'];im=Image.open(path).convert('RGB')
    assert sha(path)==d['masterSha256']
    assert im.size==(3840,2160) and im.width*9==im.height*16
    assert d['seatingCount']==2
    assert d['portraitCount']==12 and len(d['portraits'])==12
    assert len({p['file'] for p in d['portraits']})==12
    for row in (1,2):
        reading=[p for p in d['portraits'] if p['row']==row]
        assert [p['columnFromRight'] for p in reading]==list(range(1,7))
        assert all(reading[i]['frameBounds'][0]>reading[i+1]['frameBounds'][0] for i in range(5))
        portraits=sorted(reading,key=lambda p:p['frameBounds'][0])
        assert len(portraits)==6
        assert len({p['frameBounds'][1] for p in portraits})==1
        assert len({p['frameBounds'][3] for p in portraits})==1
        for i,p in enumerate(portraits):
            x,y,xx,yy=p['frameBounds'];assert (xx-x,yy-y)==tuple(d['frameDimensions'])
            if i:assert x-portraits[i-1]['frameBounds'][2]==d['horizontalFrameGap']
    for p in d['portraits']:
        source=ROOT/'references'/p['file'];assert sha(source)==p['sha256']
        displayed=im.crop(p['imageBounds'])
        expected=ImageOps.exif_transpose(Image.open(source)).convert('RGB').resize(displayed.size,Image.Resampling.LANCZOS)
        assert displayed.tobytes()==expected.tobytes(),p['file']
    source=ROOT/d['logo']['source'];assert sha(source)==d['logo']['sourceSha256']
    assert d['logo']['baseVisibility']=='blank; no logo baked into master'
    logo=Image.open(source).convert('RGBA').crop(d['logo']['transparentPaddingCrop'])
    x,y,xx,yy=d['logo']['bounds'];logo=logo.resize((xx-x,yy-y),Image.Resampling.LANCZOS)
    corepath=ROOT/d['logo']['coreOverlay'];assert sha(corepath)==d['logo']['coreOverlaySha256']
    core=Image.open(corepath).convert('RGBA');assert core.size==im.size
    normalized=Image.new('RGBA',logo.size,(0,0,0,0));normalized.alpha_composite(logo)
    assert core.crop((x,y,xx,yy)).tobytes()==normalized.tobytes()
    plate=Image.open(ROOT/d['architectureSource']).convert('RGB').crop(d['architectureCrop']).resize(im.size,Image.Resampling.LANCZOS)
    assert im.crop((x,y,xx,yy)).tobytes()==plate.crop((x,y,xx,yy)).tobytes(), 'Logo must remain absent from base'
    glowpath=ROOT/d['logo']['glowOverlay'];assert sha(glowpath)==d['logo']['glowOverlaySha256']
    glow=Image.open(glowpath);assert glow.mode=='RGBA' and glow.size==im.size and glow.getchannel('A').getbbox()
    people=json.loads((ROOT/'Presenters/character-lock.json').read_text())
    assert {p['displayNameEn'] for p in people['characters']}=={'Ava','Sajad'}
    for person in people['characters']:
        assert person['primaryReference'] in [p['path'] for p in person['references']]
        for ref in person['references']:assert sha(ROOT/ref['path'])==ref['sha256']
    assert d['additionalCameraViewsGenerated']==0
    print('PASS: blank-logo 16:9 master; 12 unchanged portraits in RTL reading order; separate unchanged logo core and glow; two chairs; five unchanged Ava/Sajad references; no extra views.')

if __name__=='__main__':main()

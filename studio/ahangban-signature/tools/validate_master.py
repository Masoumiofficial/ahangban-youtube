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
        portraits=[p for p in d['portraits'] if p['row']==row]
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
    logo=Image.open(source).convert('RGBA').crop(d['logo']['transparentPaddingCrop'])
    x,y,xx,yy=d['logo']['bounds'];logo=logo.resize((xx-x,yy-y),Image.Resampling.LANCZOS)
    difference=ImageChops.difference(im.crop((x,y,xx,yy)),logo.convert('RGB'))
    fullyopaque=logo.getchannel('A').point(lambda a:255 if a==255 else 0)
    assert ImageChops.multiply(difference,Image.merge('RGB',(fullyopaque,)*3)).getbbox() is None
    assert d['additionalCameraViewsGenerated']==0
    print('PASS: one 16:9 master, 12 unique source portraits, two equal aligned rows, unchanged source logo and opaque logo colors, no additional views.')

if __name__=='__main__':main()

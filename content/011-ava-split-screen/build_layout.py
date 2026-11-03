"""STATIC composition proof only. Does NOT generate animated talking/listening Ava."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'content/007-cosmic-ai'))
import persian_display as pd
SIZE=(1080,1920);SPLIT=1024
STUDIO=ROOT/'studio/ahangban-signature/master/MASTER-VIEW-001.png'
LOGO=ROOT/'studio/ahangban-signature/references/ahangban-logo-horizontal-color.png'
ACTOR=HERE/'assets/ava-actor-generated.png'
SOURCE=ROOT/'rendered/video-010-night-playlist/source-media'
TRACKS=json.loads((ROOT/'content/010-night-playlist/tracks.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def label(im,text,x,y,size,color='#f4eadc',center=False):
 tile=pd.render(text,size,color);im.alpha_composite(tile,(round(x-tile.width/2) if center else x,y))
def key_actor():
 a=np.array(Image.open(ACTOR).convert('RGB')).astype(np.float32)
 excess=a[:,:,1]-np.maximum(a[:,:,0],a[:,:,2]);alpha=1-np.clip((excess-18)/110,0,1)
 edge=alpha<.995;a[:,:,1]=np.where(edge,np.minimum(a[:,:,1],np.maximum(a[:,:,0],a[:,:,2])+5),a[:,:,1])
 return Image.fromarray(np.dstack((np.uint8(np.clip(a,0,255)),np.uint8(alpha*255))),'RGBA')
def studio_panel():
 # Crop only the approved right seat; preserve the actual gallery pixels, no new room.
 master=Image.open(STUDIO).convert('RGBA');box=(1950,730,2910,1526);size=(1080,896)
 bg=master.crop(box).resize(size,Image.Resampling.LANCZOS)
 actor=key_actor();actor.thumbnail((930,930),Image.Resampling.LANCZOS);bg.alpha_composite(actor,((1080-actor.width)//2,8))
 # Restore original foreground equipment/table so they correctly occlude her body.
 mask=Image.new('L',(1365,768));d=ImageDraw.Draw(mask)
 d.rectangle((0,522,1365,768),fill=255)
 d.polygon([(608,518),(613,505),(743,505),(756,523),(756,536),(607,535)],fill=255)
 d.rectangle((772,507,846,534),fill=255);d.ellipse((704,430,737,469),fill=255)
 d.rectangle((735,418,745,468),fill=255)
 d.line([(739,424),(744,402),(750,399),(850,397),(854,404),(845,530)],fill=255,width=6)
 d.line([(747,409),(846,399)],fill=255,width=3)
 mask=mask.resize(master.size,Image.Resampling.LANCZOS).crop(box).resize(size,Image.Resampling.LANCZOS)
 return Image.composite(master.crop(box).resize(size,Image.Resampling.LANCZOS),bg,mask)
def main():
 manifest=json.loads((ROOT/'content/010-night-playlist/final-female/delivery/manifest.json').read_text())
 protected={str(p.relative_to(ROOT)):sha(p) for p in (STUDIO,LOGO,*[ROOT/v[k] for v in manifest['outputs'].values() for k in ('video','cover')])}
 assert protected[str(STUDIO.relative_to(ROOT))]=='3f1817173e1e82b6bd8aa0ab70d43ab9b50dab958ec53b559811ce70dac92ddc'
 assert protected[str(LOGO.relative_to(ROOT))]=='2fa45d7af6cdf386adf32cf0ed174cfe81db6066c1b3f442c9da12967ecd66b4'
 for v in manifest['outputs'].values():assert sha(ROOT/v['video'])==v['sha256'] and sha(ROOT/v['cover'])==v['coverSha256']
 panel=studio_panel();outputs=[]
 for i,tr in enumerate(TRACKS):
  cover=SOURCE/tr['cover'];assert sha(cover)==tr['coverSha256']
  im=Image.new('RGBA',SIZE,'#101820');d=ImageDraw.Draw(im)
  # Quiet matte, full untouched cover, safe title space; no generated artist faces.
  art=ImageOps.contain(Image.open(cover).convert('RGBA'),(700,700),Image.Resampling.LANCZOS)
  shadow=Image.new('RGBA',SIZE);sd=ImageDraw.Draw(shadow);sd.rectangle((183,145,897,867),fill=(0,0,0,190));shadow=shadow.filter(ImageFilter.GaussianBlur(18));im=Image.alpha_composite(im,shadow)
  im.alpha_composite(art,((1080-art.width)//2,150))
  ImageDraw.Draw(im).rounded_rectangle((42,30,310,125),radius=16,fill='#eee8dc')
  logo=Image.open(LOGO).convert('RGBA');logo=logo.crop(logo.getbbox());logo.thumbnail((235,72),Image.Resampling.LANCZOS);im.alpha_composite(logo,(60,48))
  label(im,'انتخاب '+str(i+1).translate(str.maketrans('123','۱۲۳'))+' از ۳',820,60,32,'#c4b395')
  label(im,tr['title'],540,873,54,center=True);label(im,tr['artist'],540,949,35,'#c8b58d',center=True)
  im.alpha_composite(panel,(0,SPLIT));d=ImageDraw.Draw(im);d.rectangle((0,SPLIT,1080,SPLIT+3),fill='#bdac89')
  d.rounded_rectangle((38,SPLIT+30,210,SPLIT+99),radius=16,fill=(12,19,26,220));label(im,'آوا',80,SPLIT+37,41)
  d.rectangle((0,1840,1080,1920),fill='#0b1219')
  label(im,'نمونهٔ چیدمان ـ بدون انیمیشن',780,1858,29,'#d0d8df',center=True)
  d=ImageDraw.Draw(im);d.text((52,1865),'ahangban.ir',font=ImageFont.truetype(str(ROOT/'content/001-chavoshi-start/fonts/Vazirmatn-Regular.ttf'),28),fill='#e9ddc8')
  path=ROOT/f'downloads/ahangban-ava-layout-{i+1:02d}.jpg';im.convert('RGB').save(path,quality=94,subsampling=0)
  outputs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),size=list(SIZE),track=tr['id'],coverSourceSha256=sha(cover)))
 assert all(sha(ROOT/p)==s for p,s in protected.items())
 result=dict(status='STATIC_LAYOUT_ONLY_NOT_ANIMATED_VIDEO',userContentChoice='previous_playlist',userFaceApprovalPending=True,actorAIgenerated=True,actorSourceSha256=sha(ACTOR),originalFacePixelsNotClaimed=True,newRoomGenerated=False,studioCrop=[1950,730,2910,1526],studioSourceSha256=sha(STUDIO),logoSourceSha256=sha(LOGO),splitY=SPLIT,outputs=outputs,protectedUnchanged=protected,audioGenerated=False,lipSyncGenerated=False,headEyeOrBodyAnimationGenerated=False,publishAuthorized=False)
 (HERE/'layout-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

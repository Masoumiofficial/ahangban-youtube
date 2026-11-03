"""010 revision 02: dry speech gate, source-preserving projected cards, review film.
2.5D compositing, NOT a volumetric 3D reconstruction or new human approval.
Original 010 files are preserved. Only previews/covers are exported at this gate.
"""
import argparse,hashlib,importlib.util,json,math,re,shutil,subprocess,sys,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
HERE=Path(__file__).resolve().parent
EPISODE=HERE.parent
REPO=EPISODE.parents[1]
spec=importlib.util.spec_from_file_location('night010_base',EPISODE/'build_video.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
FF=b.FF;RATE=48000
WORK=REPO/'rendered/video-010-revision-02'
SOURCE=b.SOURCE
ROWS=json.loads((HERE/'dialogue-preview.fa.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def run(args):subprocess.run([FF,'-hide_banner','-loglevel','warning','-y',*map(str,args)],check=True)
def decode(path):
 data=subprocess.check_output([FF,'-v','error','-i',str(path),'-map','0:a:0','-ar',str(RATE),'-ac','2','-f','s16le','-'])
 return np.frombuffer(data,dtype='<i2').reshape(-1,2).astype(np.float32)/32768

def write_wave(path,data):
 with wave.open(str(path),'wb') as f:
  f.setparams((2,2,RATE,0,'NONE','not compressed'));f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())

def rgb_layer(mask,color):
 layer=Image.new('RGBA',mask.size,color);layer.putalpha(mask);return layer

def letters(value,size,color):
 # HarfBuzz helper shapes RTL; repair numeric run ordering, never change speech text.
 value=re.sub(r'[۰-۹0-9]{2,}',lambda m:m.group()[::-1],value)
 return b.pd.render(value,size,color)

def title(im,text,right,y,size,color='#fff4df',maxwidth=850,depth=7):
 while b.pd.width(text,size)>maxwidth:size-=1
 face=letters(text,size,color);mask=face.getchannel('A');x=round(right-face.width)
 # Restrained extruded edge, soft shadow and practical warm glow, not neon outlines.
 shadow=rgb_layer(mask,'#02070c');shadow.putalpha(mask.point(lambda a:round(a*.82)));shadow=shadow.filter(ImageFilter.GaussianBlur(6))
 im.alpha_composite(shadow,(x+10,y+12))
 for i in range(depth,0,-1):
  edge=rgb_layer(mask,'#5c3f24' if color!='#fff4df' else '#36434a');im.alpha_composite(edge,(x+i,y+i))
 im.alpha_composite(face,(x,y))
 return (x,y,x+face.width,y+face.height)

def homography_inverse(dst,src):
 A=[];B=[]
 for (x,y),(u,v) in zip(dst,src):
  A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);B.extend([u,v])
 return tuple(np.linalg.solve(np.array(A),np.array(B)))

def projected_card(path,side,yaw=-12,pitch=3,roll=-2):
 """Project a single original artwork plane with a pinhole camera; no AI redraw."""
 tile=Image.new('RGBA',(820,820),'#c9bca2');art=ImageOps.contain(Image.open(path).convert('RGB'),(800,800),Image.Resampling.LANCZOS)
 tile.paste(art,((820-art.width)//2,(820-art.height)//2))
 # Thin physical edge highlight stays outside the supplied artwork.
 ImageDraw.Draw(tile).rectangle((1,1,818,818),outline='#fff5d7',width=2)
 yy,xx,zz=map(math.radians,(yaw,pitch,roll))
 Ry=np.array([[math.cos(yy),0,math.sin(yy)],[0,1,0],[-math.sin(yy),0,math.cos(yy)]])
 Rx=np.array([[1,0,0],[0,math.cos(xx),-math.sin(xx)],[0,math.sin(xx),math.cos(xx)]])
 Rz=np.array([[math.cos(zz),-math.sin(zz),0],[math.sin(zz),math.cos(zz),0],[0,0,1]])
 R=Rz@Rx@Ry;pts=[];focal=side*3.4
 for x,y in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]:
  p=R@np.array([x*side,y*side,0]);pts.append((p[0]*focal/(focal+p[2]),p[1]*focal/(focal+p[2])))
 minx,miny=np.floor(np.min(pts,axis=0));maxx,maxy=np.ceil(np.max(pts,axis=0));pad=12
 dst=[(x-minx+pad,y-miny+pad) for x,y in pts]
 size=(int(maxx-minx)+pad*2,int(maxy-miny)+pad*2)
 coeff=homography_inverse(dst,[(0,0),(820,0),(820,820),(0,820)])
 card=tile.transform(size,Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)
 thick=Image.new('RGBA',(size[0]+10,size[1]+10));edge=rgb_layer(card.getchannel('A'),'#2b2520')
 for j in range(7,0,-1):thick.alpha_composite(edge,(j,j//2))
 thick.alpha_composite(card,(0,0));return thick

def place_card(im,tr,center,side,yaw=-12,pitch=3,roll=-2,reflection=True):
 card=projected_card(SOURCE/tr['cover'],side,yaw,pitch,roll);x=round(center[0]-card.width/2);y=round(center[1]-card.height/2)
 if reflection:
  ref=ImageOps.flip(card);ref=ref.resize((ref.width,max(1,round(ref.height*.32))),Image.Resampling.BICUBIC)
  a=np.asarray(ref.getchannel('A')).astype(float);fade=np.linspace(.27,0,ref.height)[:,None];ref.putalpha(Image.fromarray((a*fade).astype('uint8')))
  im.alpha_composite(ref.filter(ImageFilter.GaussianBlur(1.8)),(x+12,y+card.height-5))
 shadow=Image.new('RGBA',im.size);d=ImageDraw.Draw(shadow)
 d.ellipse((x-15,y+card.height-24,x+card.width+30,y+card.height+32),fill=(0,0,0,185));shadow=shadow.filter(ImageFilter.GaussianBlur(17))
 im.alpha_composite(shadow)
 drop=rgb_layer(card.getchannel('A'),'#000000').filter(ImageFilter.GaussianBlur(12));im.alpha_composite(drop,(x+13,y+20));im.alpha_composite(card,(x,y))

def backdrop(kind='youtube',index=0):
 size=b.SIZES[kind];asset='depth-night-vertical.jpg' if kind=='reel' else 'depth-night-wide.jpg'
 im=ImageOps.fit(Image.open(HERE/'assets'/asset).convert('RGB'),size,Image.Resampling.LANCZOS).convert('RGBA')
 # Reframe ONE real-looking room; blending unrelated rooms creates ghost geometry.
 if index>0:
  im=ImageOps.fit(im.resize((round(size[0]*1.03),round(size[1]*1.03)),Image.Resampling.LANCZOS),size,centering=(.44+index*.06,.5))
 return im

def brand(im,kind):
 logo=Image.open(b.g.LOGO).convert('RGBA');logo.thumbnail((250,88) if kind=='reel' else (260,90),Image.Resampling.LANCZOS)
 x,y=(106,140) if kind=='reel' else (1520,65)
 ImageDraw.Draw(im).rounded_rectangle((x-14,y-12,x+logo.width+14,y+logo.height+12),radius=13,fill='#eee4d2')
 im.alpha_composite(logo,(x,y))

def covers():
 bounds={}
 for kind in ('youtube','reel'):
  im=backdrop(kind);w,h=im.size;brand(im,kind)
  if kind=='youtube':
   place_card(im,b.TRACKS[1],(255,660),345,yaw=-22,roll=-5)
   place_card(im,b.TRACKS[2],(870,680),350,yaw=18,roll=4)
   place_card(im,b.TRACKS[0],(570,595),470,yaw=-10,pitch=4,roll=-2)
   bb=[title(im,'خواب',1790,245,180,maxwidth=700),title(im,'نمیاد؟',1790,427,188,maxwidth=760),title(im,'۳ آهنگ برای امشب',1780,680,57,'#efc27e',maxwidth=750,depth=3),title(im,'قمیشی • داریوش • اصلانی',1780,785,35,maxwidth=750,depth=1)]
   b.g.text(ImageDraw.Draw(im),'ahangban.ir',1790,998,29,'#e7d4ae',anchor='rt')
   im=im.convert('RGB').resize((1280,720),Image.Resampling.LANCZOS);name='ahangban-night-v2-youtube-thumbnail.jpg'
  else:
   bb=[title(im,'خوابت نمی‌بره؟',918,355,115,maxwidth=815),title(im,'۳ آهنگ برای امشب',918,515,65,'#efc27e',maxwidth=815,depth=4)]
   place_card(im,b.TRACKS[1],(230,1090),300,yaw=-23,roll=-5)
   place_card(im,b.TRACKS[2],(830,1100),300,yaw=24,roll=5)
   place_card(im,b.TRACKS[0],(535,1025),470,yaw=-10,pitch=3,roll=-2)
   bb.append(title(im,'قمیشی • داریوش • اصلانی',918,1440,38,maxwidth=815,depth=1))
   b.g.text(ImageDraw.Draw(im),'ahangban.ir',918,1532,32,'#e7d4ae',anchor='rt');im=im.convert('RGB');name='ahangban-night-v2-reel-cover.jpg'
  out=REPO/'downloads'/name;im.save(out,quality=96);bounds[kind]=dict(file=str(out.relative_to(REPO)),sha256=sha(out),size=list(im.size),titleBoundsAtNativeSize=bb)
 dump(HERE/'delivery/cover-manifest.json',dict(status='new_design_pending_user_review',outputs=bounds,logoSha256=sha(b.g.LOGO),originalArtworkUsed=True,artworkRegenerated=False,design='Original supplied cover planes projected by a pinhole camera, edge thickness, soft cast shadow and vertically faded floor reflection; extruded Persian type; generated photographic background. 2.5D composite, not real footage.'))

def speech_assets():
 WORK.mkdir(parents=True,exist_ok=True);chunks=[];timeline=[];cursor=0.;normalized={}
 for row in ROWS:
  path=HERE/'audio'/(row['id']+'.mp3');data=decode(path);rms=float(np.sqrt(np.mean(data**2)));peak=float(abs(data).max())
  assert rms>.004
  gain=min(.10/rms,.80/max(peak,1e-9));normalized[row['id']]=data*gain
  duration=len(data)/RATE;timeline.append(dict(row,start=cursor,end=cursor+duration,duration=duration,constantGain=gain,sourceSha256=sha(path)))
  chunks.append(data*gain);cursor+=duration
  if row!=ROWS[-1]:chunks.append(np.zeros((round(.28*RATE),2),np.float32));cursor+=.28
 wav=WORK/'dry-voice.wav';write_wave(wav,np.concatenate(chunks));out=REPO/'downloads/ahangban-night-v2-voice-preview.mp3'
 run(['-i',wav,'-c:a','libmp3lame','-b:a','192k',out]);check=decode(out);assert abs(check).max()<.99
 report=dict(status='new_performances_pending_user_listening',previous010PerformanceRejected=True,previous008VoiceIdentitiesRetained=True,previousAudioSha256=[x['audioSha256'] for x in b.DIALOGUE],newSpeechSourceHashes=[r['sourceSha256'] for r in timeline],timeline=timeline,duration=cursor,output=str(out.relative_to(REPO)),sha256=sha(out),musicUsed=False,soundEffectsUsed=False,humanRecordingUsed=False,personalCloneUsed=False,voicePitchChanged=False,voiceSpeedChanged=False,internalPausesEdited=False,preciseEngineEmotionOrWordStressControlAvailable=False,processing='Constant per-clip gain only, 280ms between complete utterances. No EQ/reverb/compression, time stretching or pitch shifting.',changes='Shorter conversational questions and replies; removed abstract phrases and list-like introduction. Naturalness, pronunciation and emphasis are pending human review, not technically certified.')
 dump(HERE/'delivery/voice-preview-manifest.json',report)
 return normalized,report

class DepthArtwork(b.Artwork):
 def overlay(self,event,variant=0,thumbnail=False):
  im=Image.new('RGBA',self.size);v=self.vertical;brand(im,self.kind);right=918 if v else 1800
  idx=self.byid.get(event['scene'],-1)
  if idx>=0:
   tr=b.TRACKS[idx]
   title(im,tr['title'],right,350 if v else 310,94 if v else 116,maxwidth=800 if v else 1000)
   title(im,tr['artist'],right,510 if v else 480,42 if v else 47,'#efc27e',maxwidth=800,depth=2)
   title(im,'انتخاب '+str(idx+1).translate(b.g.DIGITS)+' از ۳',right,275 if v else 235,30,'#bdc8cb',maxwidth=800,depth=1)
  else:
   title(im,'آخر شب…',right,370 if v else 310,105 if v else 135,maxwidth=800 if v else 1000)
   title(im,'کدوم آهنگ؟',right,530 if v else 495,80 if v else 98,'#efc27e',maxwidth=800,depth=4)
  title(im,'نمونهٔ اصلاح صدا و تدوین',right,1515 if v else 1002,26,'#b8c2c7',maxwidth=800,depth=0)
  b.g.text(ImageDraw.Draw(im),'ahangban.ir',88,1565 if v else 1020,26,'#e7d4ae',anchor='lt')
  return im
 def art_layer(self,event,variant):
  im=Image.new('RGBA',self.size);idx=self.byid.get(event['scene'],-1);v=self.vertical
  if idx>=0:
   place_card(im,b.TRACKS[idx],(500,1040) if v else (440,610),480 if v else 570,yaw=(-16,10,-8,17)[variant%4],roll=(-2,2,-1,1)[variant%4])
  else:
   for i,tr in enumerate(b.TRACKS):place_card(im,tr,((230+i*270),1030) if v else (240+i*245,690),220 if v else 280,yaw=(-18,0,18)[i],roll=(i-1)*2)
  return im

def foreground(size):
 w,h=size;im=Image.new('RGBA',size);d=ImageDraw.Draw(im);rng=np.random.default_rng(102)
 # Out-of-focus near-glass details move independently from background/card planes.
 for _ in range(20):
  x=int(rng.uniform(-40,w+40));y=int(rng.uniform(0,h));r=int(rng.uniform(8,30))
  d.ellipse((x-r,y-r,x+r,y+r),outline=(231,205,157,20),width=2)
  if x<w*.35:d.line((x,y-r,x-3,y+r*4),fill=(190,218,224,14),width=2)
 return im.filter(ImageFilter.GaussianBlur(3.5))

def shot_command(root,kind,shot,event,caption_file):
 fps=b.FPS[kind];w,h=b.SIZES[kind];n=shot['frames'];idx=next((i for i,t in enumerate(b.TRACKS) if t['id']==event['scene']),0)
 layer=root/'layers';offset=shot['start']-event['start'];color=b.PALETTE[idx].replace('#','0x');variant=shot['variant']
 args=[FF,'-v','error','-y','-filter_complex_threads','2','-i',str(layer/f'bg-{idx}.jpg'),'-loop','1','-framerate','1','-i',str(layer/f'title-{shot["eventIndex"]}.png'),'-loop','1','-framerate','1','-i',str(layer/f'art-{shot["eventIndex"]}-{variant}.png'),'-ss',str(shot['start']),'-i',str(root/'audio.wav'),'-f','concat','-safe','0','-i',str(caption_file),'-loop','1','-framerate','1','-i',str(layer/'near-glass.png')]
 zoom=f'1.04+0.035*on/{n}' if variant%2==0 else f'1.11-0.035*on/{n}'
 graph=f"[0:v]scale=in_range=full:out_range=tv,format=yuv420p,zoompan=z='{zoom}':x='iw/2-iw/zoom/2+22*sin(on/{fps}*.25)':y='ih/2-ih/zoom/2+6*cos(on/{fps}*.3)':d={n}:s={w}x{h}:fps={fps},setsar=1,format=yuv420p[bg];"
 graph+="[bg][2:v]overlay=x='12*sin(t*.38)':y='6*cos(t*.3)':eval=frame:shortest=0[art];[art][5:v]overlay=x='-12+16*sin(t*.22)':y='-8+10*cos(t*.19)':eval=frame:shortest=0[glass];[glass][1:v]overlay=0:0:shortest=0[title];[title][4:v]overlay=0:0:shortest=0[caption];"
 current='caption'
 if event['type']=='music':
  sw,sh=(790,70) if kind=='reel' else (790,85);sx,sy=(110,1325) if kind=='reel' else (985,735)
  graph+=f"[3:a]aformat=channel_layouts=mono,showfreqs=s={sw}x{sh}:mode=line:ascale=log:fscale=log:win_size=2048:rate={fps}:colors={color},colorkey=0x000000:0.08:0.02[frequency];[caption][frequency]overlay={sx}:{sy}:shortest=0[spectrum];"
  current='spectrum'
 # Short shutter reveal replaces repeated oversized moving light wipes.
 graph+=f'[{current}]fade=t=in:st=0:d=0.10[final]'
 return args+['-filter_complex',graph,'-map','[final]','-an','-frames:v',str(n),'-r',str(fps),'-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p',str(root/'shots'/f'{shot["index"]:03d}.mp4')]

def make_demo(normalized,kind='youtube',stills_only=False):
 root=WORK/kind;root.mkdir(parents=True,exist_ok=True);norm=root/'normalized';norm.mkdir(exist_ok=True);media=root/'source-media';media.mkdir(exist_ok=True)
 for a in b.MANIFEST['assets']:
  p=SOURCE/a['file'];assert sha(p)==a['sha256']
  if not (media/a['file']).exists():shutil.copy2(p,media/a['file'])
 events=[];chunks=[];captions=[];cursor=0.
 def append(data,info):
  nonlocal cursor
  duration=len(data)/RATE;event=dict(info,start=cursor,end=cursor+duration,duration=duration,sceneDuration=duration+.28)
  events.append(event);chunks.extend([data,np.zeros((round(.28*RATE),2),np.float32)]);cursor+=duration+.28
  if event['type']=='speech':captions.extend(b.caption_cues(event,data))
 def speech(row):
  data=normalized[row['id']];write_wave(norm/(row['id']+'.wav'),data);append(data,dict(row,type='speech'))
 def music(index,duration):
  tr=b.TRACKS[index];p=norm/(tr['id']+'.wav');offset=tr['excerptStart']
  run(['-ss',offset,'-i',SOURCE/tr['file'],'-map','0:a:0','-t',duration,'-af',f'loudnorm=I=-18:TP=-2:LRA=10,afade=t=in:d=0.1,afade=t=out:st={duration-.25}:d=0.25','-ar',RATE,'-ac','2','-c:a','pcm_s16le',p]);data=b.pcm(p)
  append(data,dict(type='music',scene=tr['id'],id=tr['id'],title=tr['title'],artist=tr['artist'],sourceStart=offset,sourceFile=tr['file'],cameraCutsLocal=b.onset_cuts(data,2)))
 speech(ROWS[0]);speech(ROWS[1]);music(0,8);speech(ROWS[2]);music(1,7);music(2,7)
 write_wave(root/'audio.wav',np.concatenate(chunks));plan=dict(kind=kind,duration=cursor,events=events,captions=captions,ctas=[],status='style_and_voice_preview_not_full_episode',captionTiming='proportional short groups, silence-nudged, not forced alignment',cameraTiming='RMS energy onsets, not certified beats')
 dump(root/'timeline.json',plan);dump(HERE/'delivery/demo-timeline.json',plan)
 b.Artwork=DepthArtwork;b.background=lambda index,k:backdrop(k,index).convert('RGB');b.shot_command=shot_command
 layers=root/'layers';layers.mkdir(exist_ok=True);foreground(b.SIZES[kind]).save(layers/'near-glass.png')
 b.render(root,kind,plan,stills_only)
 if not stills_only:
  input=root/f'ahangban-night-playlist-{kind}.mp4';out=REPO/'downloads/ahangban-night-v2-style-preview.mp4'
  run(['-i',input,'-c','copy','-metadata','comment=Revision 02 voice and 2.5D visual review preview. New performances are NOT approved. No rights clearance or public publication.','-movflags','+faststart',out])
  dump(HERE/'delivery/demo-manifest.json',dict(status='review_preview_not_final_episode',video=str(out.relative_to(REPO)),sha256=sha(out),bytes=out.stat().st_size,duration=cursor,resolution=list(b.SIZES[kind]),fps=b.FPS[kind],fullEpisodeRebuilt=False,previous010SpeechRejected=True,sourceCommit=b.MANIFEST['sourceCommit'],logoSha256=sha(b.g.LOGO),originalArtworkHashVerified=True,voiceIdentities={'female':'voice-06','male':'voice-07'},humanRecordingUsed=False,voiceSpeedOrPitchChanged=False,finalUserListeningPending=True,copyrightCleared=False,youtubePublished=False,instagramPublished=False,visualMethod='2.5D pinhole-projected original cover planes + edge thickness, soft shadow, faded table reflection, independent foreground/background/card camera motion, real audio FFT line and short shutter reveal. Not a volumetric 3D scene.'))
 return plan

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stills-only',action='store_true');p.add_argument('--assets-only',action='store_true');a=p.parse_args()
 covers();normalized,report=speech_assets();print('DRY VOICE',round(report['duration'],2),flush=True)
 if not a.assets_only:make_demo(normalized,stills_only=a.stills_only)

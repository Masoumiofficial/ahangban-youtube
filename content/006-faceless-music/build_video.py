"""Faceless music editorial: complete YouTube episode + purpose-built vertical Reel.
Only original covers, original logo, typography and audio-reactive graphics.
No presenter images, studio shots, voice regeneration, models, services or publishing.
"""
import argparse,array,hashlib,json,math,subprocess,time,wave
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
import arabic_reshaper
from bidi.algorithm import get_display
import imageio_ffmpeg

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
OLD=HERE.parent/'004-chavoshi-own-voice/delivery'
SOURCE=REPO/'downloads/ahangban-first-video-final.mp4'
SOURCE_SHA='2efd5ba3cb0731ff256e707a7ef5ba508da6c364eee3e364cf9f1c5f452ee0e5'
LOGO=REPO/'studio/ahangban-signature/references/ahangban-logo-horizontal-color.png'
FONTS=HERE.parent/'001-chavoshi-start/fonts'
PIN='d318f9f7095ab6c966a743ad3461e8f6fab0db34'
FF=imageio_ffmpeg.get_ffmpeg_exe();FPS={'youtube':25,'reel':30}
SIZES={'youtube':(1920,1080),'reel':(1080,1920)}
CREAM='#f1e8d8';MUTED='#b4b0a8';INK='#101211'
ACCENTS=['#e8b765','#c3c9a2','#dba092','#9cc9bf','#b9b0dc']
DIGITS=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def run(args):subprocess.run([FF,'-hide_banner','-loglevel','warning','-y',*map(str,args)],check=True)
@lru_cache(maxsize=90)
def font(size,bold=False):return ImageFont.truetype(str(FONTS/('Vazirmatn-Bold.ttf' if bold else 'Vazirmatn-Regular.ttf')),size)
def shaped(s):return get_display(arabic_reshaper.reshape(s))
def width(s,size,bold=False):return font(size,bold).getlength(shaped(s))
def text(d,s,x,y,size=40,fill=CREAM,bold=False,anchor='rt'):
 d.text((round(x),round(y)),shaped(s),font=font(size,bold),fill=fill,anchor=anchor)
def fit(s,size,max_width,bold=True):
 while width(s,size,bold)>max_width and size>18:size-=1
 return size

def lines(s,size,max_width):
 result=[];line=''
 for word in s.replace('\n',' ').split():
  trial=(line+' '+word).strip()
  if line and width(trial,size)>max_width:result.append(line);line=word
  else:line=trial
 if line:result.append(line)
 return result

def ease(u):u=max(0,min(1,u));return u*u*(3-2*u)

def make_plan(kind):
 source=json.loads((OLD/'timeline.json').read_text())
 if kind=='youtube':
  plan=json.loads(json.dumps(source));plan['kind']=kind
  upcoming={'10':'sange-saboor','11':'amir-bi-gazand','06':'beraghsa'}
  for e in plan['events']:e['visualScene']=upcoming.get(e.get('id'),e['scene'])
  return plan
 # Native vertical teaser, not a crop of the horizontal video.
 # Narration cuts come from pause-estimated caption boundaries, with 20ms lead padding.
 # User listening review still required; these are not forced-aligned words.
 events=[];cursor=0
 def add(duration,**kw):
  nonlocal cursor
  events.append(dict(start=cursor,end=cursor+duration,duration=duration,sceneDuration=duration,**kw));cursor+=duration
 hook_start=18.267844270833336;hook_end=22.293708333333335
 add(hook_end-hook_start,type='speech',speaker='male',scene='opening',visualScene='opening',sourceStart=hook_start,
     text='برای کسی که تازه می‌خواد چاوشی گوش بده، چی می‌ذاری؟')
 for e in source['events']:
  if e['type']=='music':
   add(5.,type='music',scene=e['scene'],visualScene=e['scene'],sourceStart=e['start']+1.,title=e['title'],artist=e['artist'])
 add(2.06,type='speech',speaker='female',scene='recap',visualScene='recap',sourceStart=196.90935416666668,text='همون رو توی کامنت بنویس.')
 add(1.2,type='hold',scene='recap',visualScene='recap',sourceStart=None)
 captions=[{'start':e['start'],'end':e['end']-.02,'text':e['text']} for e in events if e['type']=='speech']
 return {'kind':kind,'duration':cursor,'events':events,'captions':captions,'musicSampleCount':5,
         'captionTiming':'Re-edited existing pause-estimated speech windows, not word-level alignment'}

def prepare(root,tracks,plan):
 root.mkdir(parents=True,exist_ok=True);media=root/'source-media';media.mkdir(exist_ok=True)
 if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Unexpected source episode; no voice substitution permitted')
 assets=[]
 for tr in tracks:
  name=tr['cover'];gitpath='Artist/1-Mohsen-Chavoshi/'+name
  blob=subprocess.check_output(['git','rev-parse',f'{PIN}:{gitpath}'],cwd=REPO,text=True).strip()
  p=media/name
  with p.open('wb') as f:subprocess.run(['git','cat-file','blob',blob],cwd=REPO,stdout=f,check=True)
  assets.append({'path':gitpath,'gitBlob':blob,'sha256':sha(p),'size':list(Image.open(p).size)})
 audio=root/'audio.wav'
 if plan['kind']=='youtube':
  run(['-i',SOURCE,'-map','0:a:0','-vn','-ar',48000,'-ac',2,'-c:a','pcm_s16le',audio])
 else:
  samples=bytearray()
  for e in plan['events']:
   if e['type']=='hold':samples.extend(b'\0'*(round(e['duration']*48000)*4));continue
   filters='afade=t=in:d=0.008,afade=t=out:st={:.6f}:d=0.012'.format(e['duration']-.012)
   if e['type']=='music':filters='afade=t=in:d=0.075,afade=t=out:st={:.6f}:d=0.12'.format(e['duration']-.12)
   data=subprocess.check_output([FF,'-v','error','-i',str(SOURCE),
    '-t',f'{e["duration"]:.9f}','-map','0:a:0','-vn','-af',f'atrim=start={e["sourceStart"]:.9f}:duration={e["duration"]:.9f},asetpts=PTS-STARTPTS,'+filters,'-ar','48000','-ac','2','-f','s16le','-'])
   target=round(e['duration']*48000)*4;data=(data+b'\0'*max(0,target-len(data)))[:target];samples.extend(data)
  with wave.open(str(audio),'wb') as w:w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(samples)
 provenance={'sourceEpisode':str(SOURCE.relative_to(REPO)),'sourceEpisodeSha256':SOURCE_SHA,'logo':str(LOGO.relative_to(REPO)),
  'logoSha256':sha(LOGO),'assets':assets,'voicesRegenerated':False,'presenterImagesUsed':False,'studioImagesUsed':False,
  'note':'Original covers can contain artist/actor faces; no synthetic presenter or face animation is used.'}
 (root/'timeline.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
 (root/'source-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 return provenance

def spectrum(audio,fps,duration,bands=48):
 with wave.open(str(audio)) as w:
  data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).mean(axis=1)[::3]/32768.
 rate=16000;nfft=1024;window=np.hanning(nfft)
 edges=np.geomspace(60,7500,bands+1);freq=np.fft.rfftfreq(nfft,1/rate)
 bins=[np.flatnonzero((freq>=a)&(freq<b)) for a,b in zip(edges,edges[1:])]
 bins=[b if len(b) else np.array([int(np.argmin(abs(freq-(edges[i]+edges[i+1])/2)))]) for i,b in enumerate(bins)]
 out=np.zeros((math.ceil(duration*fps),bands),dtype=np.float32);previous=np.zeros(bands)
 for i in range(len(out)):
  offset=round(i*rate/fps);clip=data[offset:offset+nfft]
  if len(clip)<nfft:clip=np.pad(clip,(0,nfft-len(clip)))
  magnitudes=abs(np.fft.rfft(clip*window))/(nfft/4)
  raw=np.array([np.sqrt(np.mean(magnitudes[b]**2)) for b in bins])
  levels=np.clip((20*np.log10(raw+1e-7)+65)/55,0,1)
  if np.sqrt(np.mean(clip**2))<.001:levels*=0
  previous=np.where(levels>previous,.65*levels+.35*previous,.25*levels+.75*previous)
  out[i]=previous
 return out

class Design:
 def __init__(self,kind,root,tracks,plan):
  self.kind=kind;self.vertical=kind=='reel';self.size=SIZES[kind];self.root=root;self.tracks=tracks;self.plan=plan
  self.byid={t['id']:i for i,t in enumerate(tracks)};self.caption_cache={};self.title_cache={}
  self.art={t['id']:Image.open(root/'source-media'/t['cover']).convert('RGB') for t in tracks}
  self.back=self.background();self.logo=Image.open(LOGO).convert('RGBA');self.logo.thumbnail((248,78) if self.vertical else (250,78),Image.Resampling.LANCZOS)
  self.cover_cache={};self.setup_layers()
 def background(self):
  w,h=self.size;small=np.zeros((max(1,h//4),max(1,w//4),3),dtype=np.uint8)
  yy,xx=np.mgrid[0:small.shape[0],0:small.shape[1]];xn=xx/small.shape[1];yn=yy/small.shape[0]
  glow=np.exp(-((xn-.2)**2+(yn-.48)**2)*4)
  rng=np.random.default_rng(42);noise=rng.normal(0,.65,glow.shape)
  for c,(base,boost) in enumerate(((15,17),(19,15),(19,11))):small[:,:,c]=np.clip(base+glow*boost+noise,0,255)
  im=Image.fromarray(small).resize((w,h),Image.Resampling.BICUBIC);d=ImageDraw.Draw(im)
  for x in range(70,w,80):d.line((x,0,x,h),fill=(35,39,36),width=1)
  for y in range(70,h,80):d.line((0,y,w,y),fill=(35,39,36),width=1)
  # Quiet editorial framing, not neon strips or fake studio geometry.
  d.rectangle((28,28,w-29,h-29),outline=(77,75,64),width=1)
  return im
 def label(self,s,size,color=CREAM,bold=False):
  key=(s,size,color,bold)
  if key not in self.title_cache:
   f=font(size,bold);box=f.getbbox(shaped(s));w=math.ceil(width(s,size,bold))+8;h=size*2
   im=Image.new('RGBA',(w,h));text(ImageDraw.Draw(im),s,w-4,0,size,color,bold)
   bounds=im.getbbox();self.title_cache[key]=im.crop(bounds) if bounds else im
  return self.title_cache[key]
 def put(self,im,s,right,top,size,color=CREAM,bold=False,opacity=1):
  layer=self.label(s,size,color,bold)
  if opacity<1:layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda a:round(a*max(0,opacity))))
  im.paste(layer,(round(right-layer.width),round(top)),layer)
 def setup_layers(self):
  # Cache decorated art at a slightly larger size; per-frame transforms stay bounded.
  side=650 if not self.vertical else 690
  for t in self.tracks:
   art=ImageOps.contain(self.art[t['id']],(side,side),Image.Resampling.LANCZOS)
   tile=Image.new('RGB',(side+28,side+28),'#e4dac6');tile.paste(art,((tile.width-art.width)//2,(tile.height-art.height)//2))
   self.cover_cache[t['id']]=tile
  self.smallcovers={t['id']:ImageOps.contain(self.art[t['id']],(220,220),Image.Resampling.LANCZOS) for t in self.tracks}
 def branding(self,im):
  d=ImageDraw.Draw(im);w,h=self.size
  x,y=(88,130) if self.vertical else (1520,55)
  d.rounded_rectangle((x-14,y-10,x+270,y+88),radius=13,fill='#e9e0cd')
  im.paste(self.logo,(x,y),self.logo)
  if not self.vertical:
   self.put(im,'موسیقی، از زاویهٔ شنیدن',1390,88,25,MUTED)
   self.put(im,'ahangban.ir',w-76,h-44,23,MUTED)
 def cover(self,im,id,center,side,phase,angle=0):
  # No content-aware generation/cropping: preserve cover composition and aspect ratio.
  zoom=1+.018*math.sin(phase*.6)
  tile=self.cover_cache[id].resize((round(side*zoom),round(side*zoom)),Image.Resampling.BICUBIC).convert('RGBA')
  if angle:tile=tile.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
  x=round(center[0]-tile.width/2);y=round(center[1]-tile.height/2)
  # Soft fixed shadow. The artwork itself is never warped.
  shadow=Image.new('RGBA',(tile.width+24,tile.height+24));ImageDraw.Draw(shadow).rectangle((12,12,tile.width+12,tile.height+12),fill=(0,0,0,145))
  shadow=shadow.filter(ImageFilter.GaussianBlur(9))
  im.paste(shadow,(x+6,y+14),shadow);im.paste(tile,(x,y),tile)
 def active_caption(self,t):
  return next((c['text'] for c in self.plan['captions'] if c['start']<=t<c['end']),None)
 def caption(self,im,t,event):
  s=self.active_caption(t)
  if not s:return
  w,h=self.size;maximum=760 if self.vertical else 1570;size=48 if self.vertical else 43
  chunks=lines(s,size,maximum)
  while len(chunks)>2:size-=1;chunks=lines(s,size,maximum)
  key=(s,size)
  if key not in self.caption_cache:
   height=(size+15)*len(chunks)+30;panel=Image.new('RGBA',(maximum+60,height));d=ImageDraw.Draw(panel)
   d.rounded_rectangle((0,0,panel.width-1,height-1),radius=15,fill=(9,12,12,242),outline=(92,96,83,180),width=1)
   for i,line in enumerate(chunks):text(d,line,panel.width//2,14+i*(size+15),size,CREAM,True,anchor='mt')
   self.caption_cache[key]=panel
  panel=self.caption_cache[key];y=(1534 if self.vertical else 1032)-panel.height
  x=round((88+920-panel.width)/2) if self.vertical else (w-panel.width)//2
  im.paste(panel,(x,y),panel)
 def bars(self,im,values,accent,t,event):
  d=ImageDraw.Draw(im)
  if self.vertical:x,y,total,maxh=140,1330,740,76
  else:x,y,total,maxh=1030,820,740,116
  step=total/len(values)
  for i,v in enumerate(values):
   height=3+round(float(v)*maxh)
   d.rounded_rectangle((round(x+i*step),y-height,round(x+(i+1)*step-5),y),radius=3,fill=accent)
  # Accurate track elapsed progress, not a fabricated beat counter.
  duration=event['duration'];p=max(0,min(1,(t-event['start'])/duration))
  d.line((x,y+17,x+total,y+17),fill='#42483f',width=2)
  d.line((x,y+17,x+round(total*p),y+17),fill=accent,width=4)
 def hero(self,im,t,event,thumbnail=False):
  local=t-event['start'];vertical=self.vertical
  if vertical:
   # Native portrait design, safe from right-side action buttons and bottom caption UI.
   self.put(im,'چاوشی رو',920,292,102,CREAM,True)
   self.put(im,'از کجا شروع کنیم؟',920,425,fit('از کجا شروع کنیم؟',79,840),ACCENTS[0],True)
   for i,tr in enumerate(self.tracks):
    cx=270+i*119;cy=890+abs(i-2)*45
    self.cover(im,tr['id'],(cx,cy),340,local+i,angle=(i-2)*-5)
   self.put(im,'۵ آهنگ  /  ۵ حال‌وهوا',900,1210,44,CREAM,True)
  else:
   # A staggered album stack with generous editorial typography.
   for j in (0,4,1,3,2):
    cx=285+j*114;cy=505+abs(j-2)*35
    self.cover(im,self.tracks[j]['id'],(cx,cy),345,local+j,angle=(j-2)*-5)
   if event['scene']=='recap':a,b='انتخاب اولت','کدوم آهنگه؟'
   elif t<4.63 or thumbnail:a,b='چاوشی رو','از کجا شروع کنیم؟'
   elif t<8.88:a,b='۵ انتخاب','۵ حال‌وهوا'
   elif t<16.01:a,b='رتبه‌بندی نیست','انتخاب با گوشِ توست'
   else:a,b='اولین انتخاب','تو چیه؟'
   enter=ease(local/.7);shift=round((1-enter)*45)
   self.put(im,a,1788,290+shift,110,CREAM,True,enter)
   self.put(im,b,1788,450+shift,fit(b,80,810),ACCENTS[0],True,enter)
   self.put(im,'پنج پیشنهاد برای شروع شنیدن محسن چاوشی',1788,618,31,MUTED)
   self.put(im,'۰۱  —  ۰۵',1788,736,39,ACCENTS[0],True)
 def song(self,im,t,event,index):
  tr=self.tracks[index];accent=ACCENTS[index];local=t-event['start'];d=ImageDraw.Draw(im)
  if self.vertical:
   self.put(im,'انتخاب '+str(index+1).translate(DIGITS)+' از ۵',920,272,34,accent,True)
   self.put(im,tr['title'],920,344,fit(tr['title'],85,840),CREAM,True)
   self.put(im,tr['artist'],920,455,fit(tr['artist'],37,840,False),MUTED)
   self.cover(im,tr['id'],(490,900+5*math.sin(local*.5)),675,local)
   if event['type']=='music':self.put(im,'کدام انتخابِ توست؟',900,1450,46,CREAM,True)
  else:
   self.put(im,'انتخاب '+str(index+1).translate(DIGITS)+' از ۵',1788,218,35,accent,True)
   self.put(im,tr['title'],1788,318,fit(tr['title'],94,820),CREAM,True)
   self.put(im,tr['artist'],1788,450,fit(tr['artist'],38,820,False),MUTED)
   self.put(im,tr['cue'],1788,548,47,accent,True)
   self.cover(im,tr['id'],(508+7*math.sin(local*.3),520),650,local)
   if event['type']=='music':
    remaining=max(0,math.ceil(event['end']-t));self.put(im,str(remaining).translate(DIGITS),1788,644,61,CREAM,True)
    self.put(im,'در حال شنیدن',1690,664,25,MUTED)
   else:
    name='سجاد' if event.get('speaker')=='male' else 'آوا'
    self.put(im,'روایت: '+name,1788,664,26,MUTED)
  self.bars(im,self.levels,accent,t,event)
 def recap(self,im,t,event):
  if not self.vertical:self.hero(im,t,event);return
  self.put(im,'انتخابت کدومه؟',920,320,90,CREAM,True)
  self.put(im,'اسم آهنگ رو کامنت کن',920,450,53,ACCENTS[0],True)
  for i,tr in enumerate(self.tracks):
   size=210;cx=235+(i%3)*258;cy=790+(i//3)*265
   self.cover(im,tr['id'],(cx,cy),size,t+i)
  self.put(im,'ahangban.ir',900,1240,59,CREAM,True)
 def frame(self,t,levels,thumbnail=False):
  self.levels=levels;im=self.back.copy();event=next((e for e in self.plan['events'] if t<e['end']+(.25 if self.kind=='youtube' else 0)),self.plan['events'][-1])
  scene=event['visualScene'];self.branding(im)
  if scene=='opening':self.hero(im,t,event,thumbnail)
  elif scene=='recap':self.recap(im,t,event)
  else:self.song(im,t,event,self.byid[scene])
  if not thumbnail:
   self.caption(im,t,event)
   d=ImageDraw.Draw(im);w,h=self.size
   if self.vertical:
    # Safe region for main content: x 88..920, y 130..1560. UI may vary by device.
    y=1570;d.line((140,y,880,y),fill='#41483f',width=3);d.line((140,y,140+round(740*t/self.plan['duration']),y),fill=CREAM,width=4)
   else:
    d.line((74,1054,1846,1054),fill='#41483f',width=2);d.line((74,1054,74+round(1772*t/self.plan['duration']),1054),fill=CREAM,width=3)
  return im

def command(root,kind,total):
 w,h=SIZES[kind];audio=SOURCE if kind=='youtube' else root/'audio.wav';dest=root/f'ahangban-faceless-{kind}.mp4'
 cmd=[FF,'-hide_banner','-loglevel','warning','-y','-filter_threads','2','-f','rawvideo','-pix_fmt','rgb24',
  '-s',f'{w}x{h}','-r',str(FPS[kind]),'-i','pipe:0','-i',str(audio),'-map','0:v:0','-map','1:a:0',
  '-c:v','libx264','-preset','veryfast','-crf','21','-threads','2','-pix_fmt','yuv420p']
 cmd+=['-c:a','copy'] if kind=='youtube' else ['-c:a','aac','-b:a','192k']
 return cmd+['-metadata','title=چاوشی را از کجا شروع کنیم؟ | آهنگ‌بان',
  '-metadata','comment=Faceless music editorial. Existing real recorded Sajad and synthetic Ava; original user-provided covers and music. No presenter footage. Rights not independently cleared; no publication.',
  '-movflags','+faststart','-t',f'{total:.9f}',str(dest)]

def render(root,kind,tracks,plan,stills_only=False):
 design=Design(kind,root,tracks,plan);spec=spectrum(root/'audio.wav',FPS[kind],plan['duration'])
 snapshots=[1.,7.,25.,42.,75.,111.,145.,178.,190.] if kind=='youtube' else [1.,6.,11.,16.,21.,26.,30.]
 for t in snapshots:
  frame=design.frame(t,spec[min(len(spec)-1,round(t*FPS[kind]))]);frame.save(root/f'preview-{t:05.1f}.jpg',quality=94)
 thumb=design.frame(1.8,np.zeros(48),thumbnail=True)
 if kind=='youtube':thumb.resize((1280,720),Image.Resampling.LANCZOS).save(root/'thumbnail.jpg',quality=96)
 else:thumb.save(root/'cover.jpg',quality=95)
 if stills_only:return
 cmd=command(root,kind,plan['duration']);(root/'render-command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2)+'\n')
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE);started=time.monotonic();last_index=-1;last_frame=None;previous=None
 try:
  for i,level in enumerate(spec):
   t=i/FPS[kind];im=design.frame(t,level)
   # Cache last outgoing image for a short editorial dissolve; does not shift audio/captions.
   index=next((n for n,e in enumerate(plan['events']) if t<e['end']+(.25 if kind=='youtube' else 0)),len(plan['events'])-1)
   event=plan['events'][index]
   if index!=last_index:previous=last_frame;last_index=index
   if previous is not None and t-event['start']<.20:
    im=Image.blend(previous,im,ease((t-event['start'])/.20))
   last_frame=im
   process.stdin.write(im.tobytes())
   if i%(FPS[kind]*15)==0:print(f'{kind}: {t:.0f}/{plan["duration"]:.1f}s, elapsed {time.monotonic()-started:.0f}s',flush=True)
 finally:
  process.stdin.close();code=process.wait()
 if code:raise subprocess.CalledProcessError(code,cmd)
 print('DONE',cmd[-1],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True)
 p.add_argument('--root',type=Path);p.add_argument('--stills-only',action='store_true');p.add_argument('--render-only',action='store_true')
 a=p.parse_args();root=(a.root or REPO/f'rendered/video-006-faceless/{a.kind}').resolve();plan=make_plan(a.kind)
 tracks=json.loads((HERE.parent/'003-chavoshi-studio/tracks.json').read_text())
 if not a.render_only:prepare(root,tracks,plan)
 render(root,a.kind,tracks,plan,a.stills_only)

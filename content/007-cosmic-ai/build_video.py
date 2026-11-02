"""Surreal faceless music film: entirely synthetic speech, longer original music.
All human-recording/voice-cloning paths are deliberately absent. No publication.
"""
import argparse,hashlib,importlib.util,json,math,subprocess,sys,time,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
import persian_display as pd

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
spec=importlib.util.spec_from_file_location('editorial006',HERE.parent/'006-faceless-music/build_video.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FF=base.FF;RATE=48000;FPS={'youtube':25,'reel':30};SIZES=base.SIZES
TRACKS=json.loads((HERE.parent/'003-chavoshi-studio/tracks.json').read_text())
DIALOGUE=json.loads((HERE/'dialogue.fa.json').read_text());AUDIO=HERE/'audio'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def run(args):base.run(args)
def wavdata(path):
 with wave.open(str(path)) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(RATE,2,2)
  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float32)/32768

def captions_for(event):
 words=event['text'].split();groups=[' '.join(words[i:i+4]) for i in range(0,len(words),4)]
 weights=np.array([len(s) for s in groups],dtype=float);weights/=weights.sum();cursor=event['start'];out=[]
 for i,(s,w) in enumerate(zip(groups,weights)):
  end=event['end'] if i==len(groups)-1 else cursor+w*event['duration']
  out.append({'start':cursor,'end':end-.015,'text':s});cursor=end
 return out

def prepare(kind,root):
 root.mkdir(parents=True,exist_ok=True);media=root/'source-media';media.mkdir(exist_ok=True)
 normalized=root/'normalized';normalized.mkdir(exist_ok=True);assets=[];speech=[]
 # Recover exact original music and cover blobs. Never pull speech from earlier MP4s.
 for tr in TRACKS:
  for key in ('file','cover'):
   path='Artist/1-Mohsen-Chavoshi/'+tr[key]
   blob=subprocess.check_output(['git','rev-parse',f'{base.PIN}:{path}'],cwd=REPO,text=True).strip()
   p=media/tr[key]
   with p.open('wb') as f:subprocess.run(['git','cat-file','blob',blob],cwd=REPO,stdout=f,check=True)
   assets.append({'path':path,'file':tr[key],'gitBlob':blob,'sha256':sha(p)})
 ids=['01','04','05','06','07','08','09','10'] if kind=='youtube' else ['01','10']
 pcm={}
 for row in DIALOGUE:
  if row['id'] not in ids:continue
  source=AUDIO/(row['id']+'.mp3')
  if not source.is_file():raise FileNotFoundError('Fresh selected AI speech is required; human/old voice fallback forbidden: '+str(source))
  out=normalized/(row['id']+'.wav')
  run(['-i',source,'-vn','-af','aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2:LRA=10',
       '-ar',RATE,'-ac',2,'-c:a','pcm_s16le',out])
  pcm[row['id']]=wavdata(out)
  speech.append({'id':row['id'],'voice':row['voice'],'speaker':row['speaker'],'text':row['text'],
   'sourceSha256':sha(source),'normalizedSha256':sha(out),'duration':len(pcm[row['id']])/RATE})
 samples=[];events=[];cursor=0.;captions=[];ctas=[]
 def append(data,info):
  nonlocal cursor
  duration=len(data)/RATE;e=dict(start=cursor,end=cursor+duration,duration=duration,sceneDuration=duration+.24,**info)
  events.append(e);samples.extend([data,np.zeros((round(.24*RATE),2),dtype=np.float32)]);cursor+=duration+.24
  if e['type']=='speech':captions.extend(captions_for(e))
  return e
 def music(tr):
  duration=20 if kind=='youtube' else 8;offset=tr['excerptStart']+(2 if kind=='reel' else 0)
  out=normalized/(tr['id']+'.wav')
  run(['-ss',offset,'-i',media/tr['file'],'-t',duration,'-af',
   f'aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-2:LRA=10,afade=t=in:d=0.18,afade=t=out:st={duration-.32}:d=0.32',
   '-ar',RATE,'-ac',2,'-c:a','pcm_s16le',out])
  data=wavdata(out);assert abs(len(data)/RATE-duration)<.01,'Source music window incomplete'
  append(data,dict(type='music',scene=tr['id'],visualScene=tr['id'],title=tr['title'],artist=tr['artist'],sourceStart=offset,sourceFile=tr['file']))
 lookup={r['id']:r for r in DIALOGUE};song_for={'04':TRACKS[0],'05':TRACKS[1],'07':TRACKS[2],'08':TRACKS[3],'09':TRACKS[4]}
 if kind=='youtube':
  for id in ids:
   row=lookup[id];e=append(pcm[id],dict(type='speech',**row,visualScene=row['scene']))
   if id=='05':ctas.append({'start':e['start']+1,'end':min(e['end'],e['start']+5),'text':'این انتخابت بود؟ لایک کن'})
   if id=='06':ctas.append({'start':e['start']+1,'end':e['end']-.1,'text':'سابسکرایب | پیشنهادهای بعدی'})
   if id=='10':ctas.append({'start':e['start'],'end':e['end'],'text':'نام آهنگ را کامنت کن'})
   if id in song_for:music(song_for[id])
 else:
  append(pcm['01'],dict(type='speech',**lookup['01'],visualScene='opening'))
  for tr in TRACKS:music(tr)
  e=append(pcm['10'],dict(type='speech',**lookup['10'],visualScene='recap'))
  ctas.append({'start':e['start'],'end':e['end'],'text':'لایک + کامنت | انتخاب خودت'})
 # Original, quiet procedural transition sweeps. No downloaded/trending copyrighted FX.
 mixed=np.concatenate(samples)
 for e in events:
  if e['type']!='music':continue
  start=max(0,round((e['start']-.20)*RATE));n=min(round(.18*RATE),len(mixed)-start)
  tt=np.arange(n)/RATE;envelope=np.sin(np.pi*np.arange(n)/max(1,n-1))**2
  sweep=np.sin(2*np.pi*(160*tt+1800*tt*tt))*.009*envelope
  mixed[start:start+n]+=sweep[:,None]
 peak=float(abs(mixed).max());gain=min(1,.80/max(peak,1e-6));mixed*=gain
 out=root/'audio.wav'
 with wave.open(str(out),'wb') as w:w.setparams((2,2,RATE,0,'NONE','not compressed'));w.writeframes((np.clip(mixed,-1,1)*32767).astype('<i2').tobytes())
 plan={'kind':kind,'duration':len(mixed)/RATE,'events':events,'captions':captions,'ctas':ctas,'musicSampleCount':5,
  'musicSecondsEach':20 if kind=='youtube' else 8,'allSpeechSynthetic':True,'humanRecordingUsed':False,
  'captionTiming':'Four-word typographic groups proportionally timed; not forced phoneme alignment',
  'mixGain':gain,'proceduralTransitionFX':True}
 provenance={'allSpeechSynthetic':True,'humanRecordingUsed':False,'personalCloneUsed':False,'speech':speech,'assets':assets,
  'syntheticImages':[{'file':p.name,'sha256':sha(p),'origin':'AI-generated surreal environment; not a real location or artist depiction'} for p in sorted((HERE/'assets').glob('*.jpg'))],
  'logoSha256':sha(base.LOGO),'fontSha256':sha(HERE/'fonts/Lalezar-Regular.ttf')}
 for name,obj in [('timeline.json',plan),('source-provenance.json',provenance)]:
  (root/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 print('PREPARED',kind,round(plan['duration'],2),'seconds',flush=True)
 return plan

class Film(base.Design):
 def background(self):return Image.new('RGB',self.size,'#080c10')
 def __init__(self,kind,root,plan):
  super().__init__(kind,root,TRACKS,plan)
  self.photos={};w,h=self.size
  for p in (HERE/'assets').glob('*.jpg'):
   center=(.4,.5) if p.stem=='portal' else ((.28,.5) if p.stem=='piano' else (.5,.5))
   im=ImageOps.fit(Image.open(p).convert('RGB'),self.size,Image.Resampling.LANCZOS,centering=center)
   yy,xx=np.mgrid[0:h,0:w];v=yy/h
   # Preserve vivid center while protecting title and caption contrast.
   alpha=np.clip(85+90*(abs(v-.5)*2)**1.3+(50*(xx/w) if not self.vertical else 0),0,230).astype('uint8')
   shade=np.zeros((h,w,4),dtype=np.uint8);shade[:,:,3]=alpha
   self.photos[p.stem]=Image.alpha_composite(im.convert('RGBA'),Image.fromarray(shade)).convert('RGB')
  self.filmtext={};self.captiontext={}
 def branding(self,im):
  d=ImageDraw.Draw(im);x,y=(88,130) if self.vertical else (1520,55)
  d.rounded_rectangle((x-14,y-10,x+270,y+88),radius=13,fill='#e9e0cd')
  im.paste(self.logo,(x,y),self.logo)
 def film_put(self,im,s,right,top,size=90,color=base.CREAM):
  layer=pd.render(s,size,color);im.paste(layer,(round(right-layer.width),round(top)),layer)
 def caption(self,im,t,event):
  item=next((c for c in self.plan['captions'] if c['start']<=t<c['end']),None)
  if not item:return
  words=item['text'].split();size=76 if self.vertical else 66;maximum=770 if self.vertical else 1550
  while sum(pd.width(w,size) for w in words)+size*.25*(len(words)-1)>maximum:size-=1
  key=(item['text'],size)
  if key not in self.captiontext:
   space=size*.25;tiles=[pd.render(word,size,'#f8ce80' if i==len(words)-1 else '#fff7e7') for i,word in enumerate(words)]
   width=math.ceil(sum(tile.width for tile in tiles)+space*(len(words)-1))+40
   height=max(tile.height for tile in tiles)+28
   layer=Image.new('RGBA',(width,height));d=ImageDraw.Draw(layer)
   d.rounded_rectangle((0,0,width-1,height-1),radius=14,fill=(5,9,15,160))
   x=width-20
   for tile in tiles:
    x-=tile.width;layer.alpha_composite(tile,(round(x),round((height-tile.height)/2)));x-=space
   self.captiontext[key]=layer.crop(layer.getbbox())
  layer=self.captiontext[key];x=round((88+920-layer.width)/2) if self.vertical else (self.size[0]-layer.width)//2
  y=(1520 if self.vertical else 1015)-layer.height
  # Small eased entrance, no guessed word-by-word forced alignment claim.
  y+=round(10*(1-base.ease((t-item['start'])/.14)))
  im.paste(layer,(x,y),layer)
 def frame(self,t,levels,thumbnail=False):
  w,h=self.size;event=next((e for e in self.plan['events'] if t<e['start']+e['sceneDuration']),self.plan['events'][-1])
  scene=event['scene'];local=t-event['start'];idx=self.byid.get(scene,-1)
  name='piano' if scene in ('sange-saboor','amir-bi-gazand') else ('waves' if scene in ('beraghsa','interlude') else 'portal')
  zoom=1.03+.018*math.sin(t*.23);bw=w/zoom;bh=h/zoom
  x=(w-bw)/2+6*math.sin(t*.18);y=(h-bh)/2+4*math.cos(t*.2)
  im=self.photos[name].transform(self.size,Image.Transform.EXTENT,(x,y,x+bw,y+bh),Image.Resampling.BICUBIC)
  accent=base.ACCENTS[max(0,idx)];d=ImageDraw.Draw(im);energy=float(np.mean(levels))
  # Floating particles, orbit trails and moving optical flare: no rapid white flashes.
  for i in range(28):
   px=round((i*193+t*(8+i%5))%w);py=round((i*277-t*(7+i%4))%h)
   color=(round(90+70*energy),round(95+75*energy),round(100+60*energy))
   d.ellipse((px,py,px+1+(i%2),py+1+(i%2)),fill=color)
  # Beat-linked atmospheric halo; trails are restrained gold rather than RGB flashes.
  if event['type']=='music':
   side=840;fx=Image.new('RGBA',(side,side));fd=ImageDraw.Draw(fx)
   radius=265+12*energy;center=side/2
   for j in range(9):
    rr=radius+j*5;angle=(t*9+j*37)%360
    fd.arc((center-rr,center-rr,center+rr,center+rr),angle,angle+20+energy*30,fill=(238,194,116,round(15+energy*55)),width=2)
   fx=fx.filter(ImageFilter.GaussianBlur(2))
   fx.putalpha(fx.getchannel('A').point(lambda a:round(a*.85)))
   origin=(-250,390) if self.vertical else (160,35)
   im.paste(fx,origin,fx);d=ImageDraw.Draw(im)
  if not self.vertical:
   d.rectangle((0,0,w,34),fill='#030507');d.rectangle((0,h-34,w,h),fill='#030507')
  if t>1 or self.kind=='youtube':self.branding(im)
  if scene in ('opening','recap','interlude'):
   if scene=='opening':a,b=('چاوشی','فقط یکی!') if thumbnail else ('۵ آهنگ چاوشی','فقط یکی رو انتخاب کن')
   elif scene=='recap':a,b='انتخابت عوض شد؟','اسم آهنگ رو کامنت کن'
   else:a,b='انتخابت رو نگه دار','سه آهنگ دیگه مونده'
   right=920 if self.vertical else 1800;top=300 if self.vertical else 280
   title_size=125 if self.vertical else 148
   while pd.width(a,title_size)>(820 if self.vertical else 1350):title_size-=1
   self.film_put(im,a,right,top,title_size)
   self.film_put(im,b,right,top+170,70 if self.vertical else 90,'#f7c373')
   if scene=='opening' and not thumbnail:self.put(im,'رسانهٔ آهنگ‌بان',right,top+290,36,base.CREAM,True)
   if scene=='recap':self.put(im,'ahangban.ir',right,top+300,48,base.CREAM,True)
   for i,tr in enumerate(TRACKS):
    if self.vertical:center=(235+(i%3)*255,980+(i//3)*215);side=170
    else:center=(230+i*154,765+abs(i-2)*12);side=180
    self.cover(im,tr['id'],center,side,t+i,angle=(i-2)*-2)
  else:
   tr=TRACKS[idx];right=920 if self.vertical else 1800;top=290 if self.vertical else 240
   self.put(im,'انتخاب '+str(idx+1).translate(base.DIGITS)+' از ۵',right,top,34,accent,True)
   size=103 if self.vertical else 120
   while pd.width(tr['title'],size)>(830 if self.vertical else 980):size-=1
   self.film_put(im,tr['title'],right,top+95,size)
   self.put(im,tr['artist'],right,top+250,base.fit(tr['artist'],34,820,False),base.CREAM)
   self.put(im,tr['cue'],right,top+320,36,accent,True)
   center=(260,1150) if self.vertical else (265,755);self.cover(im,tr['id'],center,290 if self.vertical else 300,t,angle=-3)
   if event['type']=='music':
    label='در حال شنیدن  •  '+str(max(0,math.ceil(event['end']-t))).translate(base.DIGITS)
    self.put(im,label,right,1290 if self.vertical else 720,30,base.CREAM)
   # Narrow spectrum ribbon, leaving the cinematic environment visible.
   left,total,bottom,maxheight=(120,780,1360,65) if self.vertical else (980,800,840,120)
   for i,v in enumerate(levels):
    bh=3+round(float(v)*maxheight);bx=round(left+i*total/len(levels))
    d.rounded_rectangle((bx,bottom-bh,bx+8,bottom),radius=3,fill=accent)
  if not thumbnail:
   self.caption(im,t,event)
   cta=next((c for c in self.plan['ctas'] if c['start']<=t<c['end']),None)
   if cta:
    self.put(im,cta['text'],900 if self.vertical else 1780,655 if self.vertical else 135,28,'#ffe3a3',True)
  self.put(im,'ahangban.ir',900 if self.vertical else 1800,1560 if self.vertical else 1018,25,base.CREAM)
  d=ImageDraw.Draw(im);bar_y=1600 if self.vertical else 1051
  d.line((90,bar_y,w-90,bar_y),fill='#3c4247',width=2)
  d.line((90,bar_y,90+round((w-180)*t/self.plan['duration']),bar_y),fill=accent,width=3)
  return im

def command(root,kind,total):
 w,h=SIZES[kind]
 return [FF,'-v','warning','-y','-filter_threads','2','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}',
  '-r',str(FPS[kind]),'-i','pipe:0','-i',str(root/'audio.wav'),'-map','0:v:0','-map','1:a:0',
  '-c:v','libx264','-preset','veryfast','-crf','21','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
  '-metadata:s:a:0','language=fas','-metadata','comment=All speech synthetic: Ava voice-05, male narrator voice-04. AI-generated surreal environments, original supplied covers/music. No real Sajad recording, clone, presenter images or publication.',
  '-movflags','+faststart','-t',f'{total:.9f}',str(root/f'ahangban-cosmic-{kind}.mp4')]

def render(root,kind,plan,stills_only=False):
 film=Film(kind,root,plan);levels=base.spectrum(root/'audio.wav',FPS[kind],plan['duration'])
 times=[1.,12.]+[e['start']+3 for e in plan['events'] if e['type']=='music']+[plan['duration']-4]
 for i,t in enumerate(times):film.frame(t,levels[min(len(levels)-1,round(t*FPS[kind]))]).save(root/f'preview-{i:02d}.jpg',quality=95)
 thumbnail=film.frame(1.5,np.zeros(48),thumbnail=True)
 thumbnail.resize((1280,720) if kind=='youtube' else (1080,1920),Image.Resampling.LANCZOS).save(root/'cover.jpg',quality=95)
 if stills_only:return
 cmd=command(root,kind,plan['duration']);(root/'render-command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2)+'\n')
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE);started=time.monotonic();previous=None;last_scene=None;last_frame=None
 try:
  for i,values in enumerate(levels):
   t=i/FPS[kind];im=film.frame(t,values)
   event=next((e for e in plan['events'] if t<e['start']+e['sceneDuration']),plan['events'][-1])
   key=(event['start'],event['scene'])
   if key!=last_scene:previous=last_frame;last_scene=key
   if previous is not None and t-event['start']<.22:im=Image.blend(previous,im,base.ease((t-event['start'])/.22))
   last_frame=im;process.stdin.write(im.tobytes())
   if i%(FPS[kind]*20)==0:print(kind,f'{t:.0f}/{plan["duration"]:.1f}s',f'elapsed {time.monotonic()-started:.0f}s',flush=True)
 finally:
  process.stdin.close();code=process.wait()
 if code:raise subprocess.CalledProcessError(code,cmd)
 print('DONE',cmd[-1],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);p.add_argument('--stills-only',action='store_true');p.add_argument('--render-only',action='store_true')
 args=p.parse_args();root=REPO/f'rendered/video-007-cosmic/{args.kind}'
 plan=json.loads((root/'timeline.json').read_text()) if args.render_only else prepare(args.kind,root)
 render(root,args.kind,plan,args.stills_only)

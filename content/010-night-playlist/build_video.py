"""Night playlist: user-supplied originals, fresh approved voice identities, native 2D film.
No publication, voice speed/pitch changes, human recording or clones.
Excerpt selection is technical, NOT human listening or certified chorus detection.
"""
import argparse,hashlib,importlib.util,json,math,shutil,subprocess,sys,wave,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'007-cosmic-ai'))
import persian_display as pd
spec=importlib.util.spec_from_file_location('graphics006',HERE.parent/'006-faceless-music/build_video.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
FF=g.FF;RATE=48000;FPS=g.FPS;SIZES=g.SIZES;sha=g.sha
TRACKS=json.loads((HERE/'tracks.json').read_text());DIALOGUE=json.loads((HERE/'dialogue.fa.json').read_text());AUDIO=HERE/'audio'
SOURCE=REPO/'rendered/video-010-night-playlist/source-media'
MANIFEST=json.loads((HERE/'source-manifest.json').read_text())
PALETTE=['#efc27e','#cbd6c6','#d8afa0','#9cd7cf','#bed3f1']
PLATES=[HERE/'assets/rainy-night.jpg',HERE/'assets/empty-street.jpg',HERE/'assets/dawn-window.jpg']
run=g.run

def pcm(path):
 with wave.open(str(path)) as w:
  assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(2,2,RATE)
  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float32)/32768

def caption_cues(event,data):
 words=event['text'].split();groups=[' '.join(words[i:i+4]) for i in range(0,len(words),4)]
 weights=np.array([len(s) for s in groups],float);weights/=sum(weights)
 step=960;mono=data.mean(axis=1);rms=np.array([np.sqrt(np.mean(mono[i:i+step]**2)) for i in range(0,len(mono),step)])
 quiet=rms<.009;pauses=[];begin=None
 for i,q in enumerate(list(quiet)+[False]):
  if q and begin is None:begin=i
  if not q and begin is not None:
   if i-begin>=5:pauses.append((i+begin)*.01)
   begin=None
 boundaries=[0.];position=0.
 for w in weights[:-1]:
  position+=w*event['duration'];near=[p for p in pauses if abs(p-position)<.18 and p>boundaries[-1]+.3]
  boundaries.append(min(near,key=lambda p:abs(p-position)) if near else position)
 boundaries.append(event['duration'])
 return [{'start':event['start']+a,'end':event['start']+b-.012,'text':s} for a,b,s in zip(boundaries,boundaries[1:],groups)]

def onset_cuts(data,count):
 mono=data.mean(axis=1);hop=960
 energy=np.array([np.sqrt(np.mean(mono[i:i+hop]**2)) for i in range(0,len(mono),hop)])
 flux=np.maximum(0,np.diff(energy,prepend=0));threshold=np.percentile(flux,78)
 candidates=[i*.02 for i in range(1,len(flux)-1) if flux[i]>=threshold and flux[i]>flux[i-1] and flux[i]>=flux[i+1]]
 duration=len(data)/RATE;cuts=[0.]
 for target in np.linspace(0,duration,count+1)[1:-1]:
  near=[x for x in candidates if abs(x-target)<.75 and x>cuts[-1]+1.5]
  cuts.append(min(near,key=lambda x:abs(x-target)) if near else float(target))
 return cuts+[duration]

def prepare(kind,root):
 root.mkdir(parents=True,exist_ok=True);media=root/'source-media';media.mkdir(exist_ok=True);norm=root/'normalized';norm.mkdir(exist_ok=True)
 for a in MANIFEST['assets']:
  source=SOURCE/a['file'];assert sha(source)==a['sha256'];assert subprocess.check_output(['git','hash-object',str(source)],text=True).strip()==a['gitBlob']
  target=media/a['file']
  if not target.exists():shutil.copy2(source,target)
 speech=[];voices={};rows=DIALOGUE if kind=='youtube' else json.loads((HERE/'dialogue.vertical.fa.json').read_text())
 for row in rows:
  source=AUDIO/(row['id']+'.mp3');assert sha(source)==row['audioSha256'];target=norm/(row['id']+'.wav')
  run(['-i',source,'-ar',RATE,'-ac',2,'-c:a','pcm_s16le',target]);data=pcm(target)
  rms=float(np.sqrt(np.mean(data**2)));gain=min(.1/max(rms,1e-9),.84/max(float(abs(data).max()),1e-9))
  voices[row['id']]=data*gain;speech.append(dict(row,sourceSha256=sha(source),constantGain=gain,duration=len(data)/RATE))
 events=[];samples=[];captions=[];cursor=0.
 def append(data,info):
  nonlocal cursor
  duration=len(data)/RATE;e=dict(start=cursor,end=cursor+duration,duration=duration,sceneDuration=duration+.28,**info)
  events.append(e);samples.extend([data,np.zeros((round(.28*RATE),2),np.float32)]);cursor+=duration+.28
  if e['type']=='speech':captions.extend(caption_cues(e,data))
  return e
 def talk(id,scene=None):
  row=next(r for r in rows if r['id']==id);info=dict(row);info['scene']=scene or row.get('scene', 'opening' if id=='v01' else 'recap')
  append(voices[id],dict(type='speech',**info))
 def music(tr):
  duration=35 if kind=='youtube' else 12;offset=tr['excerptStart'] if kind=='youtube' else tr['verticalExcerptStart'];target=norm/(tr['id']+'.wav')
  assert offset+duration<=tr['sourceDurationSeconds']
  run(['-ss',offset,'-i',media/tr['file'],'-map','0:a:0','-t',duration,'-af',f'loudnorm=I=-18:TP=-2:LRA=10,afade=t=in:d=0.18,afade=t=out:st={duration-.35}:d=0.35','-ar',RATE,'-ac',2,'-c:a','pcm_s16le',target])
  data=pcm(target);assert abs(len(data)/RATE-duration)<.001
  append(data,dict(type='music',scene=tr['id'],title=tr['title'],artist=tr['artist'],sourceFile=tr['file'],sourceStart=offset,cameraCutsLocal=onset_cuts(data,4 if kind=='youtube' else 3)))
 if kind=='youtube':
  talk('01');music(TRACKS[0]);talk('02',TRACKS[1]['id']);music(TRACKS[1]);talk('03');talk('04',TRACKS[2]['id']);music(TRACKS[2]);talk('05','recap');talk('06','recap')
 else:
  talk('v01')
  for tr in TRACKS:music(tr)
  talk('v02','recap')
 mixed=np.concatenate(samples);gain=min(1,.80/max(float(abs(mixed).max()),1e-6));mixed*=gain
 with wave.open(str(root/'audio.wav'),'wb') as w:w.setparams((2,2,RATE,0,'NONE','not compressed'));w.writeframes((np.clip(mixed,-1,1)*32767).astype('<i2').tobytes())
 plan=dict(kind=kind,duration=len(mixed)/RATE,events=events,captions=captions,ctas=[],musicSecondsEach=35 if kind=='youtube' else 12,allNarrationSynthetic=True,humanRecordingUsed=False,approvedVoiceIdentitiesUsed=True,voicePitchOrSpeedChanged=False,mixGain=gain,captionTiming='Proportional short groups nudged toward nearby quiet gaps; NOT forced alignment',cameraTiming='Positive RMS-energy onset guided, not certified tempo/beat detection')
 prov=dict(speech=speech,assets=MANIFEST['assets'],sourceCommit=MANIFEST['sourceCommit'],logoSha256=sha(g.LOGO),environmentPlates=[dict(path=str(p.relative_to(REPO)),sha256=sha(p),origin='AI-generated still, animated as 2D environment') for p in PLATES],allNarrationSynthetic=True,humanRecordingUsed=False,personalCloneUsed=False,excerptSelection=MANIFEST['excerptSelection'],userSuppliedWebLinks=MANIFEST['userSuppliedWebLinks'])
 for name,data in [('timeline.json',plan),('source-provenance.json',prov)]: (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print('PREPARED',kind,round(plan['duration'],2),flush=True);return plan

class Artwork(g.Design):
 def __init__(self,kind,root,plan):
  super().__init__(kind,root,TRACKS,plan);self.captiontext={}
 def big(self,im,s,right,top,size,color=g.CREAM,maxwidth=None):
  # pd shapes an RTL Arabic run: preserve internal visual order of multi-digit numbers.
  s=re.sub(r'[۰-۹0-9]{2,}',lambda m:m.group()[::-1],s)
  while maxwidth and pd.width(s,size)>maxwidth:size-=1
  layer=pd.render(s,size,color);im.alpha_composite(layer,(round(right-layer.width),round(top)))
 def overlay(self,event,variant=0,thumbnail=False):
  w,h=self.size;v=self.vertical;im=Image.new('RGBA',self.size);d=ImageDraw.Draw(im)
  x,y=(88,125) if v else (1530,60);d.rounded_rectangle((x-12,y-10,x+268,y+88),radius=12,fill='#eee4d1');im.paste(self.logo,(x,y),self.logo)
  right=918 if v else 1800;top=300 if v else 255
  scene=event['scene'];idx=self.byid.get(scene,-1);accent=PALETTE[max(0,idx)]
  if idx>=0:
   tr=TRACKS[idx];self.big(im,'انتخاب '+str(idx+1).translate(g.DIGITS)+' از ۳',right,top,34,accent)
   self.big(im,tr['title'],right,top+95,100 if v else 120,maxwidth=810 if v else 1080)
   self.big(im,tr['artist'],right,top+260,46 if v else 48,g.CREAM,maxwidth=810)
   self.big(im,tr['cue'],right,top+350,32,accent,maxwidth=810)
   if event['type']=='music':self.big(im,('۱۲' if v else '۳۵')+' ثانیه با این آهنگ',right,1270 if v else 740,30,accent)
  else:
   if scene=='opening':a,b=('وقتی خواب نمیاد…','کدوم آهنگ؟') if thumbnail else ('وقتی شب تموم نمی‌شه','سه آهنگ، سه حال‌وهوا')
   elif scene=='recap':a,b='انتخاب امشبت کدومه؟','اسم آهنگ رو کامنت کن'
   else:a,b='یه آهنگ، یه خاطره؟','جوابش برای همه یکی نیست'
   self.big(im,a,right,top+40,94 if v else 112,maxwidth=805 if v else 1350)
   self.big(im,b,right,top+200,66 if v else 80,'#efc27e',maxwidth=810 if v else 1100)
   self.big(im,'رسانهٔ آهنگ‌بان',right,top+340,34,g.CREAM)
   if scene=='recap':self.put(im,'ahangban.ir',right,top+430,42,g.CREAM,True)
  self.put(im,'ahangban.ir',900 if v else 1800,1570 if v else 1015,27,g.CREAM)
  d.line((88,1610 if v else 1050,w-88,1610 if v else 1050),fill=(235,208,160,75),width=2)
  if not v:d.rectangle((0,0,w,30),fill=(2,4,7,255));d.rectangle((0,h-28,w,h),fill=(2,4,7,255))
  return im
 def art_layer(self,event,variant):
  v=self.vertical;im=Image.new('RGBA',self.size);idx=self.byid.get(event['scene'],-1)
  if idx>=0:
   center=(490,1035) if v else (395,610);side=410 if v else 510
   self.cover(im,TRACKS[idx]['id'],center,side,variant*2,angle=-2+variant)
  else:
   for i,tr in enumerate(TRACKS):
    center=(230+i*270,1000+abs(i-1)*22) if v else (235+i*210,785+abs(i-1)*14)
    self.cover(im,tr['id'],center,195 if v else 220,i,angle=(i-1)*-3)
  return im
 def caption_image(self,text):
  im=Image.new('RGBA',self.size);v=self.vertical;words=text.split();size=72 if v else 65;limit=790 if v else 1500
  while True:
   tiles=[pd.render(word,size,'#f6ca7f' if i==len(words)-1 else '#fff8eb') for i,word in enumerate(words)]
   width=math.ceil(sum(t.width for t in tiles)+size*.23*(len(words)-1))+38
   if width<=limit:break
   size-=1
  height=max(t.height for t in tiles)+26;panel=Image.new('RGBA',(width,height));d=ImageDraw.Draw(panel)
  d.rounded_rectangle((0,0,width-1,height-1),radius=12,fill=(4,8,12,195));x=width-19
  for tile in tiles:x-=tile.width;panel.alpha_composite(tile,(round(x),(height-tile.height)//2));x-=size*.23
  im.alpha_composite(panel,((1008-width)//2 if v else (self.size[0]-width)//2,(1518 if v else 997)-height));return im

def background(index,kind):
 size=SIZES[kind];w,h=size;v=kind=='reel';p=PLATES[index]
 center=(.38,.5) if index==0 else ((.29,.5) if index==1 else (.48,.5))
 im=ImageOps.fit(Image.open(p).convert('RGB'),size,Image.Resampling.LANCZOS,centering=center)
 yy,xx=np.mgrid[0:h,0:w];shade=np.clip(38+80*(abs(yy/h-.48)*2)**1.3+(70*(xx/w)**1.5 if not v else 14),0,220).astype('uint8')
 layer=np.zeros((h,w,4),np.uint8);layer[:,:,3]=shade
 return Image.alpha_composite(im.convert('RGBA'),Image.fromarray(layer)).convert('RGB')

def caption_track(root,shot,film):
 directory=root/'layers';start=shot['start'];end=shot['end'];timeline=[];cursor=start
 for cue in film.plan['captions']:
  a=max(start,cue['start']);z=min(end,cue['end'])
  if z<=a:continue
  if a>cursor:timeline.append(('blank.png',a-cursor))
  name='cue-'+hashlib.sha1(cue['text'].encode()).hexdigest()[:16]+'.png';p=directory/name
  if not p.exists():film.caption_image(cue['text']).save(p)
  timeline.append((name,z-a));cursor=z
 if cursor<end:timeline.append(('blank.png',end-cursor))
 path=directory/f'captions-{shot["index"]:03d}.ffconcat';text='ffconcat version 1.0\n'
 for name,duration in timeline:text+=f"file '{name}'\nduration {duration:.9f}\n"
 text+="file 'blank.png'\n";path.write_text(text);return path

def make_shots(plan):
 fps=FPS[plan['kind']];shots=[];events=plan['events']
 for i,event in enumerate(events):
  end=events[i+1]['start'] if i+1<len(events) else plan['duration']
  cuts=event.get('cameraCutsLocal',[0.,event['duration']]);cuts=[event['start']+x for x in cuts[:-1]]+[end]
  for variant,(a,z) in enumerate(zip(cuts,cuts[1:])):
   first=round(a*fps);last=round(z*fps)
   shots.append(dict(index=len(shots),eventIndex=i,variant=variant,start=first/fps,end=last/fps,frames=last-first))
 return shots

def shot_command(root,kind,shot,event,caption_file):
 fps=FPS[kind];w,h=SIZES[kind];v=kind=='reel';n=shot['frames'];variant=shot['variant'];idx=next((i for i,t in enumerate(TRACKS) if t['id']==event['scene']),0)
 layer=root/'layers';duration=n/fps;offset=shot['start']-event['start'];color=PALETTE[idx].replace('#','0x')
 args=[FF,'-v','error','-y','-filter_complex_threads','2','-i',str(layer/f'bg-{idx}.jpg'),
 '-loop','1','-framerate','1','-i',str(layer/f'title-{shot["eventIndex"]}.png'),
 '-loop','1','-framerate','1','-i',str(layer/f'art-{shot["eventIndex"]}-{variant}.png'),
 '-ss',str(shot['start']),'-i',str(root/'audio.wav'),'-f','concat','-safe','0','-i',str(caption_file),
 '-loop','1','-framerate','1','-i',str(layer/'light-wipe.png')]
 zoom=['1.012+0.055*on/'+str(n),'1.14-0.025*on/'+str(n),'1.07+0.025*on/'+str(n),'1.075-0.04*on/'+str(n)][variant%4]
 graph=f"[0:v]scale=in_range=full:out_range=tv,format=yuv420p,zoompan=z='{zoom}':x='iw/2-iw/zoom/2+12*sin(on/{fps}*.3)':y='ih/2-ih/zoom/2':d={n}:s={w}x{h}:fps={fps},setsar=1,format=yuv420p[bg];"
 graph+=f"[bg][2:v]overlay=x='4*sin(t*.7)':y='3*cos(t*.6)':eval=frame:shortest=0[art];[art][1:v]overlay=0:0:shortest=0[title];"
 graph+=f"[title][4:v]overlay=0:0:shortest=0[caption];"
 current='caption'
 if event['type']=='music':
  sw,sh=(790,85) if v else (800,115);sx,sy=(110,1325) if v else (975,800)
  graph+=f"[3:a]aformat=channel_layouts=mono,showfreqs=s={sw}x{sh}:mode=bar:ascale=log:fscale=log:win_size=2048:rate={fps}:colors={color},colorkey=0x000000:0.08:0.02[spectrum];"
  graph+=f"[{current}][spectrum]overlay={sx}:{sy}:shortest=0[wave];";current='wave'
  graph+=f"color=c={color}:s={sw}x4:r={fps},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(X/W,(T+{offset})/{event['duration']}),240,35)'[progress];"
  graph+=f"[{current}][progress]overlay={sx}:{sy+sh+26}:shortest=0[progressed];";current='progressed'
 graph+=f"[{current}][5:v]overlay=x='-260+(W+520)*t/.36':y=0:enable='between(t,0,.36)'[final]"
 return args+['-filter_complex',graph,'-map','[final]','-an','-frames:v',str(n),'-r',str(fps),'-c:v','libx264','-preset','veryfast','-crf','21','-threads','2','-pix_fmt','yuv420p',str(root/'shots'/f'{shot["index"]:03d}.mp4')]

def render(root,kind,plan,stills_only=False,limit=None):
 layers=root/'layers';layers.mkdir(exist_ok=True);(root/'shots').mkdir(exist_ok=True);film=Artwork(kind,root,plan)
 w,h=SIZES[kind]
 for idx in range(len(TRACKS)):background(idx,kind).save(layers/f'bg-{idx}.jpg',quality=96)
 Image.new('RGBA',(w,h)).save(layers/'blank.png')
 xx=np.linspace(-1,1,260);alpha=(np.exp(-xx*xx*18)*28).astype('uint8');fx=np.zeros((h,260,4),np.uint8);fx[:,:,:3]=(244,211,156);fx[:,:,3]=alpha[None,:]
 Image.fromarray(fx).save(layers/'light-wipe.png')
 shots=make_shots(plan)
 for i,e in enumerate(plan['events']):
  film.overlay(e).save(layers/f'title-{i}.png')
  for variant in range(4):film.art_layer(e,variant).save(layers/f'art-{i}-{variant}.png')
  idx=next((j for j,t in enumerate(TRACKS) if t['id']==e['scene']),0)
  preview=background(idx,kind).convert('RGBA');preview.alpha_composite(film.art_layer(e,0));preview.alpha_composite(film.overlay(e));preview.convert('RGB').save(root/f'preview-{i:02d}.jpg',quality=94)
 cover=background(0,kind).convert('RGBA');cover.alpha_composite(film.art_layer(plan['events'][0],0));cover.alpha_composite(film.overlay(plan['events'][0],thumbnail=True))
 cover.convert('RGB').resize((1280,720) if kind=='youtube' else (1080,1920),Image.Resampling.LANCZOS).save(root/'cover.jpg',quality=95)
 (root/'shots.json').write_text(json.dumps(shots,indent=2)+'\n')
 if stills_only:return
 commands=[]
 for shot in shots[:limit]:
  event=plan['events'][shot['eventIndex']];cf=caption_track(root,shot,film);cmd=shot_command(root,kind,shot,event,cf);commands.append(cmd)
  print('SHOT',kind,shot['index']+1,'/',len(shots),event['scene'],f'{shot["end"]-shot["start"]:.2f}s',flush=True)
  subprocess.run(cmd,check=True)
 (root/'render-commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
 if limit:return
 concat=root/'video.ffconcat';concat.write_text('ffconcat version 1.0\n'+''.join(f"file 'shots/{s['index']:03d}.mp4'\n" for s in shots))
 run(['-f','concat','-safe','0','-i',concat,'-i',root/'audio.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-metadata:s:a:0','language=fas','-metadata','comment=Approved voice-06 and voice-07 conversational performances. AI environments animated in 2D, original music/covers. No human recording, clone, pitch or speed change.','-movflags','+faststart','-t',plan['duration'],root/f'ahangban-night-playlist-{kind}.mp4'])
 print('DONE',kind,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);p.add_argument('--stills-only',action='store_true');p.add_argument('--render-only',action='store_true');p.add_argument('--limit',type=int);a=p.parse_args()
 root=REPO/f'rendered/video-010-night-playlist/{a.kind}';plan=json.loads((root/'timeline.json').read_text()) if a.render_only else prepare(a.kind,root)
 render(root,a.kind,plan,a.stills_only,a.limit)

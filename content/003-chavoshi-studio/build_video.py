"""Studio edition: existing approved synthetic speech + supplied music excerpts.
No publication, credentials, voice cloning or implied lip sync. Large inputs/outputs
stay under ignored rendered/. Reuses local selected speech, never regenerates it.
"""
from pathlib import Path
import argparse,array,hashlib,json,math,shutil,subprocess,wave
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance
import arabic_reshaper
from bidi.algorithm import get_display
import imageio_ffmpeg
import timing

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
STUDIO=REPO/'studio/ahangban-signature'
FONTS=HERE.parent/'001-chavoshi-start/fonts'
FF=imageio_ffmpeg.get_ffmpeg_exe()
PINNED='d318f9f7095ab6c966a743ad3461e8f6fab0db34'
RATE=48000;FPS=25;GAP=.25;SIZE=(1920,1080)
WHITE='#f4f1ea';MUTED='#bcc7ce';BLUE='#8ac6e3';GOLD='#dec49a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def run(args):
 subprocess.run([FF,'-hide_banner','-loglevel','warning','-y',*map(str,args)],check=True)

def font(size,bold=False):
 return ImageFont.truetype(str(FONTS/('Vazirmatn-Bold.ttf' if bold else 'Vazirmatn-Regular.ttf')),size)

def text(draw,s,x,y,size=40,fill=WHITE,bold=False,anchor='rt'):
 draw.text((x,y),get_display(arabic_reshaper.reshape(s)),font=font(size,bold),fill=fill,anchor=anchor)

def panel(im,box,opacity=232):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 d.rounded_rectangle(box,radius=18,fill=(13,23,32,opacity),outline=(126,154,172,155),width=2)
 return Image.alpha_composite(im.convert('RGBA'),layer)

def prepare_inputs(root,tracks,dialogue,speech_root,male_root):
 media=root/'source-media';audio=root/'audio'
 media.mkdir(exist_ok=True);audio.mkdir(exist_ok=True)
 provenance={'repository':'Masoumiofficial/ahangban-youtube','revision':PINNED,'music':[],'speech':[],
             'voiceSelection':{'female':'voice-00','male':'voice-02','scope':'Selected session voices, not portable voice models'}}
 for track in tracks:
  for key in ('file','cover'):
   name=track[key];path=f'Artist/1-Mohsen-Chavoshi/{name}'
   blob=subprocess.check_output(['git','rev-parse',f'{PINNED}:{path}'],cwd=REPO,text=True).strip()
   dest=media/name
   # Recover the exact pinned Git blob rather than redownloading or substituting.
   with dest.open('wb') as f:subprocess.run(['git','cat-file','blob',blob],cwd=REPO,stdout=f,check=True)
   provenance['music'].append({'path':path,'gitBlob':blob,'file':str(dest.relative_to(root)),'sha256':sha(dest),'bytes':dest.stat().st_size})
 for item in dialogue:
  ismale=item['speaker']=='male'
  source=(male_root if ismale else speech_root)/(item['id']+('.wav' if ismale else '.mp3'))
  if not source.is_file():raise FileNotFoundError(f'Selected speech source missing: {source}; no silent fallback to the old male voice')
  dest=audio/source.name;shutil.copy2(source,dest)
  provenance['speech'].append({'id':item['id'],'speaker':item['speaker'],'voice':'voice-02' if ismale else 'voice-00',
                              'file':str(dest.relative_to(root)),'sha256':sha(dest),'source':str(source.relative_to(REPO))})
 (root/'source-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 return provenance

def pcm(path):
 with wave.open(str(path)) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(RATE,2,2)
  return w.readframes(w.getnframes())

def assemble(root,tracks,dialogue):
 normalized=root/'normalized';normalized.mkdir(exist_ok=True)
 assembled=bytearray();events=[];captions=[];trackmap={t['id']:t for t in tracks}
 def append(data,info):
  start=len(assembled)/(RATE*4);duration=len(data)/(RATE*4)
  assembled.extend(data);assembled.extend(b'\0'*(round(RATE*GAP)*4))
  event={**info,'start':start,'end':start+duration,'duration':duration,'sceneDuration':duration+GAP}
  events.append(event);return event
 for item in dialogue:
  source=root/'audio'/(item['id']+('.wav' if item['speaker']=='male' else '.mp3'))
  out=normalized/(item['id']+'.wav')
  run(['-i',source,'-af','aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11','-ar',RATE,'-ac',2,'-c:a','pcm_s16le',out])
  data=pcm(out);event=append(data,{'type':'speech',**item})
  samples=array.array('h',data)
  mono=array.array('h',((samples[i]+samples[i+1])//2 for i in range(0,len(samples),2))).tobytes()
  pauses=timing.pauses(mono);chunks=timing.text_chunks(item['text']);previous=0
  for i,(words,a,b) in enumerate(chunks):
   expected=event['duration']*chunks[i+1][1]/len(item['text']) if i+1<len(chunks) else event['duration']
   end=timing.closest(expected,pauses,previous+.5,event['duration']) if i+1<len(chunks) else event['duration']
   captions.append({'start':event['start']+previous,'end':event['start']+end-.035,'text':timing.wrap(words)})
   previous=end
  if item['speaker']=='female' and item['scene'] in trackmap:
   t=trackmap[item['scene']];out=normalized/(t['id']+'-sample.wav')
   run(['-ss',t['excerptStart'],'-i',root/'source-media'/t['file'],'-t',t['excerptDuration'],
        '-af',f'aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-2:LRA=9,afade=t=in:d=0.45,afade=t=out:st={t["excerptDuration"]-.65}:d=0.65',
        '-ar',RATE,'-ac',2,'-c:a','pcm_s16le',out])
   append(pcm(out),{'type':'music','scene':t['id'],'title':t['title'],'artist':t['artist'],'sourceOffset':t['excerptStart'],'sourceFile':t['file']})
 total=len(assembled)/(RATE*4)
 with wave.open(str(root/'mixed.wav'),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(assembled)
 timeline={'duration':total,'events':events,'musicSampleCount':5,'captions':captions,
           'captionTiming':'Text-proportional with nearby pauses; no forced alignment / phonetic review'}
 (root/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
 return timeline

def make_cards(root,tracks,timeline,presenter_image=None):
 cards=root/'cards';cards.mkdir(exist_ok=True)
 presenter_image=presenter_image or STUDIO/'productions/HOSTS-VIEW-001.png'
 im=Image.open(presenter_image).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 trackmap={t['id']:t for t in tracks}
 for i,event in enumerate(timeline['events']):
  scene=event['scene'];track=trackmap.get(scene)
  if event['type']=='speech':
   card=panel(im,(470,790,1450,955));d=ImageDraw.Draw(card)
   female=event['speaker']=='female';name='آوا' if female else 'سجاد';accent=BLUE if female else GOLD
   d.rounded_rectangle((1235,806,1418,850),radius=10,fill=(35,57,69,255))
   text(d,name,1394,810,30,accent,True)
   title=track['title'] if track else ('پنج نقطهٔ شروع با محسن چاوشی' if scene=='opening' else 'انتخاب اول تو کدام است؟')
   text(d,title,1205,813,32,WHITE,True)
   subtitle=track['cue'] if track else ('معرفی و نمونهٔ شنیداری' if scene=='opening' else 'نام آهنگ را در کامنت بنویس')
   text(d,subtitle,1398,866,27,MUTED)
  else:
   # A graphic cutaway, not a second studio angle or modified room.
   card=panel(im,(365,325,1555,955),246);d=ImageDraw.Draw(card)
   art=ImageOps.contain(Image.open(root/'source-media'/track['cover']).convert('RGB'),(430,430),Image.Resampling.LANCZOS)
   card.paste(art,(430+(430-art.width)//2,390+(430-art.height)//2))
   d=ImageDraw.Draw(card);d.rectangle((427,387,863,823),outline=(98,129,147,255),width=2)
   index=next(n for n,t in enumerate(tracks,1) if t['id']==scene)
   text(d,f'انتخاب {str(index).translate(str.maketrans("0123456789","۰۱۲۳۴۵۶۷۸۹"))} از ۵',1490,387,31,BLUE)
   text(d,track['title'],1490,478,56,WHITE,True)
   text(d,track['artist'],1490,576,31,MUTED)
   text(d,track['cue'],1490,662,34,GOLD)
   text(d,'نمونهٔ شنیداری • ۱۲ ثانیه',1490,748,29,MUTED)
  # Captions have a stable dark backing. Nothing covers the presenters' faces in speech.
  card=panel(card,(180,966,1740,1065),228)
  card.convert('RGB').save(cards/f'{i:02d}.png')
 concat='ffconcat version 1.0\n'
 for i,event in enumerate(timeline['events']):
  concat+=f"file '{(cards/f'{i:02d}.png').as_posix()}'\nduration {event['sceneDuration']:.6f}\n"
 last_card=cards/('{:02d}.png'.format(len(timeline['events'])-1))
 concat+=f"file '{last_card.as_posix()}'\n"
 (root/'visuals.ffconcat').write_text(concat)
 # Retain original logo pixels/proportions. Only the separate glow opacity cycles.
 core=Image.open(STUDIO/'overlays/AHANGBAN-LOGO-CORE.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 glow=Image.open(STUDIO/'overlays/AHANGBAN-LOGO-GLOW.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 bounds=glow.getbbox();assert bounds
 core.crop(bounds).save(root/'logo-core-crop.png');glow.crop(bounds).save(root/'logo-glow-crop.png')
 # A preview of the actual first card, with official mark rather than retyped branding.
 preview=Image.open(cards/'00.png').convert('RGBA');preview=Image.alpha_composite(preview,glow);preview=Image.alpha_composite(preview,core)
 preview.convert('RGB').resize((1600,900),Image.Resampling.LANCZOS).save(root/'studio-preview.jpg',quality=94)
 return bounds

def subtitles(root,timeline):
 captions=timeline['captions']
 (root/'subtitles.fa.srt').write_text('\n\n'.join(f'{i+1}\n{timing.clock(c["start"])} --> {timing.clock(c["end"])}\n{c["text"]}' for i,c in enumerate(captions))+'\n')
 ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Vazirmatn,42,&H00EAF1F4,&H00FFFFFF,&H0017200D,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,205,205,28,1
Style: Count,Vazirmatn,30,&H00E3C68A,&H00FFFFFF,&H0017200D,&H80000000,0,0,0,0,100,100,0,0,1,1,0,3,0,430,215,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 def event(a,b,style,words):return f'Dialogue: 1,{timing.clock(a,True)},{timing.clock(b,True)},{style},,0,0,0,,{words}\n'
 for c in captions:ass+=event(c['start'],c['end'],'Sub',c['text'].replace('\n',r'\N'))
 for e in timeline['events']:
  if e['type']=='music':
   ass+=event(e['start'],e['end'],'Sub',f'نمونهٔ شنیداری از «{e["title"]}»')
   for sec in range(math.ceil(e['duration'])):
    n=str(math.ceil(e['duration'])-sec).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
    ass+=event(e['start']+sec,min(e['start']+sec+1,e['end']),'Count','در حال پخش • '+n)
 (root/'subtitles.ass').write_text(ass)

def render_command(root,total,bounds=None):
 fonts=root/'fonts';fonts.mkdir(exist_ok=True)
 for f in FONTS.glob('*.ttf'):shutil.copy2(f,fonts/f.name)
 vf=(f"ass=filename='{(root/'subtitles.ass').as_posix()}':fontsdir='{fonts.as_posix()}',"
     f"fade=t=in:st=0:d=0.35,fade=t=out:st={total-.5}:d=0.5,format=yuv420p")
 return [FF,'-hide_banner','-loglevel','warning','-y','-filter_threads','2',
   '-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate',str(FPS),'-i','pipe:0',
   '-i',str(root/'mixed.wav'),'-map','0:v:0','-map','1:a:0','-vf',vf,
   '-c:v','libx264','-preset','veryfast','-crf','24','-threads','2','-r',str(FPS),
   '-c:a','aac','-b:a','192k','-af',f'afade=t=out:st={total-.25}:d=0.25',
   '-metadata:s:a:0','language=fas','-metadata','title=محسن چاوشی را از کدام آهنگ شروع کنیم؟ | استودیو آهنگ‌بان',
   '-metadata','comment=AI-generated static presenter imagery and selected synthetic voices. No lip sync. Third-party music excerpts; rights not independently verified. Review edit, not published.',
   '-movflags','+faststart','-t',f'{total:.6f}',str(root/'ahangban-chavoshi-studio-review.mp4')]

def render_frames(root,command,timeline):
 # Stream bounded-memory RGB frames. Avoid multi-input loop/overlay queues,
 # which can grow without bound for sparse image-concat timestamps.
 import time
 core=Image.open(root/'logo-core-crop.png').convert('RGBA')
 glow=Image.open(root/'logo-glow-crop.png').convert('RGBA')
 bounds=Image.open(STUDIO/'overlays/AHANGBAN-LOGO-GLOW.png').resize(SIZE,Image.Resampling.LANCZOS).getbbox()
 x,y,xx,yy=bounds
 plate=Image.open(root/'cards/00.png').convert('RGBA').crop(bounds)
 patches=[]
 for phase in range(FPS*6):
  intensity=.60+.30*math.sin(2*math.pi*phase/(FPS*6))
  light=glow.copy();light.putalpha(glow.getchannel('A').point(lambda a:round(a*intensity)))
  patches.append(Image.alpha_composite(Image.alpha_composite(plate,light),core).convert('RGB'))
 with wave.open(str(root/'mixed.wav')) as w: samples=array.array('h',w.readframes(w.getnframes()))
 count=math.ceil(timeline['duration']*FPS);events=timeline['events'];scene=-1;card=None
 started=time.monotonic();process=subprocess.Popen(command,stdin=subprocess.PIPE)
 try:
  for frame in range(count):
   t=frame/FPS
   index=next((i for i,e in enumerate(events) if t<e['start']+e['sceneDuration']),len(events)-1)
   if index!=scene:
    card=Image.open(root/'cards'/f'{index:02d}.png').convert('RGB');scene=index
   im=card.copy();im.paste(patches[frame%len(patches)],(x,y))
   d=ImageDraw.Draw(im);points=[];offset=round(t*RATE)
   for column in range(660):
    n=min(len(samples)//2-1,offset+round(column*RATE/(FPS*660)))
    value=(samples[n*2]+samples[n*2+1])/65536
    amplitude=math.copysign(math.sqrt(abs(value)),value)*15
    points.append((630+column,930-round(amplitude)))
   d.line(points,fill=BLUE,width=2)
   process.stdin.write(im.tobytes())
   if frame%(FPS*20)==0:print(f'Rendered {t:.0f}/{timeline["duration"]:.0f}s ({time.monotonic()-started:.0f}s elapsed)',flush=True)
 finally:
  process.stdin.close()
  code=process.wait()
 if code:raise subprocess.CalledProcessError(code,command)

def package_metadata(root,tracks,timeline,provenance):
 starts=[(0,'شروع؛ پنج انتخاب آهنگ‌بان')]
 for t in tracks:starts.append((next(e['start'] for e in timeline['events'] if e['scene']==t['id']),t['title']))
 starts.append((next(e['start'] for e in timeline['events'] if e['scene']=='recap'),'جمع‌بندی و انتخاب تو'))
 chaptertext='\n'.join(f'{int(t)//60:02d}:{int(t)%60:02d} {title}' for t,title in starts)
 (root/'chapters.txt').write_text(chaptertext+'\n',encoding='utf-8-sig')
 pages='\n'.join(f'{t["title"]}: {t["pageUrl"]}' for t in tracks if t['pageUrl'])
 description=f'''پنج پیشنهاد آهنگ‌بان برای شروع شنیدن محسن چاوشی، با اجرای صوتی آوا و سجاد در نمای استودیویی.
این فهرست انتخاب تحریریه است، نه رتبه‌بندی آماری.

کجایی — محسن چاوشی و سینا سرلک
سنگ صبور — محسن چاوشی
امیر بی‌گزند — محسن چاوشی
برقص آ — محسن چاوشی
بیست هزار آرزو — محسن چاوشی

{chaptertext}

{pages}

تصویر مجریان با هوش مصنوعی و صدای آن‌ها با گفتار مصنوعی ساخته شده است. تصویر مجریان ثابت است و لب‌خوانی ندارد.
نمونه‌های صوتی و کاورها متعلق به صاحبان حقوق آثارند؛ ذکر نام و کوتاه‌بودن نمونه جایگزین مجوز نیست و تضمین رفع Content ID محسوب نمی‌شود.
این نسخه برای بازبینی است و خودکار در یوتیوب منتشر نشده است.

برای آشنایی با چاوشی کدام آهنگ را پیشنهاد می‌کنی؟
#محسن_چاوشی #آهنگ_بان #معرفی_موسیقی
'''
 (root/'upload-description.txt').write_text(description,encoding='utf-8-sig')
 (root/'upload-title.txt').write_text('محسن چاوشی را از کدام آهنگ شروع کنیم؟ | ۵ پیشنهاد آهنگ‌بان\n',encoding='utf-8-sig')
 manifest={'status':'prepared_for_render','duration':timeline['duration'],'resolution':list(SIZE),'fps':FPS,
   'voices':provenance['voiceSelection'],'speechTurns':len(provenance['speech']),'musicSamples':5,
   'studioMasterSha256':sha(STUDIO/'master/MASTER-VIEW-001.png'),
   'presenterCompositeSha256':sha(STUDIO/'productions/HOSTS-VIEW-001.png'),
   'logoCoreSha256':sha(STUDIO/'overlays/AHANGBAN-LOGO-CORE.png'),
   'logoGlowSha256':sha(STUDIO/'overlays/AHANGBAN-LOGO-GLOW.png'),
   'presenterMotion':'Static reference-based still; no lip sync or facial animation',
   'visualMotion':'Audio-reactive waveform, isolated neon glow opacity cycle, timed music cutaways/countdown',
   'captionTiming':'Estimated text/pauses; not forced alignment','youtubePublished':False}
 (root/'production-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser();p.add_argument('--media-root',type=Path,default=REPO/'rendered/video-003-studio')
 p.add_argument('--speech-root',type=Path,default=REPO/'rendered/video-002/audio')
 p.add_argument('--male-root',type=Path,default=REPO/'rendered/studio-voice-revision')
 p.add_argument('--prepare-only',action='store_true');p.add_argument('--render-only',action='store_true');args=p.parse_args()
 root=args.media_root.resolve();root.mkdir(parents=True,exist_ok=True)
 if args.render_only:
  timeline=json.loads((root/'timeline.json').read_text())
  command=render_command(root,timeline['duration'])
  (root/'render-command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2)+'\n')
 else:
  tracks=json.loads((HERE/'tracks.json').read_text());dialogue=json.loads((HERE/'dialogue.fa.json').read_text())
  provenance=prepare_inputs(root,tracks,dialogue,args.speech_root.resolve(),args.male_root.resolve())
  timeline=assemble(root,tracks,dialogue);bounds=make_cards(root,tracks,timeline)
  subtitles(root,timeline);package_metadata(root,tracks,timeline,provenance)
  command=render_command(root,timeline['duration'],bounds)
  (root/'render-command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2)+'\n')
  print(f'PREPARED: {timeline["duration"]:.2f}s, 11 speech turns, new male voice-02, 5 music samples.',flush=True)
 if not args.prepare_only:
  print('RENDERING studio review MP4...',flush=True)
  render_frames(root,command,timeline)
  run(['-i',root/'mixed.wav','-c:a','libmp3lame','-b:a','192k',root/'mixed-audio.mp3'])
  manifest=json.loads((root/'production-manifest.json').read_text());manifest.update(status='rendered_pending_QA',videoSha256=sha(root/'ahangban-chavoshi-studio-review.mp4'))
  (root/'production-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  print('DONE:',root/'ahangban-chavoshi-studio-review.mp4',flush=True)
if __name__=='__main__':main()

"""Actual complete exports with a STATIC Ava. NO lip/head/listening inference.
Retains decoded original music-panel motion and byte-identical encoded source audio.
"""
import argparse,hashlib,json,subprocess,sys,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;EP=HERE.parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(EP));import build_layout as b;import build_mic_revision as r
FF=imageio_ffmpeg.get_ffmpeg_exe();WORK=ROOT/'rendered/ava-static-exports'
SETTINGS={'youtube':((1920,1080),25),'reel':((1080,1920),30)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def run(cmd):subprocess.run([str(x) for x in cmd],check=True)
def logo(im,x,y,width=235):
 l=Image.open(b.LOGO).convert('RGBA');l=l.crop(l.getbbox());l.thumbnail((width,round(width*.31)),Image.Resampling.LANCZOS)
 d=ImageDraw.Draw(im);d.rounded_rectangle((x-18,y-14,x+l.width+18,y+l.height+14),radius=17,fill='#eee8dc');im.alpha_composite(l,(x,y))
def center(im,text,x,y,size,color='#f2eadb',width=None):
 if width:
  while b.pd.width(text,size)>width and size>20:size-=1
 b.label(im,text,x,y,size,color,center=True)
def english(im,text,x,y,size):
 ImageDraw.Draw(im).text((x,y),text,font=ImageFont.truetype(str(ROOT/'content/001-chavoshi-start/fonts/Vazirmatn-Regular.ttf'),size),fill='#eadbc1')
def base(kind,panel):
 size,fps=SETTINGS[kind];im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
 if kind=='reel':
  # Upper891px transparent: continuously moving music-card crop of approved source.
  d.rectangle((0,850,1080,1024),fill='#101820');im.alpha_composite(panel,(0,1024))
  d=ImageDraw.Draw(im);d.rectangle((0,1024,1080,1027),fill='#bdac89')
  d.rounded_rectangle((36,1055,360,1123),radius=15,fill='#0b1219');b.label(im,'آوا ـ تصویر ثابت',61,1069,29)
  d.rectangle((0,1840,1080,1920),fill='#0b1219');english(im,'ahangban.ir',52,1862,29)
  center(im,'سه آهنگ برای آخر شب',780,1859,30,'#c9c4b9',width=430);logo(im,60,48)
 else:
  # Right-side unmodified actor plate. Left is real retained music-panel motion.
  d.rectangle((900,0,1920,1080),fill='#101820')
  for x in range(785,970):d.line((x,0,x,1080),fill=(16,24,32,round((x-785)/184*255)))
  p=panel.resize((844,700),Image.Resampling.LANCZOS);im.alpha_composite(p,(1020,250))
  d=ImageDraw.Draw(im);d.rounded_rectangle((1210,156,1680,225),radius=16,fill='#0b1219')
  center(im,'آوا ـ تصویر ثابت',1445,166,39);logo(im,1530,50,260)
 return im

def scene_label(plan,t):
 events=plan['events'];e=next((e for e in events if e['start']<=t<e['end']+.28),events[-1]);idx=next((i for i,tr in enumerate(b.TRACKS) if tr['id']==e['scene']),-1)
 return e,idx

def prepare(kind):
 size,fps=SETTINGS[kind];root=WORK/kind;root.mkdir(parents=True,exist_ok=True)
 plan=json.loads((ROOT/f'content/010-night-playlist/final-female/delivery/{kind}/timeline.json').read_text())
 source=ROOT/f'downloads/ahangban-night-final-{kind}.mp4';old=json.loads((ROOT/'content/010-night-playlist/final-female/delivery/manifest.json').read_text())['outputs'][kind]
 assert sha(source)==old['sha256']
 panel=r.studio_panel();panel.save(root/'ava-panel-fixed.png');original=base(kind,panel)
 total=round(plan['duration']*fps);boundaries={0,total}
 for row in plan['events']+plan['captions']:
  for k in ('start','end'):boundaries.add(max(0,min(total,round(row[k]*fps))))
 boundaries=sorted(boundaries);rows=[];listing=['ffconcat version 1.0']
 for i,(a,z) in enumerate(zip(boundaries,boundaries[1:])):
  t=(a+z)/(2*fps);e,idx=scene_label(plan,t);im=original.copy()
  cap=next((c['text'] for c in plan['captions'] if c['start']<=t<c['end']),None)
  if cap is None and e['type']=='speech' and t<e['end']:
   recent=[c for c in plan['captions'] if e['start']<=c['start']<=t]
   if recent:cap=recent[-1]['text']
  if kind=='reel':
   center(im,('انتخاب '+str(idx+1).translate(str.maketrans('123','۱۲۳'))+' از ۳') if idx>=0 else 'آخر شب، با آوا',865,58,29,'#c8b58d',width=310)
   if cap:center(im,cap,540,895,52,width=970)
   else:
    title=b.TRACKS[idx]['title'] if idx>=0 else 'انتخاب امشبت؟';artist=b.TRACKS[idx]['artist'] if idx>=0 else 'اسم آهنگ رو کامنت کن'
    center(im,title,540,867,55,width=960);center(im,artist,540,950,36,'#c8b58d',width=960)
  else:
   if idx>=0:
    center(im,b.TRACKS[idx]['title'],450,100,73,width=780);center(im,b.TRACKS[idx]['artist'],450,205,39,'#dbc08f',width=780)
   else:
    center(im,'آخر شب، با آوا',450,96,70,width=780);center(im,'سه آهنگ، یک حال‌وهوا',450,202,40,'#dbc08f',width=780)
   if e['type']=='speech':
    # Original source subtitles live on its right half and can extend into our
    # left crop. Mask that lower speech-only area; avoid duplicated/clipped words.
    dr=ImageDraw.Draw(im)
    for yy in range(810,870):dr.line((0,yy,970,yy),fill=(16,24,32,round((yy-810)/59*255)))
    dr.rectangle((0,870,970,1080),fill='#101820');english(im,'ahangban.ir',88,1020,26)
   if cap:center(im,cap,1445,987,43,width=880)
  file=root/f'overlay-{i:03d}.png';im.save(file)
  listing += [f"file '{file.as_posix()}'",f'option framerate {fps}',f'duration {(z-a)/fps:.10f}']
  rows.append(dict(startFrame=a,endFrame=z,eventId=e['id'],scene=e['scene'],type=e['type'],caption=cap,overlay=file.name))
 listing += [f"file '{file.as_posix()}'",f'option framerate {fps}']
 (root/'overlays.ffconcat').write_text('\n'.join(listing)+'\n')
 # Raw source frames are never warped differently in time; actor never changes pose.
 if kind=='reel':graph='[0:v]crop=800:660:100:710,scale=1080:891:flags=lanczos,pad=1080:1920:0:0:color=0x101820[bg];'
 else:graph='[0:v]crop=900:1080:0:0,pad=1920:1080:0:0:color=0x101820[bg];'
 # Source already has native CFR: no redundant fps filter (which trims a tail frame).
 # shortest=1 uses the complete main stream, not concat's extra sentinel image.
 graph+=f'[1:v]format=rgba[ov];[bg][ov]overlay=x=0:y=0:shortest=1:eof_action=repeat:format=auto,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1[v]'
 destination=ROOT/f'downloads/ahangban-ava-static-{kind}.mp4'
 cmd=[FF,'-hide_banner','-y','-filter_complex_threads','1','-threads','1','-i',source,'-f','concat','-safe','0','-i',root/'overlays.ffconcat','-filter_complex',graph,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','21','-maxrate','2500k','-bufsize','5000k','-threads','2','-c:a','copy','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-movflags','+faststart','-map_metadata','-1','-metadata','title=سه آهنگ برای آخر شب | آوا با تصویر ثابت','-metadata','comment=STATIC Ava portrait: no lip sync, head motion, blinks or listening performance. Synthetic female voice06. Existing music-panel motion and exact source AAC preserved. No publication.',destination]
 data=dict(kind=kind,status='READY_TO_RENDER_STATIC_AVA_NOT_ANIMATED',size=list(size),fps=fps,totalFrames=total,sourceVideo=str(source.relative_to(ROOT)),sourceSha256=sha(source),sourceDuration=old['duration'],narrationVoice='voice-06',maleNarrationUsed=False,musicSecondsEach=plan['musicSecondsEach'],actorSourceSha256=sha(b.ACTOR),microphoneSourceSha256=sha(r.MIC),fixedPanelSha256=sha(root/'ava-panel-fixed.png'),actorAnimated=False,headLipEyeListeningMotionGenerated=False,userExplicitlyApprovedNoMotion=False,staticFallbackDisclosedBeforeBuild=True,noExternalUserExecutionRequired=True,audioProcessing='AAC stream copy, no re-encode/retime',audioGenerated=False,publishAuthorized=False,sourceSpeechCaptionCropGuard=True,intervals=rows,command=[str(x) for x in cmd])
 dump(root/'render-plan.json',data);return cmd,data

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=SETTINGS,required=True);p.add_argument('--prepare-only',action='store_true');args=p.parse_args();cmd,d=prepare(args.kind)
 if not args.prepare_only:run(cmd)
 print('STATIC_AVA',args.kind,'PREPARED' if args.prepare_only else 'RENDERED',flush=True)
if __name__=='__main__':main()

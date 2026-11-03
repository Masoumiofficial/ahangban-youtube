"""Full approved-style night playlist, female voice ONLY. No upload/publishing.
Preserve reviewed female performances and approved cover image bytes exactly.
"""
import argparse,hashlib,importlib.util,json,shutil,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EPISODE=HERE.parent;REPO=EPISODE.parents[1]
spec=importlib.util.spec_from_file_location('night_revision02',EPISODE/'revision-02/build_revision.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
b=r.b;FF=r.FF;RATE=48000;WORK=REPO/'rendered/video-010-final-female';AUDIO=HERE/'audio'
ROWS=json.loads((HERE/'dialogue.fa.json').read_text())
COVERS={'youtube':REPO/'downloads/ahangban-night-v2-youtube-thumbnail.jpg','reel':REPO/'downloads/ahangban-night-v2-reel-cover.jpg'}
sha=r.sha;dump=r.dump

class FinalArtwork(r.DepthArtwork):
 def overlay(self,event,variant=0,thumbnail=False):
  im=Image.new('RGBA',self.size);v=self.vertical;r.brand(im,self.kind);right=918 if v else 1800;idx=self.byid.get(event['scene'],-1)
  if idx>=0:
   tr=b.TRACKS[idx]
   r.title(im,tr['title'],right,350 if v else 310,94 if v else 116,maxwidth=800 if v else 1000)
   r.title(im,tr['artist'],right,510 if v else 480,42 if v else 47,'#efc27e',maxwidth=800,depth=2)
   r.title(im,'انتخاب '+str(idx+1).translate(b.g.DIGITS)+' از ۳',right,275 if v else 235,30,'#bdc8cb',maxwidth=800,depth=1)
  else:
   a,z=('انتخاب امشبت؟','اسم آهنگ رو کامنت کن') if event['scene']=='recap' else ('آخر شب…','کدوم آهنگ؟')
   r.title(im,a,right,370 if v else 310,100 if v else 130,maxwidth=800 if v else 1000)
   r.title(im,z,right,530 if v else 495,67 if v else 83,'#efc27e',maxwidth=800 if v else 1000,depth=4)
  # The final is NOT labelled as a demo; the approved visual style remains intact.
  if not v:r.title(im,'رسانهٔ آهنگ‌بان',right,1002,26,'#b8c2c7',maxwidth=800,depth=0)
  b.g.text(ImageDraw.Draw(im),'ahangban.ir',88,1565 if v else 1020,26,'#e7d4ae',anchor='lt')
  return im

def prepare(kind):
 root=WORK/kind;root.mkdir(parents=True,exist_ok=True);media=root/'source-media';media.mkdir(exist_ok=True);norm=root/'normalized';norm.mkdir(exist_ok=True)
 for a in b.MANIFEST['assets']:
  source=b.SOURCE/a['file'];assert sha(source)==a['sha256']
  assert subprocess.check_output(['git','hash-object',str(source)],text=True).strip()==a['gitBlob']
  target=media/a['file']
  if not target.exists():shutil.copy2(source,target)
 rows=[x for x in ROWS if x['id'].startswith('vertical-')==(kind=='reel')];normalized={};speech=[]
 for row in rows:
  assert row['speaker']=='female' and row['voice']=='voice-06'
  source=AUDIO/row['file'];assert sha(source)==row['sha256']
  if row['exactReviewedPerformanceReuse']:assert sha(REPO/row['reviewedSource'])==row['sha256']
  data=r.decode(source);rms=float(np.sqrt(np.mean(data**2)));gain=min(.1/max(rms,1e-9),.8/max(float(abs(data).max()),1e-9));data*=gain
  normalized[row['id']]=data;r.write_wave(norm/(row['id']+'.wav'),data)
  speech.append(dict(row,sourceSha256=sha(source),duration=len(data)/RATE,constantGain=gain))
 events=[];chunks=[];captions=[];cursor=0.
 def append(data,info):
  nonlocal cursor
  duration=len(data)/RATE;e=dict(info,start=cursor,end=cursor+duration,duration=duration,sceneDuration=duration+.28);events.append(e);chunks.extend([data,np.zeros((round(.28*RATE),2),np.float32)]);cursor+=duration+.28
  if e['type']=='speech':captions.extend(b.caption_cues(e,data))
 def talk(id):
  row=next(x for x in rows if x['id']==id);append(normalized[id],dict(row,type='speech'))
 def music(index):
  t=b.TRACKS[index];duration=35 if kind=='youtube' else 12;offset=t['excerptStart'] if kind=='youtube' else t['verticalExcerptStart'];assert offset+duration<=t['sourceDurationSeconds'];out=norm/(t['id']+'.wav')
  r.run(['-ss',offset,'-i',media/t['file'],'-map','0:a:0','-t',duration,'-af',f'loudnorm=I=-18:TP=-2:LRA=10,afade=t=in:d=0.18,afade=t=out:st={duration-.35}:d=0.35','-ar',RATE,'-ac','2','-c:a','pcm_s16le',out])
  data=b.pcm(out);assert abs(len(data)/RATE-duration)<.001
  append(data,dict(type='music',id=t['id'],scene=t['id'],title=t['title'],artist=t['artist'],sourceFile=t['file'],sourceStart=offset,cameraCutsLocal=b.onset_cuts(data,4 if kind=='youtube' else 3)))
 if kind=='youtube':
  talk('hook');talk('intro');music(0);talk('transition');music(1);talk('third');music(2);talk('closing');talk('brand')
 else:
  talk('vertical-hook')
  for index in range(3):music(index)
  talk('vertical-closing')
 r.write_wave(root/'audio.wav',np.concatenate(chunks))
 plan=dict(kind=kind,status='full_female_only_final_for_user_listening',duration=cursor,events=events,captions=captions,ctas=[],narrationGender='female_only',narrationVoice='voice-06',maleNarrationUsed=False,musicSecondsEach=35 if kind=='youtube' else 12,captionTiming='Proportional groups silence-nudged, not word-level forced alignment',cameraTiming='Positive RMS onsets, not certified tempo/beat detection')
 prov=dict(sourceCommit=b.MANIFEST['sourceCommit'],assets=b.MANIFEST['assets'],speech=speech,logoSha256=sha(b.g.LOGO),femaleOnlyAuthorized=True,maleNarrationUsed=False,voicePitchOrSpeedChanged=False,humanRecordingUsed=False,personalCloneUsed=False,approvedCoverSource=str(COVERS[kind].relative_to(REPO)),approvedCoverSha256=sha(COVERS[kind]),visualSourceRevision='revision-02',environmentPlates=[dict(path=str((r.HERE/'assets'/name).relative_to(REPO)),sha256=sha(r.HERE/'assets'/name)) for name in ['depth-night-wide.jpg','depth-night-vertical.jpg']],userSuppliedWebLinks=b.MANIFEST['userSuppliedWebLinks'],pronunciationCorrection=dict(expected='سیاوش قُمیشی',ttsText='سیاوَش قُمیشی',correctedClip='intro',wholeUtteranceRegenerated=True,auralVerificationByAgent=False),copyrightCleared=False,published=False)
 dump(root/'timeline.json',plan);dump(root/'source-provenance.json',prov);print('PREPARED',kind,round(cursor,3),flush=True);return root,plan

def render(kind,stills_only=False):
 root,plan=prepare(kind);layers=root/'layers';layers.mkdir(exist_ok=True);r.foreground(b.SIZES[kind]).save(layers/'near-glass.png')
 b.Artwork=FinalArtwork;b.background=lambda index,k:r.backdrop(k,index).convert('RGB');b.shot_command=r.shot_command
 b.render(root,kind,plan,stills_only)
 # Never recreate the approved thumbnail/cover; copy its exact reviewed bytes.
 shutil.copy2(COVERS[kind],root/'cover.jpg')
 if not stills_only:
  r.run(['-i',root/f'ahangban-night-playlist-{kind}.mp4','-c','copy','-metadata','comment=Full female-only AhangBan night playlist. Voice06; no male narration. Script pronunciation Siyaavash Qomayshi corrected and resynthesized. Approved 2.5D visuals/covers. Final listening pending; no publication or copyright clearance.','-movflags','+faststart',root/f'ahangban-night-final-{kind}.mp4'])
 return plan

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);p.add_argument('--stills-only',action='store_true');args=p.parse_args();render(args.kind,args.stills_only)

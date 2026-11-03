"""Finish the first episode with real recorded Sajad, rewritten Ava and black suit.
No cloned male voice, third-party voice upload or YouTube publication.
Selected speech, source media and intermediate files remain in ignored rendered/.
"""
from pathlib import Path
import argparse,importlib.util,json,hashlib,subprocess,sys
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PREVIOUS=HERE.parent/'003-chavoshi-studio'
sys.path.insert(0,str(PREVIOUS))
spec=importlib.util.spec_from_file_location('studio_renderer',PREVIOUS/'build_video.py')
studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)
FF=studio.FF
SOURCE=REPO/'studio/ahangban-signature/Presenters/Sajad/sajad.m4a'
SOURCE_SHA='acbbb46ebe3202bebb8c3535a8feffb2b5defc5d480cb3c2304d507830a3d6c0'
PRESENTER=studio.STUDIO/'productions/HOSTS-VIEW-002.png'
VIDEO='ahangban-first-video-final.mp4'
# Four long spoken islands in the supplied take, with consonant/breath padding.
# The short initial preface and long inter-take silences are excluded.
# Boundaries are derived from technical silence analysis, not ASR confirmation.
CUTS={'02':(4.707750,10.991458),'10':(14.617292,23.629583),
      '11':(27.990167,35.169021),'06':(40.311458,47.735958)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def extract_user_turn(source,dest,start,end):
 duration=end-start
 studio.run(['-ss',f'{start:.6f}','-i',source,'-t',f'{duration:.6f}',
  '-map_metadata','-1','-vn','-af',f'highpass=f=60,volume=-3dB,afade=t=in:d=0.012,afade=t=out:st={duration-.035:.6f}:d=0.035',
  '-ar',48000,'-ac',1,'-c:a','pcm_s16le',dest])

def prepare_inputs(root,tracks,dialogue):
 assert sha(SOURCE)==SOURCE_SHA,'Unexpected source recording; do not silently substitute a voice'
 media=root/'source-media';audio=root/'audio';media.mkdir(exist_ok=True);audio.mkdir(exist_ok=True)
 provenance={'repository':'Masoumiofficial/ahangban-youtube','revision':studio.PINNED,
  'voiceSelection':{'female':'voice-00 unchanged, seven newly synthesized rewritten turns','male':'Real user-supplied Sajad recording; not a clone or voice-02'},
  'music':[],'speech':[],'recordingSource':str(SOURCE.relative_to(REPO)),
  'recordingSourceSha256':SOURCE_SHA,'recordingCuts':CUTS,
  'cutReview':'Speech islands with padding; needs user aural confirmation, not forced alignment'}
 for track in tracks:
  for key in ('file','cover'):
   name=track[key];path=f'Artist/1-Mohsen-Chavoshi/{name}'
   blob=subprocess.check_output(['git','rev-parse',f'{studio.PINNED}:{path}'],cwd=REPO,text=True).strip()
   dest=media/name
   with dest.open('wb') as f:subprocess.run(['git','cat-file','blob',blob],cwd=REPO,stdout=f,check=True)
   provenance['music'].append({'path':path,'gitBlob':blob,'file':str(dest.relative_to(root)),'sha256':sha(dest),'bytes':dest.stat().st_size})
 for row in dialogue:
  id=row['id'];male=row['speaker']=='male';dest=audio/(id+('.wav' if male else '.mp3'))
  if male:
   start,end=CUTS[id];extract_user_turn(SOURCE,dest,start,end)
   entry={'source':str(SOURCE.relative_to(REPO)),'sourceSha256':SOURCE_SHA,'voice':'user_recording',
          'sourceStart':start,'sourceEnd':end,'processing':'60Hz high-pass, -3dB headroom, 12/35ms edge fades; no pitch/time change'}
  else:
   if not dest.is_file():raise FileNotFoundError(f'Missing new voice-00 speech {dest}; old narration must not be reused for rewritten text')
   entry={'source':str(dest.relative_to(REPO)),'sourceSha256':sha(dest),'voice':'voice-00','generation':'New speech generated for revised script in this session'}
  provenance['speech'].append({'id':id,'speaker':row['speaker'],'file':str(dest.relative_to(root)),'sha256':sha(dest),**entry})
 (root/'source-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 return provenance

def make_thumbnail(root,tracks):
 from PIL import Image,ImageDraw,ImageOps
 im=Image.open(PRESENTER).convert('RGBA')
 for name in ('AHANGBAN-LOGO-GLOW.png','AHANGBAN-LOGO-CORE.png'):
  im=Image.alpha_composite(im,Image.open(studio.STUDIO/'overlays'/name).convert('RGBA'))
 im=im.resize((1280,720),Image.Resampling.LANCZOS)
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 d.rounded_rectangle((25,476,1255,702),radius=22,fill=(9,20,28,245),outline=(133,175,195,220),width=2)
 im=Image.alpha_composite(im,layer);d=ImageDraw.Draw(im)
 studio.text(d,'چاوشی',1214,483,78,'#f4f1ea',True)
 studio.text(d,'از کجا شروع کنیم؟',1214,587,53,'#dec49a',True)
 studio.text(d,'۵ آهنگ برای شروع',555,494,34,'#8ac6e3',True)
 for i,t in enumerate(tracks):
  art=ImageOps.fit(Image.open(root/'source-media'/t['cover']).convert('RGB'),(92,92),method=Image.Resampling.LANCZOS)
  x=51+i*102;im.paste(art,(x,562));ImageDraw.Draw(im).rectangle((x-1,561,x+92,654),outline='#728e9e',width=1)
 im.convert('RGB').save(root/'thumbnail.jpg',quality=95)

def metadata(root,tracks,timeline,provenance):
 studio.package_metadata(root,tracks,timeline,provenance)
 desc=(root/'upload-description.txt').read_text(encoding='utf-8-sig')
 desc=desc.replace('تصویر مجریان با هوش مصنوعی و صدای آن‌ها با گفتار مصنوعی ساخته شده است. تصویر مجریان ثابت است و لب‌خوانی ندارد.',
  'تصویر مجریان با هوش مصنوعی ساخته شده است. صدای آوا مصنوعی است؛ صدای سجاد از ضبط واقعی خودش استفاده می‌کند و کلون نیست. تصویر مجریان ثابت است و لب‌خوانی ندارد.')
 (root/'upload-description.txt').write_text(desc,encoding='utf-8-sig')
 manifest=json.loads((root/'production-manifest.json').read_text())
 manifest.update(edition='First episode completed with real Sajad recording and revised dialogue',
  presenterComposite=str(PRESENTER.relative_to(REPO)),presenterCompositeSha256=sha(PRESENTER),
  dialogueFile=str((HERE/'dialogue.fa.json').relative_to(REPO)),dialogueSha256=sha(HERE/'dialogue.fa.json'),
  maleVoice='Actual user recording, not synthetic, not cloned',femaleVoice='voice-00 unchanged identity; seven newly generated turns',
  userRecordingSha256=SOURCE_SHA,ownVoiceCloned=False,thirdPartyVoiceUpload=False,
  performerWardrobe='Sajad black suit / black shirt, same approved frontal studio',
  captionAndTakeReview='Timing from text/pauses. Male takes segmented from recorded speech islands; no ASR or aural phonetic confirmation.')
 (root/'production-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def command(root,total):
 cmd=studio.render_command(root,total)
 cmd[-1]=str(root/VIDEO)
 for i,item in enumerate(cmd):
  if isinstance(item,str) and item.startswith('comment='):
   cmd[i]='comment=Actual user-recorded Sajad and synthetic Ava; static AI presenter images, no lip sync. Five user-supplied third-party music excerpts; rights not independently verified. Not published to YouTube.'
 return cmd

def main():
 p=argparse.ArgumentParser();p.add_argument('--media-root',type=Path,default=REPO/'rendered/video-004-own-voice')
 p.add_argument('--prepare-only',action='store_true');p.add_argument('--render-only',action='store_true');args=p.parse_args()
 root=args.media_root.resolve();root.mkdir(parents=True,exist_ok=True)
 if args.render_only:timeline=json.loads((root/'timeline.json').read_text())
 else:
  dialogue=json.loads((HERE/'dialogue.fa.json').read_text());tracks=json.loads((PREVIOUS/'tracks.json').read_text())
  provenance=prepare_inputs(root,tracks,dialogue)
  timeline=studio.assemble(root,tracks,dialogue)
  studio.make_cards(root,tracks,timeline,presenter_image=PRESENTER)
  studio.subtitles(root,timeline)
  # Avoid RTL quote-order ambiguity in the music cutaway subtitle.
  ass=root/'subtitles.ass';s=ass.read_text()
  for t in tracks:s=s.replace(f'نمونهٔ شنیداری از «{t["title"]}»',f'نمونهٔ شنیداری: {t["title"]}')
  ass.write_text(s)
  make_thumbnail(root,tracks)
  metadata(root,tracks,timeline,provenance)
  print(f'PREPARED {timeline["duration"]:.2f}s: real Sajad recording, revised Ava, black suit.',flush=True)
 cmd=command(root,timeline['duration'])
 (root/'render-command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2)+'\n')
 if not args.prepare_only:
  studio.render_frames(root,cmd,timeline)
  manifest=json.loads((root/'production-manifest.json').read_text())
  manifest.update(status='rendered_pending_QA',video=VIDEO,videoSha256=sha(root/VIDEO))
  (root/'production-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  print('DONE',root/VIDEO,flush=True)
if __name__=='__main__':main()

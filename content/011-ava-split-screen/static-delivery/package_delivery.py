"""Publish local file links/metadata ONLY after both independent QA reports PASS; no upload."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];WORK=ROOT/'rendered/ava-static-exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 outputs={}
 for kind in ('youtube','reel'):
  qa=json.loads((WORK/kind/'qa-report.json').read_text());assert qa['status']=='PASS' and sha(ROOT/qa['file'])==qa['sha256']
  target=HERE/'delivery'/kind;target.mkdir(parents=True,exist_ok=True)
  shutil.copy2(WORK/kind/'qa-report.json',target/'qa-report.json')
  plan=json.loads((WORK/kind/'render-plan.json').read_text());plan['status']='RENDERED_COMPLETE_STATIC_AVA_QA_PASSED'
  (target/'render-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
  original=ROOT/f'content/010-night-playlist/final-female/delivery/{kind}'
  for name in ('subtitles.fa.srt',('chapters.txt' if kind=='youtube' else 'instagram-caption.txt')):
   shutil.copy2(original/name,target/name)
  title='سه آهنگ برای آخر شب | آوا با تصویر ثابت'
  tracks=json.loads((ROOT/'content/010-night-playlist/tracks.json').read_text())
  description='سه آهنگ برای آخر شب، همراه تصویر ثابت آوا و گویندگی مصنوعی زن.\n\nاین نسخه لب‌خوانی، حرکت سر/پلک یا اجرای گوش‌دادن ندارد؛ فقط بخش موسیقی دارای حرکت تصویری است.\n\n'+'\n'.join(f"{t['title']} — {t['artist']}\n{t['url']}" for t in tracks)+'\n\nahangban.ir\nهیچ تضمین رفع کپی‌رایت/ContentID وجود ندارد. انتشار خودکار انجام نشده است.\n'
  (target/'upload-title.txt').write_text(title+'\n');(target/'upload-description.txt').write_text(description)
  outputs[kind]=qa
 result=dict(status='COMPLETE_PLAYABLE_FILES_STATIC_AVA_NOT_ANIMATED_HOST',outputs=outputs,actorAnimated=False,requestedNaturalMotionDelivered=False,staticFallbackDisclosedBeforeBuild=True,userExplicitlyChoseStaticFallback=False,externalExecutionRequiredFromUser=False,newTTSGenerated=False,voice='voice-06',publishAuthorized=False,postedToYouTubeOrInstagram=False)
 (HERE/'delivery/manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

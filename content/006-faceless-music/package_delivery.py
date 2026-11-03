"""Copy QA-passed final videos and requested companions; no raw audio exports."""
import json,shutil
from pathlib import Path
import build_video as build

HERE=build.HERE

def clock(t):
 total=round(t*1000);h,total=divmod(total,3600000);m,total=divmod(total,60000);s,ms=divmod(total,1000)
 return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def main():
 tracks=json.loads((HERE.parent/'003-chavoshi-studio/tracks.json').read_text())
 trackmap={t['id']:t for t in tracks};manifest={'edition':'Faceless music editorial: YouTube full episode + native Instagram Reel',
  'voices':{'male':'Real existing user-recorded Sajad, no clone','female':'Existing approved voice-00 Ava, no new generation'},
  'presenterImagesUsed':False,'studioImagesUsed':False,'newSpeechGenerated':False,'thirdPartyUpload':False,
  'youtubePublished':False,'instagramPublished':False,'copyrightCleared':False,'outputs':{}}
 for kind in ('youtube','reel'):
  root=build.REPO/f'rendered/video-006-faceless/{kind}'
  qa=json.loads((root/'qa-report.json').read_text());plan=json.loads((root/'timeline.json').read_text())
  assert qa['status'].startswith('technical_QA_passed')
  video=root/f'ahangban-faceless-{kind}.mp4';assert build.sha(video)==qa['sha256']
  dst=HERE/'delivery'/kind;dst.mkdir(parents=True,exist_ok=True)
  for name in ('timeline.json','source-provenance.json','qa-report.json'):shutil.copy2(root/name,dst/name)
  target=build.REPO/'downloads'/video.name;shutil.copy2(video,target)
  image=root/('thumbnail.jpg' if kind=='youtube' else 'cover.jpg')
  cover_name='ahangban-faceless-youtube-thumbnail.jpg' if kind=='youtube' else 'ahangban-faceless-reel-cover.jpg'
  shutil.copy2(image,build.REPO/'downloads'/cover_name)
  srt='\n\n'.join(f'{i+1}\n{clock(c["start"])} --> {clock(c["end"])}\n{c["text"]}' for i,c in enumerate(plan['captions']))+'\n'
  (dst/'subtitles.fa.srt').write_text(srt)
  (dst/'upload-title.txt').write_text('چاوشی را از کجا شروع کنیم؟ | ۵ آهنگ، پنج حال‌وهوا\n')
  manifest['outputs'][kind]={'video':str(target.relative_to(build.REPO)),'sha256':qa['sha256'],'bytes':qa['bytes'],
   'duration':qa['duration'],'resolution':qa['resolution'],'fps':qa['fps'],'cover':'downloads/'+cover_name,
   'coverSha256':build.sha(image),'captionFile':str((dst/'subtitles.fa.srt').relative_to(build.REPO)),
   'status':'rendered_technical_QA_passed_pending_user_listening_review'}
  if kind=='youtube':
   chapters=[(0,'شروع؛ پنج انتخاب برای شنیدن چاوشی')];seen=set()
   for e in plan['events']:
    scene=e['visualScene']
    if scene in trackmap and scene not in seen:chapters.append((e['start'],trackmap[scene]['title']));seen.add(scene)
   chapters.append((next(e['start'] for e in plan['events'] if e['visualScene']=='recap'),'انتخاب تو کدام است؟'))
   chapter_text='\n'.join(f'{int(t)//60:02d}:{int(t)%60:02d} {title}' for t,title in chapters)
   (dst/'chapters.txt').write_text(chapter_text+'\n')
   pages='\n'.join(t['title']+' — '+t['pageUrl'] for t in tracks if t.get('pageUrl'))
   description=f'''چاوشی را از کدام آهنگ شروع کنیم؟ پنج پیشنهاد آهنگ‌بان برای پنج حال‌وهوا.
این فهرست انتخاب تحریریه است، نه رتبه‌بندی آماری یا ادعای «بهترین» آهنگ‌ها.
در این قسمت از هر قطعه ۱۲ ثانیه می‌شنویم؛ کدام انتخاب به سلیقهٔ تو نزدیک‌تر است؟ اسمش را کامنت کن.

{chapter_text}

آهنگ‌ها:
کجایی — محسن چاوشی و سینا سرلک
سنگ صبور — محسن چاوشی
امیر بی‌گزند — محسن چاوشی
برقص آ — محسن چاوشی
بیست هزار آرزو — محسن چاوشی

{pages}

آهنگ‌بان: https://ahangban.ir
یوتیوب آهنگ‌بان: https://www.youtube.com/@AhangBan

گفتار سجاد از ضبط واقعی خود اوست؛ صدای آوا گفتار مصنوعیِ همان صدای منتخب است. تصویر مجری نمایش داده نمی‌شود. تصویرهای استفاده‌شده کاورهای اصلیِ ارائه‌شده‌اند؛ ممکن است روی خود کاورها چهرهٔ هنرمند/بازیگر دیده شود.
حقوق موسیقی و تصاویر متعلق به صاحبان آثار است. ذکر نام یا کوتاه‌بودن نمونه، مجوز استفاده یا تضمین رفع Content ID نیست؛ وضعیت حقوق پیش از انتشار باید بررسی شود.

#محسن_چاوشی #معرفی_موسیقی #آهنگبان
'''
   (dst/'upload-description.txt').write_text(description)
  else:
   caption='''چاوشی رو با کدوم آهنگ شروع می‌کنی؟ 🎧
پنج انتخاب برای پنج حال‌وهوا؛ نه رتبه‌بندی بهترین‌ها.

۱. کجایی — محسن چاوشی و سینا سرلک
۲. سنگ صبور — محسن چاوشی
۳. امیر بی‌گزند — محسن چاوشی
۴. برقص آ — محسن چاوشی
۵. بیست هزار آرزو — محسن چاوشی

انتخابت رو کامنت کن 👇
ahangban.ir
یوتیوب آهنگ‌بان: https://www.youtube.com/@AhangBan

موسیقی و تصاویر کاور متعلق به صاحبان آثارند. نام‌بردن، جایگزین مجوز استفاده نیست.
#محسن_چاوشی #معرفی_موسیقی #آهنگبان #موسیقی_ایرانی
'''
   (dst/'instagram-caption.txt').write_text(caption)
 (HERE/'delivery/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

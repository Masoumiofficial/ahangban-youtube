"""Package only hash-verified, technically checked exports. Never publish."""
import json,shutil
from pathlib import Path
import build_video as b

def clock(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def main():
 title='پنج آهنگ محسن چاوشی؛ انتخاب تو کدام است؟'
 manifest={'edition':'007 cosmic faceless / freshly selected synthetic narration','voices':{'female':'voice-05','male':'voice-04'},
  'allNarrationSynthetic':True,'humanRecordingUsed':False,'personalCloneUsed':False,'presenterImagesUsed':False,
  'environmentVisuals':'AI-generated 2D environment plates, animated locally; not a real location or a 3D performance',
  'copyrightCleared':False,'youtubePublished':False,'instagramPublished':False,'outputs':{}}
 for kind in ('youtube','reel'):
  root=b.REPO/f'rendered/video-007-cosmic/{kind}';qa=json.loads((root/'qa-report.json').read_text());plan=json.loads((root/'timeline.json').read_text())
  assert qa['status'].startswith('technical_QA_passed');video=root/qa['video'];assert b.sha(video)==qa['sha256']
  target=b.REPO/'downloads'/video.name;shutil.copy2(video,target)
  cover='ahangban-cosmic-'+kind+('-thumbnail.jpg' if kind=='youtube' else '-cover.jpg');shutil.copy2(root/'cover.jpg',b.REPO/'downloads'/cover)
  dest=b.HERE/'delivery'/kind;dest.mkdir(parents=True,exist_ok=True)
  for name in ('timeline.json','source-provenance.json','qa-report.json'):shutil.copy2(root/name,dest/name)
  (dest/'subtitles.fa.srt').write_text('\n\n'.join(f'{i+1}\n{clock(c["start"])} --> {clock(c["end"])}\n{c["text"]}' for i,c in enumerate(plan['captions']))+'\n')
  (dest/'upload-title.txt').write_text(title+'\n')
  manifest['outputs'][kind]={'video':str(target.relative_to(b.REPO)),'sha256':qa['sha256'],'bytes':qa['bytes'],
   'duration':qa['duration'],'resolution':qa['resolution'],'fps':qa['fps'],'cover':'downloads/'+cover,
   'coverSha256':b.sha(root/'cover.jpg'),'musicSamples':5,'musicSecondsEach':plan['musicSecondsEach'],
   'speechSourceIds':[e['id'] for e in plan['events'] if e['type']=='speech'],'status':'technical_QA_passed_pending_user_listening'}
  songs='\n'.join(f'{i+1}. {t["title"]} — {t["artist"]}' for i,t in enumerate(b.TRACKS))
  if kind=='youtube':
   # The seven-second hook and first song intro share chapter zero; never create <10s chapters.
   chapters=[(0,'پنج انتخاب؛ کجایی')]
   for e in plan['events']:
    if e['type']=='speech' and e['scene'] in [t['id'] for t in b.TRACKS[1:]]:
     chapters.append((int(e['start']),next(t['title'] for t in b.TRACKS if t['id']==e['scene'])))
   chapters.append((int(next(e['start'] for e in plan['events'] if e['scene']=='recap')),'انتخاب تو کدام است؟'))
   boundaries=[p[0] for p in chapters]+[plan['duration']];assert all(y-x>=10 for x,y in zip(boundaries,boundaries[1:]))
   chapter_text='\n'.join(f'{t//60:02d}:{t%60:02d} {label}' for t,label in chapters);(dest/'chapters.txt').write_text(chapter_text+'\n')
   description=f'''پنج آهنگ محسن چاوشی؛ از هر قطعه ۲۰ ثانیه بشنو و انتخاب خودت را پیدا کن.
کجایی، سنگ صبور، امیر بی‌گزند، برقص آ یا بیست هزار آرزو؟ نام انتخابت را کامنت کن.
رسانهٔ آهنگ‌بان: https://ahangban.ir

{chapter_text}

{songs}

این فهرست انتخاب تحریریه است، نه رتبه‌بندی آماری یا ادعای ترند امروز.
اگر این مدل معرفی موسیقی را دوست داری، لایک کن و برای قسمت بعد کانال را سابسکرایب کن.
https://www.youtube.com/@AhangBan

گفتار معرفی تماماً با دو صدای مصنوعیِ انتخاب‌شده ساخته شده است؛ ضبط شخصی یا کلون صدا به کار نرفته. محیط‌های سوررئال با هوش مصنوعی تصویرسازی و به‌صورت دوبعدی متحرک شده‌اند؛ بازنمایی اجرای واقعی هنرمند نیستند. نمونه‌های موسیقی و کاورها همان فایل‌های اصلیِ ارائه‌شده‌اند و ممکن است روی کاورها چهرهٔ هنرمند/بازیگر باشد.
حقوق موسیقی و کاور متعلق به صاحبان آثار است. کوتاهی نمونه یا ذکر نام مجوز استفاده و تضمین رفع Content ID نیست؛ پیش از انتشار وضعیت حقوق بررسی شود.

#محسن_چاوشی #معرفی_موسیقی #آهنگبان
'''
   (dest/'upload-description.txt').write_text(description)
  else:
   caption=f'''پنج آهنگ از چاوشی؛ فقط یکی رو انتخاب کن 🎧
آخرش انتخابت عوض شد؟ اسم آهنگ رو کامنت کن 👇

{songs}

این پنج انتخاب تحریریه‌ست، نه رتبه‌بندی بهترین‌ها یا ترند امروز.
اگه کسی رو یاد این آهنگ‌ها می‌ندازن، براش بفرست؛ برای دوباره شنیدن هم ذخیره کن.
رسانهٔ آهنگ‌بان | ahangban.ir

گفتار مصنوعی و محیط‌های تصویرسازی‌شده با هوش مصنوعی؛ موسیقی و کاورهای اصلی متعلق به صاحبان آثارند. نام‌بردن یا کوتاهی نمونه جایگزین مجوز نیست.
#محسن_چاوشی #معرفی_موسیقی #آهنگبان #موسیقی_ایرانی
'''
   (dest/'instagram-caption.txt').write_text(caption)
 (b.HERE/'delivery/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

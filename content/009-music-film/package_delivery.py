"""Copy only QA-passed finals, metadata, captions, edit decisions; never publish."""
import json,shutil
import build_video as b

def clock(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def main():
 manifest=dict(edition='009 music-first cinematic film',voices={'female':'voice-06','male':'voice-07'},approved008SamplePerformancesReused=True,
  voicePitchOrSpeedChanged=False,allNarrationSynthetic=True,humanRecordingUsed=False,personalCloneUsed=False,presenterImagesUsed=False,
  copyrightCleared=False,youtubePublished=False,instagramPublished=False,finalUserListeningPending=True,outputs={})
 title='چرا بعضی آهنگ‌های چاوشی تکراری نمی‌شوند؟'
 songs='\n'.join(f'{i+1}. {t["title"]} — {t["artist"]}' for i,t in enumerate(b.TRACKS))
 for kind in ('youtube','reel'):
  root=b.REPO/f'rendered/video-009-music-film/{kind}';qa=json.loads((root/'qa-report.json').read_text());plan=json.loads((root/'timeline.json').read_text())
  assert qa['status'].startswith('technical_QA_passed');video=root/qa['video'];assert b.sha(video)==qa['sha256']
  target=b.REPO/'downloads'/video.name;shutil.copy2(video,target)
  cover='ahangban-music-film-'+kind+('-thumbnail.jpg' if kind=='youtube' else '-cover.jpg');shutil.copy2(root/'cover.jpg',b.REPO/'downloads'/cover)
  dest=b.HERE/'delivery'/kind;dest.mkdir(parents=True,exist_ok=True)
  for name in ('timeline.json','source-provenance.json','qa-report.json','shots.json'):shutil.copy2(root/name,dest/name)
  (dest/'upload-title.txt').write_text(title+'\n')
  (dest/'subtitles.fa.srt').write_text('\n\n'.join(f'{i+1}\n{clock(c["start"])} --> {clock(c["end"])}\n{c["text"]}' for i,c in enumerate(plan['captions']))+'\n')
  manifest['outputs'][kind]=dict(video=str(target.relative_to(b.REPO)),sha256=qa['sha256'],bytes=qa['bytes'],duration=qa['duration'],resolution=qa['resolution'],fps=qa['fps'],cover='downloads/'+cover,coverSha256=b.sha(root/'cover.jpg'),musicSecondsEach=plan['musicSecondsEach'],musicTotalSeconds=qa['musicTotalSeconds'],musicCameraShots=qa['musicCameraShots'])
  if kind=='youtube':
   chapters=[(0,'چرا باز از اول؟')];seen=set()
   for e in plan['events']:
    if e['scene'] in [t['id'] for t in b.TRACKS] and e['scene'] not in seen:
     chapters.append((int(e['start']),next(t['title'] for t in b.TRACKS if t['id']==e['scene'])));seen.add(e['scene'])
   chapters.append((int(next(e['start'] for e in plan['events'] if e['scene']=='recap')),'کدام را دوباره می‌شنوی؟'))
   boundaries=[x[0] for x in chapters]+[plan['duration']];assert all(z-a>=10 for a,z in zip(boundaries,boundaries[1:]))
   text='\n'.join(f'{t//60:02d}:{t%60:02d} {s}' for t,s in chapters);(dest/'chapters.txt').write_text(text+'\n')
   description=f'''چرا بعضی آهنگ‌های محسن چاوشی را بارها می‌شنویم؟ صدا، کلام یا خاطره؟
پنج قطعه، هر کدام ۳۰ ثانیه؛ کجایی، سنگ صبور، امیر بی‌گزند، برقص آ و بیست هزار آرزو.
رسانهٔ آهنگ‌بان: https://ahangban.ir

{text}

{songs}

این‌ها پیشنهاد تحریریه‌اند، نه رتبه‌بندی آماری یا ادعای ترند امروز. این برنامه پاسخ علمی دربارهٔ حافظه نمی‌دهد؛ دعوتی است به شنیدن و مقایسهٔ سلیقهٔ خودت.
کدام قطعه را دوباره پخش می‌کنی؟ اسمش را کامنت کن. اگر این مدل معرفی را دوست داری، لایک کن و برای قسمت بعد سابسکرایب کن.
https://www.youtube.com/@AhangBan

گفتار معرفی با صداهای مصنوعیِ تأییدشده در نمونهٔ شنیداری ساخته شده؛ ضبط شخصی، کلون، تغییر سرعت یا زیر و بم استفاده نشده است. فضاهای سینمایی با هوش مصنوعی تصویرسازی و به‌صورت دوبعدی متحرک شده‌اند؛ فیلم اجرای واقعی هنرمند نیستند. کاورها و موسیقی همان منابع اصلی ارائه‌شده‌اند.
حقوق موسیقی و کاور متعلق به صاحبان آثار است. ذکر نام و کوتاهی نمونه جایگزین مجوز نیست و هیچ تضمینی برای رفع Content ID وجود ندارد.

#محسن_چاوشی #معرفی_موسیقی #آهنگبان
'''
   (dest/'upload-description.txt').write_text(description)
  else:
   (dest/'instagram-caption.txt').write_text(f'''چرا بعضی آهنگا رو هی از اول پخش می‌کنیم؟ 🎧
یه صداست، یه جمله‌ست، یا یه خاطره؟

{songs}

از هر آهنگ ۱۲ ثانیه بشنو؛ آخرش بگو کدوم رو دوباره پخش می‌کنی 👇
اگه کسی رو یادت انداخت، براش بفرست. برای دوباره شنیدن هم ذخیره کن.
رسانهٔ آهنگ‌بان | ahangban.ir

پیشنهاد تحریریه، نه رتبه‌بندی بهترین‌ها یا ترند امروز. گفتار مصنوعی و تصویرسازی هوش مصنوعی؛ موسیقی و کاورهای اصلی متعلق به صاحبان آثارند. ذکر نام یا کوتاهی نمونه مجوز نیست.
#محسن_چاوشی #معرفی_موسیقی #آهنگبان #موسیقی_ایرانی
''')
 (b.HERE/'delivery/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

"""Package only QA-passed single-female finals. Never upload or alter 009 job."""
import json,shutil
import build_final as f

def clock(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000);return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def main():
 m=dict(status='full_female_only_final_files_delivered',title='سه آهنگ برای وقتی که شب تموم نمی‌شه',femaleOnlyAuthorizedByUser=True,visualStyleApprovedByUser=True,coversApprovedByUser=True,narrationVoice='voice-06',maleNarrationUsed=False,exactReviewedFemalePerformancesReused=2,voiceSpeedOrPitchChanged=False,humanRecordingUsed=False,personalCloneUsed=False,finalUserListeningPending=True,copyrightCleared=False,publishAuthorized=False,youtubePublished=False,instagramPublished=False,outputs={})
 songs='\n'.join(f'{i+1}. {t["title"]} — {t["artist"]}\n{t["url"]}' for i,t in enumerate(f.b.TRACKS))
 for kind in ('youtube','reel'):
  root=f.WORK/kind;q=json.loads((root/'qa-report.json').read_text());plan=json.loads((root/'timeline.json').read_text());assert q['status']=='technical_final_QA_passed_pending_final_user_listening'
  video=root/q['video'];assert f.sha(video)==q['sha256'];target=f.REPO/'downloads'/video.name;shutil.copy2(video,target)
  cover='ahangban-night-final-'+kind+('-thumbnail.jpg' if kind=='youtube' else '-cover.jpg');coverfile=f.REPO/'downloads'/cover;shutil.copy2(f.COVERS[kind],coverfile);assert f.sha(coverfile)==f.sha(f.COVERS[kind])
  dest=f.HERE/'delivery'/kind;dest.mkdir(parents=True,exist_ok=True)
  for name in ['timeline.json','source-provenance.json','qa-report.json','shots.json']:shutil.copy2(root/name,dest/name)
  (dest/'subtitles.fa.srt').write_text('\n\n'.join(f'{i+1}\n{clock(c["start"])} --> {clock(c["end"])}\n{c["text"]}' for i,c in enumerate(plan['captions']))+'\n')
  (dest/'upload-title.txt').write_text(m['title']+'\n')
  m['outputs'][kind]=dict(video=str(target.relative_to(f.REPO)),sha256=q['sha256'],bytes=q['bytes'],duration=q['duration'],resolution=q['resolution'],fps=q['fps'],cover=str(coverfile.relative_to(f.REPO)),coverSha256=f.sha(coverfile),coverReusedExactlyFrom=str(f.COVERS[kind].relative_to(f.REPO)),musicSecondsEach=q['musicSecondsEach'],musicTotalSeconds=q['musicTotalSeconds'])
  if kind=='youtube':
   chapters=[(0,'سه انتخاب برای آخر شب')]+[(int(e['start']),e['title']) for e in plan['events'] if e['type']=='music'];recap=int(next(e['start'] for e in plan['events'] if e['scene']=='recap'))
   if plan['duration']-recap>=10:chapters.append((recap,'انتخاب امشبت کدام است؟'))
   times=[t for t,_ in chapters]+[plan['duration']];assert all(z-a>=10 for a,z in zip(times,times[1:])),times
   text='\n'.join(f'{t//60:02d}:{t%60:02d} {s}' for t,s in chapters);(dest/'chapters.txt').write_text(text+'\n')
   (dest/'upload-description.txt').write_text(f'''سه آهنگ برای وقتی که شب تموم نمی‌شه؛ سه خواننده، سه انتخاب برای یک پلی‌لیست شبانه.
از هر انتخاب ۳۵ ثانیه می‌شنویم؛ با معرفی کوتاه و تک‌گویندهٔ زن، بدون گفتار روی موسیقی.
رسانهٔ آهنگ‌بان: https://ahangban.ir

{text}

آهنگ‌ها و لینک‌های معرفی‌شده توسط کاربر:
{songs}

تو برای آخر شب کدام را می‌گذاری؟ اسم آهنگ را کامنت کن؛ پیشنهاد بیرون این فهرست هم بنویس.
https://www.youtube.com/@AhangBan

این انتخاب تحریریه است، نه رتبه‌بندی آماری یا ترند امروز و نه ادعای علمی/درمانی دربارهٔ خاطره و خواب.
معرفی‌ها با صدای مصنوعی زن ساخته شده‌اند؛ تمام گویندگی مرد حذف شده است (خوانندگی قطعات اصلی تغییری نکرده). ضبط شخصی، کلون یا تغییر سرعت و زیر و بم گفتار استفاده نشده است. محیط‌ها تصویرسازی‌شده با هوش مصنوعی و کامپوزیت عمق‌دار ۲٫۵بعدی‌اند، نه صحنهٔ حجمی واقعی یا فیلم اجرای هنرمندان. کاورها و موسیقی از فایل‌های ارسالی کاربرند و لوگوی اصلی بازطراحی نشده است.
انتخاب برش‌ها فنی و سیگنال‌محور است؛ تشخیص شعر یا ترجیع‌بند ادعا نمی‌شود. حقوق موسیقی و کاور متعلق به صاحبان آثار است؛ کوتاهی نمونه و ذکر منبع جای مجوز نیست و رفع Content ID تضمین نمی‌شود.

#سیاوش_قمیشی #داریوش #فرامرز_اصلانی #پلی_لیست_شبانه #آهنگبان
''')
  else:
   (dest/'instagram-caption.txt').write_text(f'''آخر شب، کدوم آهنگ رو دوباره پخش می‌کنی؟ 🌙
سه انتخاب، از هر کدوم ۱۲ ثانیه؛ اسم انتخابت رو کامنت کن.

{songs}

رسانهٔ آهنگ‌بان | ahangban.ir
گویندگی مصنوعی زن و فضاهای تصویرسازی‌شده با کامپوزیت ۲٫۵بعدی؛ موسیقی و کاورها همان فایل‌های ارسالی‌اند. پیشنهاد تحریریه، نه رتبه‌بندی یا ترند امروز؛ ذکر منبع و کوتاهی نمونه تضمین مجوز یا رفع Content ID نیست.
#پلی_لیست_شبانه #سیاوش_قمیشی #داریوش #فرامرز_اصلانی #آهنگبان
''')
 # Optional isolated complete name-introduction utterance, not a word splice.
 pronunciation=f.REPO/'downloads/ahangban-night-final-name-intro.mp3';shutil.copy2(f.AUDIO/'intro.mp3',pronunciation);m['nameIntroductionAudio']=dict(file=str(pronunciation.relative_to(f.REPO)),sha256=f.sha(pronunciation),ttsName='سیاوَش قُمیشی',aurallyVerifiedByAgent=False)
 f.dump(f.HERE/'delivery/manifest.json',m);print(json.dumps(m,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

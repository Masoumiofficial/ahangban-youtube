"""Package independently QA-passed finals, real chapters and user-supplied links.
This script copies local files ONLY. It never publishes or changes the upload job.
"""
import json,shutil
import build_video as b

def clock(t):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def main():
    manifest=dict(edition='010 night playlist',title='سه آهنگ برای وقتی که شب تموم نمی‌شه',voices={'female':'voice-06','male':'voice-07'},freshSpeechClips=8,voicePitchOrSpeedChanged=False,allNarrationSynthetic=True,humanRecordingUsed=False,personalCloneUsed=False,presenterImagesUsed=False,copyrightCleared=False,publishAuthorized=False,youtubePublished=False,instagramPublished=False,finalUserListeningPending=True,outputs={})
    songs='\n'.join(f'{i+1}. {t["title"]} — {t["artist"]}\n{t["url"]}' for i,t in enumerate(b.TRACKS))
    for kind in ('youtube','reel'):
        root=b.REPO/f'rendered/video-010-night-playlist/{kind}'
        qa=json.loads((root/'qa-report.json').read_text());plan=json.loads((root/'timeline.json').read_text())
        assert qa['status']=='technical_QA_passed_pending_final_user_listening'
        video=root/qa['video'];assert b.sha(video)==qa['sha256']
        target=b.REPO/'downloads'/video.name;shutil.copy2(video,target)
        cover='ahangban-night-playlist-'+kind+('-thumbnail.jpg' if kind=='youtube' else '-cover.jpg')
        shutil.copy2(root/'cover.jpg',b.REPO/'downloads'/cover)
        dest=b.HERE/'delivery'/kind;dest.mkdir(parents=True,exist_ok=True)
        for name in ('timeline.json','source-provenance.json','qa-report.json','shots.json'):shutil.copy2(root/name,dest/name)
        (dest/'subtitles.fa.srt').write_text('\n\n'.join(f'{i+1}\n{clock(c["start"])} --> {clock(c["end"])}\n{c["text"]}' for i,c in enumerate(plan['captions']))+'\n')
        (dest/'upload-title.txt').write_text(manifest['title']+'\n')
        manifest['outputs'][kind]=dict(video=str(target.relative_to(b.REPO)),sha256=qa['sha256'],bytes=qa['bytes'],duration=qa['duration'],resolution=qa['resolution'],fps=qa['fps'],cover='downloads/'+cover,coverSha256=b.sha(root/'cover.jpg'),musicSecondsEach=plan['musicSecondsEach'],musicTotalSeconds=qa['musicTotalSeconds'],musicCameraShots=qa['musicCameraShots'])
        if kind=='youtube':
            chapters=[(0,'سه انتخاب برای آخر شب')]+[(int(e['start']),e['title']) for e in plan['events'] if e['type']=='music']+[(int(next(e['start'] for e in plan['events'] if e['scene']=='recap')),'انتخاب امشبت کدام است؟')]
            boundaries=[t for t,_ in chapters]+[plan['duration']]
            assert all(z-a>=10 for a,z in zip(boundaries,boundaries[1:]))
            text='\n'.join(f'{t//60:02d}:{t%60:02d} {title}' for t,title in chapters)
            (dest/'chapters.txt').write_text(text+'\n')
            (dest/'upload-description.txt').write_text(f'''سه آهنگ برای وقتی که شب تموم نمی‌شه؛ سه خواننده، سه انتخاب برای یک پلی‌لیست شبانه.
از هر انتخاب ۳۵ ثانیه می‌شنویم؛ با معرفی‌های کوتاه، بدون گفتار روی موسیقی.
رسانهٔ آهنگ‌بان: https://ahangban.ir

{text}

آهنگ‌ها و لینک صفحات معرفی‌شده توسط آهنگ‌بان:
{songs}

کدام آهنگ بیشتر به حال امشبت می‌خورد؟ اسمش را کامنت کن؛ انتخاب بیرون این فهرست هم پذیرفته است.
https://www.youtube.com/@AhangBan

این انتخاب تحریریه است؛ نه رتبه‌بندی آماری، ترند امروز، ادعای درمان یا نتیجهٔ علمی دربارهٔ حافظه.
گفتار با صداهای مصنوعی ساخته شده است؛ ضبط شخصی، کلون یا تغییر سرعت و زیر و بم گفتار به کار نرفته است. فضاهای شبانه تصویرسازی هوش مصنوعی‌اند و به‌صورت دوبعدی متحرک شده‌اند، نه فیلم اجرای واقعی هنرمندان. موسیقی و کاورها از فایل‌های ارائه‌شدهٔ کاربر آمده‌اند. برش‌ها با معیار فنی سیگنال انتخاب شده‌اند، نه تشخیص خودکار شعر یا بخش ترجیع‌بند.
حقوق موسیقی و کاور متعلق به صاحبان آثار است. کوتاهی نمونه یا ذکر نام جای مجوز را نمی‌گیرد؛ رفع Content ID یا امکان انتشار عمومی تضمین نشده است.

#سیاوش_قمیشی #داریوش #فرامرز_اصلانی #پلی_لیست_شبانه #آهنگبان
''')
        else:
            (dest/'instagram-caption.txt').write_text(f'''وقتی خواب نمیاد، کدوم آهنگ رو دوباره پخش می‌کنی؟ 🌙
از هر انتخاب ۱۲ ثانیه بشنو؛ آخرش اسم انتخاب امشبت رو کامنت کن.

{songs}

رسانهٔ آهنگ‌بان | ahangban.ir
انتخاب تحریریه، نه رتبه‌بندی رسمی یا ترند امروز. گفتار مصنوعی و محیط‌های دوبعدیِ تصویرسازی‌شده با هوش مصنوعی؛ فایل‌های موسیقی و کاور ارائه‌شده توسط کاربر. کوتاهی نمونه و ذکر منبع تضمین مجوز یا رفع Content ID نیست.
#پلی_لیست_شبانه #سیاوش_قمیشی #داریوش #فرامرز_اصلانی #آهنگبان
''')
    (b.HERE/'delivery/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

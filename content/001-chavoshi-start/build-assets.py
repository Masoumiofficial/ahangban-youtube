"""Optional: rebuild ready-to-use PNGs. These are original typeset graphics, not audio waveforms.
python -m pip install -r asset-requirements.txt
python build-assets.py
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
BG, PANEL, LINE = '#101713', '#1c2820', '#334838'
GREEN, WHITE, MUTED = '#bbef94', '#f1f4ed', '#9cae9d'
FONT = ROOT / 'fonts'

def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ('Vazirmatn-Bold.ttf' if bold else 'Vazirmatn-Regular.ttf')), size)

def persian(draw, text, x, y, size, color=WHITE, bold=False, anchor='rt'):
    visual = get_display(arabic_reshaper.reshape(text))
    draw.text((x, y), visual, font=font(size, bold), fill=color, anchor=anchor)

def latin(draw, text, x, y, size=20, color=MUTED):
    draw.text((x,y),text,font=font(size),fill=color)

def canvas(w, h):
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    # Original geometric decoration. No artist photo, artwork, or song audio is embedded.
    for i in range(11):
        x = -w*.15 + i*w*.15
        d.line((x, h, x+w*.4, 0), fill='#18231b', width=1)
    d.rounded_rectangle((28,28,w-28,h-28),radius=28,outline=LINE,width=2)
    return im, d

def save(im, name):
    im.save(OUT/name, optimize=True)

def bars(d, x, y, scale=1):
    for i, height in enumerate([18,35,25,49,31]):
        height=int(height*scale)
        d.rounded_rectangle((x+i*int(10*scale),y-height/2,x+i*int(10*scale)+int(5*scale),y+height/2),radius=int(2*scale),fill=GREEN)

def header(d, w, section):
    latin(d, 'AHANGBAN / LISTENING NOTES', 85, 76, 22)
    bars(d, w-160, 99, 1.2)
    persian(d, 'آهنگ‌بان', w-205, 77, 28, GREEN, True)
    d.line((85,155,w-85,155),fill=LINE,width=2)
    persian(d, section, w-90, 205, 29, MUTED)

def footer(d,w,h,label):
    d.line((85,h-128,w-85,h-128),fill=LINE,width=2)
    persian(d,label,w-90,h-94,25,MUTED)
    latin(d,'@AhangBan',85,h-98,25)

def disc(d,cx,cy,r,number):
    for i in range(11):
        rr=r-i*16
        if rr>40: d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=LINE,width=2)
    d.ellipse((cx-96,cy-96,cx+96,cy+96),fill=PANEL,outline=GREEN,width=2)
    persian(d,number,cx,cy-34,78,GREEN,True,'mt')
    d.ellipse((cx-7,cy+63,cx+7,cy+77),fill=GREEN)

tracks=[('کجایی','اول کلام','۰۱','02-kajayi.png'),('سنگ صبور','راوی چه می‌گوید؟','۰۲','03-sange-sabour.png'),('امیر بی‌گزند','این بار، اجرا','۰۳','04-amir-bi-gazand.png')]
for name, cue, num, filename in tracks:
    im,d=canvas(1920,1080); header(d,1920,'سه پیشنهاد برای شروع')
    disc(d,430,555,265,num)
    persian(d,name,1815,370,115,WHITE,True)
    persian(d,'محسن چاوشی',1815,535,45,MUTED)
    d.rounded_rectangle((1155,660,1815,755),radius=18,fill=PANEL,outline=LINE,width=2)
    persian(d,cue,1775,684,42,GREEN)
    footer(d,1920,1080,'راهنمای شنیدن؛ نه رتبه‌بندی رسمی')
    save(im,filename)

im,d=canvas(1920,1080);header(d,1920,'معرفی موسیقی / قسمت اول')
persian(d,'محسن چاوشی',1815,292,77,GREEN,True)
persian(d,'از کجا شروع کنیم؟',1815,410,105,WHITE,True)
for i,(name,cue,num,_) in enumerate(tracks):
    right=1815-i*570;left=right-530
    d.rounded_rectangle((left,625,right,815),radius=20,fill=PANEL,outline=LINE,width=2)
    persian(d,num,right-28,650,29,GREEN)
    persian(d,name,right-28,714,49,WHITE,True)
footer(d,1920,1080,'سه آهنگ؛ سه راه برای دقیق‌تر شنیدن')
save(im,'01-opening.png')

im,d=canvas(1920,1080);header(d,1920,'جمع‌بندی انتخاب‌های آهنگ‌بان')
persian(d,'انتخاب اول تو کدام است؟',1815,290,84,WHITE,True)
for i,(name,cue,num,_) in enumerate(tracks):
    right=1815-i*570;left=right-530
    d.rounded_rectangle((left,480,right,800),radius=22,fill=PANEL,outline=LINE,width=2)
    persian(d,num,right-32,515,39,GREEN)
    persian(d,name,right-32,600,55,WHITE,True)
    persian(d,['کلام','روایت','اجرا'][i],right-32,708,37,MUTED)
footer(d,1920,1080,'ترتیب دلخواهت را خودت انتخاب کن')
save(im,'05-recap.png')

im,d=canvas(1920,1080);header(d,1920,'حالا نوبت انتخاب توست')
persian(d,'تو کدام آهنگ را',1815,345,107,WHITE,True)
persian(d,'پیشنهاد می‌کنی؟',1815,500,107,GREEN,True)
persian(d,'اسمش را در کامنت بنویس.',1815,720,45,MUTED)
footer(d,1920,1080,'آهنگ‌بان | پیشنهادهایی برای شنیدن')
save(im,'06-question.png')

# Thumbnail is separately designed at YouTube's usual 16:9 thumbnail dimensions.
im,d=canvas(1280,720)
latin(d,'AHANGBAN / 001',65,48,18)
bars(d,1160,71,1)
persian(d,'محسن چاوشی',1200,160,57,MUTED,True)
persian(d,'انتخاب',1200,265,142,WHITE,True)
persian(d,'اولت؟',1200,440,142,GREEN,True)
for i,(name,_,num,_) in enumerate(tracks):
    top=202+i*137
    d.rounded_rectangle((62,top,605,top+109),radius=18,fill=PANEL,outline=LINE,width=2)
    persian(d,num,572,top+20,23,GREEN)
    persian(d,name,510,top+28,44,WHITE,True)
save(im,'thumbnail.png')
print('Created 6 full-HD editing cards and a 1280x720 thumbnail.')

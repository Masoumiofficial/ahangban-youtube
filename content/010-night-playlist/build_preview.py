"""Opening-frame concept only; not a rendered or timed video.
Run with Pillow, uharfbuzz and freetype-py (see requirements.txt).
"""
from pathlib import Path
import sys
from PIL import Image, ImageOps, ImageDraw
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent/'007-cosmic-ai'))
import persian_display as pd

def build():
    frame = ImageOps.fit(Image.open(HERE/'assets/rainy-night.jpg').convert('RGB'), (1920,1080)).convert('RGBA')
    shade = Image.new('RGBA',frame.size,(0,0,0,0))
    draw = ImageDraw.Draw(shade)
    for x in range(1920):
        draw.line([(x,0),(x,1080)], fill=(3,9,19,int(35+120*x/1919)))
    frame = Image.alpha_composite(frame,shade)
    # Scale the original artwork proportionally; never redraw or recolor the logo.
    logo = Image.open(REPO/'studio/ahangban-signature/references/ahangban-logo-horizontal-color.png').convert('RGBA')
    logo.thumbnail((300,115),Image.Resampling.LANCZOS)
    ImageDraw.Draw(frame).rounded_rectangle((1920-logo.width-125,65,1835,85+logo.height+20),radius=16,fill=(245,241,232,242))
    frame.alpha_composite(logo,(1920-logo.width-105,85))
    def text(value,size,y,color):
        layer=pd.render(value,size,color)
        assert layer.width < 1710, 'Text exceeds horizontal safe area'
        frame.alpha_composite(layer,(1815-layer.width,y))
    text('سه آهنگ برای وقتی که',74,385,'#fff5e7')
    text('شب تموم نمی‌شه',113,490,'#e9c18e')
    text('سه خواننده، سه حال‌وهوا',44,670,'#dbdfe3')
    text('طرح اولیهٔ تصویر — نه ویدیوی نهایی',30,942,'#aab5c3')
    ImageDraw.Draw(frame).text((110,967),'ahangban.ir',fill='#e9c18e',font_size=30)
    output=HERE/'delivery/opening-concept.jpg'
    output.parent.mkdir(exist_ok=True)
    frame.convert('RGB').save(output,quality=93)
    print(output)
if __name__ == '__main__': build()

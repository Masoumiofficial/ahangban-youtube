"""Real OpenType Persian shaping without Pillow RAQM.
Lalezar has GSUB glyphs, not a complete Arabic Presentation Forms cmap. Passing
arabic_reshaper output to it creates tofu. HarfBuzz + FreeType shapes original
Unicode instead, with no alteration or repackaging of the licensed font.
"""
from functools import lru_cache
from pathlib import Path
import math
import freetype
import uharfbuzz as hb
from PIL import Image,ImageFilter
FONT=Path(__file__).parent/'fonts/Lalezar-Regular.ttf'
DATA=FONT.read_bytes()

@lru_cache(maxsize=128)
def font(size):
 f=hb.Font(hb.Face(DATA));f.scale=(size*64,size*64);hb.ot_font_set_funcs(f)
 face=freetype.Face(str(FONT));face.set_pixel_sizes(0,size)
 return f,face

@lru_cache(maxsize=4096)
def shape(text,size):
 f,_=font(size);b=hb.Buffer();b.add_str(text);b.direction='rtl';b.script='Arab';b.language='fa';hb.shape(f,b)
 assert all(g.codepoint!=0 for g in b.glyph_infos),f'Unsupported display glyph: {text!r}'
 return tuple((g.codepoint,p.x_advance/64,p.x_offset/64,p.y_offset/64) for g,p in zip(b.glyph_infos,b.glyph_positions))

def width(text,size):return sum(g[1] for g in shape(text,size))

@lru_cache(maxsize=2048)
def render(text,size,color='#fff7e7'):
 _,face=font(size);glyphs=[];x=0.;minx=miny=0;maxx=maxy=0
 for gid,advance,xoff,yoff in shape(text,size):
  face.load_glyph(gid,freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL);slot=face.glyph;bm=slot.bitmap
  gx=round(x+xoff+slot.bitmap_left);gy=round(-yoff-slot.bitmap_top)
  if bm.width and bm.rows:
   # FreeType grayscale bitmaps can have row padding.
   pixels=bytes(bm.buffer);rows=[pixels[i*bm.pitch:i*bm.pitch+bm.width] for i in range(bm.rows)]
   glyph=Image.frombytes('L',(bm.width,bm.rows),b''.join(rows));glyphs.append((glyph,gx,gy))
   minx=min(minx,gx);miny=min(miny,gy);maxx=max(maxx,gx+bm.width);maxy=max(maxy,gy+bm.rows)
  x+=advance
 pad=5;mask=Image.new('L',(max(1,math.ceil(maxx-minx))+2*pad,max(1,math.ceil(maxy-miny))+2*pad))
 for glyph,gx,gy in glyphs:mask.paste(glyph,(gx-minx+pad,gy-miny+pad),glyph)
 outline=mask.filter(ImageFilter.MaxFilter(5));image=Image.new('RGBA',mask.size,(5,8,12,0));image.putalpha(outline)
 foreground=Image.new('RGBA',mask.size,color);foreground.putalpha(mask)
 return Image.alpha_composite(image,foreground)

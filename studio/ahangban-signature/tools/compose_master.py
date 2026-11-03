"""Compose authoritative portraits and the unchanged logo onto the studio architecture.
Requires Pillow. No generative face synthesis, redrawing, or semantic editing is done here.
Source photographs are contained, never stretched, and retain their complete source composition.
The final 4K image is composited; the generated architecture plate is 1376x768, not native 4K.
"""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFilter,ImageOps

ROOT=Path(__file__).resolve().parents[1]
W,H=3840,2160

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    lockfile=ROOT/'environment-lock.json'
    if lockfile.exists() and json.loads(lockfile.read_text()).get('approvalStatus')=='approved':
        raise SystemExit('Approved master is locked. Obtain explicit approval for a design revision before replacing it.')
    refs=ROOT/'references';work=ROOT/'working';out=ROOT/'master';out.mkdir(exist_ok=True)
    data=json.loads((ROOT/'reference-manifest.json').read_text())
    plate=Image.open(work/'architecture-clean.png').convert('RGB')
    assert plate.size==(1376,768)
    # Symmetric 16:9 crop: 16 px each side, 6 px top/bottom, no aspect distortion.
    canvas=plate.crop((16,6,1360,762)).resize((W,H),Image.Resampling.LANCZOS).convert('RGBA')
    # Reuse a single photoreal frame material sample; the layout is exactly twelve.
    frame=Image.open(refs/'frame-material-template.png').convert('RGB').resize((260,252),Image.Resampling.LANCZOS).convert('RGBA')
    placements=[];rows=[562,844];centers=[770,1230,1690,2150,2610,3070]
    for i,portrait in enumerate(data['portraits']):
        src=refs/portrait['file'];assert sha(src)==portrait['sha256']
        row=portrait['row']-1;col=portrait['column']-1;x=centers[col]-130;y=rows[row]
        shadow=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(shadow)
        d.rectangle((x+7,y+10,x+263,y+257),fill=(0,0,0,125))
        canvas=Image.alpha_composite(canvas,shadow.filter(ImageFilter.GaussianBlur(7)))
        copy=frame.copy();mask=Image.new('L',copy.size,0)
        ImageDraw.Draw(mask).rectangle((2,2,257,249),fill=255);copy.putalpha(mask)
        canvas.alpha_composite(copy,(x,y))
        # Small neutral museum matte; the source photo itself receives no color grading.
        aperture=(x+42,y+33,x+219,y+222)
        d=ImageDraw.Draw(canvas);d.rectangle(aperture,fill='#d6d2c7')
        photo=ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        contained=ImageOps.contain(photo,(aperture[2]-aperture[0]-4,aperture[3]-aperture[1]-4),Image.Resampling.LANCZOS)
        px=aperture[0]+(aperture[2]-aperture[0]-contained.width)//2
        py=aperture[1]+(aperture[3]-aperture[1]-contained.height)//2
        canvas.paste(contained,(px,py))
        # One fixed miniature champagne picture light per frame; preserve source faces below.
        lamp_y=y-21
        d=ImageDraw.Draw(canvas)
        d.line((centers[col]-15,lamp_y+1,centers[col]+15,lamp_y+1),fill='#5e5140',width=5)
        d.rounded_rectangle((centers[col]-16,lamp_y+2,centers[col]+16,lamp_y+11),radius=3,fill='#a89a7d',outline='#d8c9aa',width=1)
        d.line((centers[col]-12,lamp_y+11,centers[col]+12,lamp_y+11),fill='#f8dfac',width=2)
        placements.append({**portrait,'frameBounds':[x,y,x+260,y+252],'imageBounds':[px,py,px+contained.width,py+contained.height],'matteOpening':list(aperture)})
    # Crop transparent padding ONLY. The logo's non-transparent shapes, lettering, color,
    # internal spacing and proportions are never redrawn or reinterpreted.
    logo_src=refs/'ahangban-logo-horizontal-color.png';assert sha(logo_src)==data['logoSha256']
    logo=Image.open(logo_src).convert('RGBA');bbox=logo.getbbox();trimmed=logo.crop(bbox)
    # Plaque interior mapped through the same crop and scale as the architecture.
    scale=W/1344
    slot=[round((513-16)*scale),round((125-6)*scale),round((862-16)*scale),round((181-6)*scale)]
    fitted=ImageOps.contain(trimmed,(slot[2]-slot[0],slot[3]-slot[1]),Image.Resampling.LANCZOS)
    lx=slot[0]+(slot[2]-slot[0]-fitted.width)//2;ly=slot[1]+(slot[3]-slot[1]-fitted.height)//2
    # Keep the physical logo panel EMPTY in the permanent architecture master.
    # Core lettering and an optional blue light halo are independent compositing layers.
    overlaydir=ROOT/'overlays';overlaydir.mkdir(exist_ok=True)
    core=Image.new('RGBA',(W,H),(0,0,0,0));core.alpha_composite(fitted,(lx,ly))
    corepath=overlaydir/'AHANGBAN-LOGO-CORE.png';core.save(corepath,optimize=True)
    glow=Image.new('RGBA',(W,H),(0,0,0,0));alpha=core.getchannel('A')
    # Glow is added behind the unchanged original logo; it never replaces/recolors its glyphs.
    for radius,strength in [(28,.20),(12,.30),(4,.40)]:
        spread=alpha.filter(ImageFilter.GaussianBlur(radius)).point(lambda value:round(value*strength))
        halo=Image.new('RGBA',(W,H),(21,86,216,0));halo.putalpha(spread)
        glow=Image.alpha_composite(glow,halo)
    glowpath=overlaydir/'AHANGBAN-LOGO-GLOW.png';glow.save(glowpath,optimize=True)
    master=out/'MASTER-VIEW-001.png';canvas.convert('RGB').save(master,optimize=True)
    lock={
      'version':'1.2','approvalStatus':'pending_user_approval','master':str(master.relative_to(ROOT)),
      'masterSha256':sha(master),'dimensions':[W,H],'aspectRatio':'16:9',
      'architectureNativeDimensions':list(plate.size),'architectureCrop':[16,6,1360,762],
      'architectureIsUpscaledIn4KComposite':True,
      'architectureSource':'working/architecture-clean.png','architectureSourceSha256':sha(work/'architecture-clean.png'),
      'camera':'Centered frontal hero-wide, approximately 26mm visual intent; not a calibrated 3D camera.',
      'seatingCount':2,'seatingPurpose':'Two empty side-by-side host chairs; no characters yet.',
      'galleryReadingDirection':'right-to-left within each row',
      'portraitCount':12,'rows':2,'columns':6,'frameDimensions':[260,252],
      'horizontalFrameGap':200,'rowTopCoordinates':rows,'portraits':placements,
      'logo':{'source':str(logo_src.relative_to(ROOT)),'sourceSha256':sha(logo_src),'transparentPaddingCrop':list(bbox),'bounds':[lx,ly,lx+fitted.width,ly+fitted.height],'alteration':'uniform resampling only; no recoloring/redrawing','baseVisibility':'blank; no logo baked into master','coreOverlay':str(corepath.relative_to(ROOT)),'coreOverlaySha256':sha(corepath),'glowOverlay':str(glowpath.relative_to(ROOT)),'glowOverlaySha256':sha(glowpath),'glowStatus':'Static light layer, ready for opacity animation in video; not yet an animated video'},
      'voiceSelection':{'mainFemale':'voice-00','replacementMale':'voice-02','replacedMale':'voice-01','scope':'Session-specific voice identifiers; not guaranteed portable to other services/sessions.'},
      'immutableAfterApproval':['room geometry','ceiling','doors','walnut slats','acoustic panels','material palette','lighting positions','blank logo slot and original logo overlay','gallery order and positions','desk','one microphone and arm','two speakers','mixing console','headphones','two host chairs'],
      'presenterIdentityLock':'Presenters/character-lock.json',
      'presenterIdentityLockSha256':sha(ROOT/'Presenters/character-lock.json'),
      'additionalCameraViewsGenerated':0,
      'limitation':'This is a 2D AI architecture concept with exact-source artwork compositing, not an engineered acoustic design or a reconstructed 3D scene. A locked 3D scene is needed for guaranteed geometric identity across new camera angles.'
    }
    (ROOT/'environment-lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2))
    print('MASTER:',master,'4K blank-logo master; twelve exact-source photos in RTL reading order; separate original-logo and glow layers.')

if __name__=='__main__':main()

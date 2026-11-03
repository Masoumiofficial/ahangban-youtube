"""Camera-only proof: unchanged frontal photograph, digital reframes, no lip sync.
Uses the completed episode's audio directly; never resynthesizes either voice.
"""
import argparse, hashlib, json, math, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / '003-chavoshi-studio'))
import build_video as studio

SOURCE = REPO / 'studio/ahangban-signature/productions/HOSTS-VIEW-002.png'
EPISODE = REPO / 'downloads/ahangban-first-video-final.mp4'
DURATION = 28.0
FPS = 25
SIZE = (1280, 720)
# start, end, description, start (center x,y,zoom), end (center x,y,zoom)
SHOTS = [
    (0., 4., 'wide push-in', (.5,.5,1.), (.5,.51,1.12)),
    (4., 10.5, 'Ava frontal close-up / push-in', (.61,.565,3.05), (.605,.565,3.22)),
    (10.5, 16.01, 'two-shot / pull-back', (.5,.54,1.55), (.5,.52,1.35)),
    (16.01, 22.543708333333335, 'Sajad frontal close-up / push-in', (.405,.565,3.05), (.41,.565,3.22)),
    (22.543708333333335, 28., 'Ava frontal close-up / pull-back', (.605,.565,3.22), (.61,.565,3.05)),
]

def framing(t):
    for start, end, name, a, b in SHOTS:
        if start <= t < end:
            u = (t-start)/(end-start)
            ease = u*u*(3-2*u)
            return name, tuple(x+(y-x)*ease for x,y in zip(a,b))
    if t == DURATION:
        return SHOTS[-1][2], SHOTS[-1][4]
    raise ValueError('Time is outside the demo')

def crop_box(size, state):
    width,height = size
    cx,cy,zoom = state
    w,h = width/zoom,height/zoom
    left = min(max(0,cx*width-w/2),width-w)
    top = min(max(0,cy*height-h/2),height-h)
    return left,top,left+w,top+h

def render(root):
    root.mkdir(parents=True,exist_ok=True)
    base = Image.open(SOURCE).convert('RGBA')
    for name in ('AHANGBAN-LOGO-GLOW.png','AHANGBAN-LOGO-CORE.png'):
        base = Image.alpha_composite(base,Image.open(studio.STUDIO/'overlays'/name).convert('RGBA'))
    base = base.convert('RGB')
    fonts = root/'fonts';fonts.mkdir(exist_ok=True)
    for font in studio.FONTS.glob('*.ttf'):shutil.copy2(font,fonts/font.name)
    captions = REPO/'rendered/video-004-own-voice/subtitles.ass'
    if not captions.exists():
        # Restore captions from the tracked timeline if the scratch cache is gone.
        timeline = json.loads((HERE.parent/'004-chavoshi-own-voice/delivery/timeline.json').read_text())
        studio.subtitles(root,timeline);captions=root/'subtitles.ass'
    dest = root/'ahangban-camera-demo-no-lipsync.mp4'
    cmd = [studio.FF,'-hide_banner','-loglevel','warning','-y','-filter_threads','2',
           '-f','rawvideo','-pixel_format','rgb24','-video_size','1280x720','-framerate',str(FPS),'-i','pipe:0',
           '-i',str(EPISODE),'-map','0:v:0','-map','1:a:0',
           '-vf',f"ass=filename='{captions}':fontsdir='{fonts}',format=yuv420p",
           '-c:v','libx264','-preset','veryfast','-crf','21','-threads','2',
           '-c:a','copy','-t',str(DURATION),'-movflags','+faststart',
           '-metadata','comment=Camera-only proof. Digital frontal reframes, not new 3D angles. Static faces, NO lip sync. Audio copied from approved first episode. Not published.',str(dest)]
    process = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(round(DURATION*FPS)):
            t=frame/FPS
            name,state=framing(t)
            im=base.transform(SIZE,Image.Transform.EXTENT,crop_box(base.size,state),Image.Resampling.BICUBIC)
            layer=Image.new('RGBA',SIZE);d=ImageDraw.Draw(layer)
            # Screen-space graphics are NOT zoomed/cropped with the photograph.
            d.rounded_rectangle((72,642,1208,712),radius=12,fill=(9,20,28,230))
            d.rounded_rectangle((970,32,1230,81),radius=10,fill=(9,20,28,225))
            im=Image.alpha_composite(im.convert('RGBA'),layer)
            d=ImageDraw.Draw(im)
            studio.text(d,'تست دوربین • بدون لب‌خوانی',1214,43,19,studio.GOLD,True)
            speaker='سجاد' if 16.01<=t<22.543708333333335 else 'آوا'
            studio.text(d,speaker,1210,91,22,studio.WHITE,True)
            if frame in (50,175,325,475,625):
                im.convert('RGB').save(root/f'frame-{frame:04d}.jpg',quality=94)
            process.stdin.write(im.convert('RGB').tobytes())
    finally:
        process.stdin.close()
        code=process.wait()
    if code:raise subprocess.CalledProcessError(code,cmd)
    report={'status':'camera_only_rendered_lipsync_NOT_implemented','duration':DURATION,
            'resolution':SIZE,'fps':FPS,'shots':SHOTS,'trueNewCameraAngles':False,
            'facialAnimation':False,'lipSync':False,'voicesRegenerated':False,
            'audio':'AAC stream copied from completed first episode; no voice or script changes',
            'sourceImageSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'sourceEpisodeSha256':hashlib.sha256(EPISODE.read_bytes()).hexdigest(),
            'videoSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
            'youtubePublished':False}
    (root/'camera-demo-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(dest,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,default=REPO/'rendered/video-005-cinematic')
    render(p.parse_args().output_root.resolve())

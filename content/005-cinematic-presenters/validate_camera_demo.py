"""Technical camera proof QA; deliberately does not assert lip-sync quality."""
import argparse, hashlib, json, subprocess
import imageio_ffmpeg
from pathlib import Path
import build_camera_demo as build

def validate(root):
    video=root/'ahangban-camera-demo-no-lipsync.mp4'
    manifest=json.loads((root/'camera-demo-manifest.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(video)==manifest['videoSha256']
    assert sha(build.SOURCE)==manifest['sourceImageSha256']
    assert sha(build.EPISODE)==manifest['sourceEpisodeSha256']
    assert not manifest['lipSync'] and not manifest['trueNewCameraAngles']
    subprocess.run([build.studio.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
    reader=imageio_ffmpeg.read_frames(str(video))
    try:
        meta=next(reader)
    finally:
        reader.close()
    assert tuple(meta['size'])==build.SIZE
    assert meta['fps']==build.FPS
    assert abs(meta['duration']-build.DURATION)<0.12
    def audio_hash(path):
        return subprocess.check_output([build.studio.FF,'-v','error','-i',str(path),'-map','0:a:0',
            '-t',str(build.DURATION),'-c:a','pcm_s16le','-f','hash','-hash','sha256','-'],text=True).strip().split('=')[-1]
    a=audio_hash(build.EPISODE);b=audio_hash(video)
    assert a==b,'The camera edit must not change either voice'
    for t in (2,7,13,19,25):
        subprocess.run([build.studio.FF,'-v','error','-y','-ss',str(t),'-i',str(video),
            '-frames:v','1',str(root/f'encoded-{t:02d}.jpg')],check=True)
    qa={'status':'technical_checks_passed_pending_user_visual_review','fullDecode':'PASS',
        'decodedAudioPCMMatchesFirst28SecondsOfOriginalEpisode':True,'audioPcmSha256':a,
        'videoSha256':sha(video),'decodedResolution':list(meta['size']),'decodedFps':meta['fps'],
        'containerDuration':meta['duration'],'newCameraAngles':False,'lipSync':False,
        'facialAnimation':False,'audioRegenerated':False,
        'note':'Digital crop/zoom sample only; no lip-sync quality claim. Original first video is preserved.'}
    (root/'qa-report.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps(qa,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,default=build.REPO/'rendered/video-005-cinematic')
    validate(p.parse_args().output_root.resolve())

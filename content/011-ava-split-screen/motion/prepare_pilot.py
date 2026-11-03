"""Prepare exact approved Ava and preserved voice06 for REAL model inference elsewhere.
No model downloads, remote execution, or inference occur here. No still-as-animation export.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,wave,zipfile,shutil
import numpy as np
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];EP=HERE.parent
WORK=ROOT/'rendered/ava-motion-pilot';FF=imageio_ffmpeg.get_ffmpeg_exe();FPS=25
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pcm(path):
 r=subprocess.run([FF,'-v','error','-i',str(path),'-ar','48000','-ac','2','-f','s16le','pipe:1'],check=True,capture_output=True)
 return np.frombuffer(r.stdout,dtype='<i2').reshape(-1,2).copy()
def write(p,a,rate=48000):
 with wave.open(str(p),'wb') as w:w.setparams((a.shape[1],2,rate,0,'NONE','not compressed'));w.writeframes(a.astype('<i2').tobytes())
def main():
 WORK.mkdir(parents=True,exist_ok=True)
 actor=EP/'assets/ava-actor-generated.png';hook=ROOT/'content/010-night-playlist/final-female/audio/hook.mp3'
 assert sha(actor)=='68854d222a57969ff89567530f8b4c8202d4f8b8855acac96a23e7628e861adf'
 assert sha(hook)=='87548f0636deaf4b5776ad24625b504dbe13679c134e5ed704ff3d645901a995'
 # Copy byte-identical APPROVED pose; NO mic/studio inside model input.
 image=WORK/'ava.png';shutil.copy2(actor,image)
 talk=pcm(hook);assert len(talk)==215040 # complete4.48s, no word trimming
 pad=np.zeros((17280,2),dtype=np.int16)
 padded=np.concatenate((talk,pad));assert len(padded)==232320
 write(WORK/'talk-playback.wav',padded)
 subprocess.run([FF,'-v','error','-y','-i',str(WORK/'talk-playback.wav'),'-ar','16000','-ac','1',str(WORK/'talk-conditioning.wav')],check=True)
 silence=np.zeros((64640,1),dtype=np.int16);write(WORK/'listen-conditioning.wav',silence,16000)
 tr=json.loads((ROOT/'content/010-night-playlist/tracks.json').read_text())[0]
 music=ROOT/'rendered/video-010-night-playlist/source-media'/tr['file'];assert sha(music)==tr['sha256']
 subprocess.run([FF,'-v','error','-y','-ss','65','-i',str(music),'-t','4.04','-af','loudnorm=I=-18:TP=-2:LRA=10,afade=t=in:d=0.12,afade=t=out:st=3.79:d=0.25','-ar','48000','-ac','2','-c:a','pcm_s16le',str(WORK/'listen-playback.wav')],check=True)
 jobs=[dict(id='talk',conditioning='talk-conditioning.wav',playback='talk-playback.wav',frames=121,duration=4.84,completeSpeechSeconds=4.48,tailSilenceSeconds=.36,text='شده آخر شب، یه آهنگ رو هی از اول بذاری؟',prompt='The same woman in the reference asks a short friendly question, speaking naturally to the camera with accurate small lip and jaw movement, gentle head motion and occasional natural blinking. Preserve her exact face, black scarf, hair, embroidered clothes, jewelry and posture. No broad gestures or large turns. Her lips relax closed at the end. A perfectly fixed camera and uniform flat green background.'),dict(id='listen',conditioning='listen-conditioning.wav',playback='listen-playback.wav',frames=101,duration=4.04,conditioningIsSilence=True,musicUsedOnlyForPlayback=True,prompt='The same woman quietly listens attentively. Her lips stay gently CLOSED the entire time. She does NOT speak or sing or mouth words. Subtle slow head nod, one natural blink and a brief downward glance, then a calm gaze toward camera. Preserve her exact face, black scarf, hair, embroidered clothes and jewelry. No large gestures. A perfectly fixed camera and uniform flat green background.')]
 files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(WORK.iterdir()) if p.name in ['ava.png','talk-playback.wav','talk-conditioning.wav','listen-conditioning.wav','listen-playback.wav']}
 manifest=dict(status='INPUTS_PREPARED_NOT_RENDERED',voice='voice-06',newSpeechSynthesized=False,approvedActorSourceSha256=sha(actor),reviewedSpeechSourceSha256=sha(hook),musicOriginalSourceSha256=sha(music),musicOriginalSourceStart=65,modelImage='ava.png',modelFPS=FPS,preferredNativeActorResolution=[768,768],resolutionIsNot1080pNativeActor=True,jobs=jobs,files=files,inferenceExecuted=False,copyrightCleared=False,publishAuthorized=False,conditions=['No new face or wardrobe','No camera pans/zooms over still image as a substitute','NO singer/music vocals in listening conditioning','Microphone, covers, gallery and logo composited separately and remain fixed','Check identity, Persian lip sync and listening closed mouth by human viewing before full production','Frame-change checks alone do not certify phoneme sync or naturalness'])
 (WORK/'pilot-inputs.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(HERE/'pilot-inputs.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 out=ROOT/'downloads/ahangban-ava-motion-pilot-inputs.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for name in [*files,'pilot-inputs.json']:
   info=zipfile.ZipInfo(name,date_time=(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,(WORK/name).read_bytes())
 (HERE/'bundle.json').write_text(json.dumps(dict(path=str(out.relative_to(ROOT)),sha256=sha(out),bytes=out.stat().st_size),indent=2)+'\n')
 print(json.dumps(dict(status=manifest['status'],zip=str(out.relative_to(ROOT)),sha256=sha(out),bytes=out.stat().st_size),indent=2))
if __name__=='__main__':main()

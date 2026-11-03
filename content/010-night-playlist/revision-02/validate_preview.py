"""Independent encoded-preview checks, never naturalness/pronunciation approval."""
import json,math,re,subprocess
import numpy as np
from PIL import Image,ImageChops
import imageio_ffmpeg
import build_revision as r

def segment(path,start,duration):
 data=subprocess.check_output([r.FF,'-v','error','-i',str(path),'-ss',str(start),'-t',str(duration),'-map','0:a:0','-ac','1','-ar','16000','-f','s16le','-'])
 return np.frombuffer(data,dtype='<i2').astype(float)/32768

def main():
 manifest=json.loads((r.HERE/'delivery/demo-manifest.json').read_text());video=r.REPO/manifest['video'];root=r.WORK/'youtube';plan=json.loads((root/'timeline.json').read_text())
 assert r.sha(video)==manifest['sha256'];subprocess.run([r.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(video));meta=next(reader);reader.close()
 assert tuple(meta['size'])==(1920,1080) and meta['fps']==25
 assert abs(meta['duration']-plan['duration'])<.12
 checks=[]
 for e in plan['events']:
  duration=e['duration']-1;actual=segment(video,e['start']+.5,duration);source=segment(root/'normalized'/(e['id']+'.wav'),.5,duration)
  n=min(len(source),len(actual));a=actual[:n];s=source[:n];corr=float(np.dot(a,s)/np.sqrt(np.dot(a,a)*np.dot(s,s)));assert corr>.97,(e['id'],corr)
  assert np.sqrt(np.mean(a*a))>.004
  checks.append(dict(id=e['id'],type=e['type'],sourceToDecodedOutputCorrelation=corr))
 for cue in plan['captions']:
  assert not any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in plan['events'] if e['type']=='music')
 report=subprocess.run([r.FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],text=True,capture_output=True,check=True)
 peak=float(re.search(r'max_volume:\s*([+-]?[0-9.]+) dB',report.stderr).group(1));assert peak<=-.3
 frames=root/'qa-frames';frames.mkdir(exist_ok=True)
 music=next(e for e in plan['events'] if e['type']=='music');pairs=[]
 for i,t in enumerate([music['start']+1,music['start']+2,.5,plan['duration']-2]):
  path=frames/f'{i:02d}.jpg';r.run(['-ss',t,'-i',video,'-frames:v','1','-update','1',path]);pairs.append(Image.open(path).convert('RGB'))
 assert ImageChops.difference(pairs[0].crop((700,80,1000,300)),pairs[1].crop((700,80,1000,300))).getbbox()
 assert ImageChops.difference(pairs[0].crop((985,735,1775,820)),pairs[1].crop((985,735,1775,820))).getbbox()
 voice=json.loads((r.HERE/'delivery/voice-preview-manifest.json').read_text());dry=r.decode(r.REPO/voice['output']);assert abs(dry).max()<.99
 assert not set(voice['newSpeechSourceHashes'])&set(voice['previousAudioSha256'])
 covers=json.loads((r.HERE/'delivery/cover-manifest.json').read_text())
 for k,size in [('youtube',(1280,720)),('reel',(1080,1920))]:
  a=covers['outputs'][k];p=r.REPO/a['file'];assert Image.open(p).size==size and r.sha(p)==a['sha256']
 assert covers['logoSha256']==r.sha(r.b.g.LOGO)
 qa=dict(status='technical_preview_QA_passed_NOT_human_voice_approval',duration=meta['duration'],resolution=list(meta['size']),fps=meta['fps'],fullDecode='PASS',decodedPeakDbFS=peak,audioChecks=checks,cameraAndAudioSpectrumMotion='PASS',drySpeechDecoded=True,drySpeechHasMusic=False,drySpeechEffects=False,threeFreshClipsNotReusedFromRejected010=True,logoAndCoverOutputHashes='PASS',coverSizes='PASS',speechSpeedOrPitchChanged=False,humanRecordingUsed=False,preciseEmotionOrWordStressControl=False,fullEpisodeRebuilt=False,newVoicePerformanceApproved=False,published=False,copyrightCleared=False)
 r.dump(r.HERE/'delivery/qa-report.json',qa);print(json.dumps(qa,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

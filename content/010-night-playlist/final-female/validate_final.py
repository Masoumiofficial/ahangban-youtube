"""Independent final media checks: single approved female identity, source audio,
native resolution, exact reviewed-performance and approved-cover hashes.
Technical checks are not pronunciation/naturalness or Content ID clearance.
"""
import argparse,json,re,subprocess
import numpy as np
from PIL import Image,ImageChops
import imageio_ffmpeg
import build_final as f

def segment(path,start=0,duration=None):
 args=[f.FF,'-v','error','-i',str(path),'-ss',str(start)]
 if duration is not None:args+=['-t',str(duration)]
 data=subprocess.check_output(args+['-map','0:a:0','-ar','16000','-ac','1','-f','s16le','-'])
 return np.frombuffer(data,dtype='<i2').astype(float)/32768

def validate(kind):
 root=f.WORK/kind;plan=json.loads((root/'timeline.json').read_text());prov=json.loads((root/'source-provenance.json').read_text());shots=json.loads((root/'shots.json').read_text());video=root/f'ahangban-night-final-{kind}.mp4'
 subprocess.run([f.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(video));meta=next(reader);reader.close()
 assert tuple(meta['size'])==f.b.SIZES[kind] and meta['fps']==f.b.FPS[kind]
 assert abs(meta['duration']-plan['duration'])<.12
 assert plan['narrationGender']=='female_only' and not plan['maleNarrationUsed']
 speech=[e for e in plan['events'] if e['type']=='speech'];music=[e for e in plan['events'] if e['type']=='music']
 assert len(speech)==(6 if kind=='youtube' else 2) and len(music)==3
 for row in prov['speech']:
  assert row['speaker']=='female' and row['voice']=='voice-06'
  assert f.sha(f.AUDIO/row['file'])==row['sourceSha256']==row['sha256']
  if row['exactReviewedPerformanceReuse']:assert f.sha(f.REPO/row['reviewedSource'])==row['sourceSha256']
 for e,tr in zip(music,f.b.TRACKS):
  assert e['duration']==(35 if kind=='youtube' else 12)
  assert e['sourceFile']==tr['file'] and e['sourceStart']==(tr['excerptStart'] if kind=='youtube' else tr['verticalExcerptStart'])
 for a in prov['assets']:
  path=root/'source-media'/a['file'];assert f.sha(path)==a['sha256'];assert subprocess.check_output(['git','hash-object',str(path)],text=True).strip()==a['gitBlob']
 assert f.sha(root/'cover.jpg')==prov['approvedCoverSha256']==f.sha(f.COVERS[kind]);assert f.sha(f.b.g.LOGO)==prov['logoSha256']
 for asset in prov['environmentPlates']:assert f.sha(f.REPO/asset['path'])==asset['sha256']
 for cue in plan['captions']:
  assert not any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in music)
 assert all(a['end']==z['start'] for a,z in zip(shots,shots[1:]));assert abs(sum(s['frames'] for s in shots)/f.b.FPS[kind]-plan['duration'])<.025
 checks=[]
 for e in plan['events']:
  actual=segment(video,e['start']+.5,e['duration']-1);source=segment(root/'normalized'/(e['id']+'.wav'),.5,e['duration']-1);n=min(len(actual),len(source));a=actual[:n];s=source[:n]
  correlation=float(np.dot(a,s)/np.sqrt(np.dot(a,a)*np.dot(s,s)));rms=float(np.sqrt(np.mean(a*a)));assert correlation>.97,(kind,e['id'],correlation);assert rms>.004
  checks.append(dict(id=e['id'],type=e['type'],sourceToDecodedOutputCorrelation=correlation,rms=rms))
 volume=subprocess.run([f.FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],text=True,capture_output=True,check=True)
 peak=float(re.search(r'max_volume:\s*([+-]?[0-9.]+) dB',volume.stderr).group(1));assert peak<=-.3
 frames=root/'qa-frames';frames.mkdir(exist_ok=True);pairs=[]
 for i,t in enumerate([music[0]['start']+1,music[0]['start']+2,.6,music[1]['start']+3,music[2]['start']+3,plan['duration']-2]):
  path=frames/f'{i:02d}.jpg';f.r.run(['-ss',t,'-i',video,'-frames:v','1','-update','1',path]);pairs.append(Image.open(path).convert('RGB'))
 bg=(700,80,1000,300) if kind=='youtube' else (380,700,700,790)
 sp=(985,735,1775,820) if kind=='youtube' else (110,1325,900,1395)
 assert ImageChops.difference(pairs[0].crop(bg),pairs[1].crop(bg)).getbbox()
 assert ImageChops.difference(pairs[0].crop(sp),pairs[1].crop(sp)).getbbox()
 q=dict(status='technical_final_QA_passed_pending_final_user_listening',kind=kind,video=video.name,sha256=f.sha(video),bytes=video.stat().st_size,duration=meta['duration'],resolution=list(meta['size']),fps=meta['fps'],fullDecode='PASS',narration='female_only',narrationVoice='voice-06',maleNarrationUsed=False,exactReviewedFemalePerformancesReused=2 if kind=='youtube' else 0,reviewedCoverBytesPreserved='PASS',sourceLogoAndPlateHashes='PASS',musicSamples=3,musicSecondsEach=plan['musicSecondsEach'],musicTotalSeconds=sum(e['duration'] for e in music),decodedPeakDbFS=peak,audioChecks=checks,encodedCameraAndRealFFTMovement='PASS',voicePitchOrSpeedChanged=False,humanRecordingUsed=False,personalCloneUsed=False,pronunciationScriptCorrected=True,pronunciationAurallyVerifiedByAgent=False,captionTiming=plan['captionTiming'],cameraTiming=plan['cameraTiming'],finalUserListeningPending=True,copyrightCleared=False,publishAuthorized=False,published=False)
 f.dump(root/'qa-report.json',q);print(json.dumps(q,ensure_ascii=False,indent=2));return q
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);validate(p.parse_args().kind)

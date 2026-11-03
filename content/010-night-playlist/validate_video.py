"""Independent checks on exported video/audio, not just intended edit commands.
Checks are technical, never a new subjective/aural approval or rights clearance.
"""
import argparse,json,math,re,subprocess
import numpy as np
from PIL import Image,ImageChops
import imageio_ffmpeg
import build_video as b

def audio(path,start=0,duration=None):
 args=[b.FF,'-v','error','-i',str(path),'-ss',str(start)]
 if duration is not None:args+=['-t',str(duration)]
 data=subprocess.check_output(args+['-map','0:a:0','-ac','1','-ar','16000','-f','s16le','-'])
 return np.frombuffer(data,dtype='<i2').astype(float)/32768

def validate(kind):
 root=b.REPO/f'rendered/video-010-night-playlist/{kind}';plan=json.loads((root/'timeline.json').read_text());prov=json.loads((root/'source-provenance.json').read_text());shots=json.loads((root/'shots.json').read_text())
 video=root/f'ahangban-night-playlist-{kind}.mp4';subprocess.run([b.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(video));meta=next(reader);reader.close()
 assert tuple(meta['size'])==b.SIZES[kind] and abs(meta['fps']-b.FPS[kind])<.01
 assert abs(meta['duration']-plan['duration'])<.12
 assert prov['allNarrationSynthetic'] and not prov['humanRecordingUsed'] and not prov['personalCloneUsed']
 for s in prov['speech']:
  assert s['voice']==('voice-06' if s['speaker']=='female' else 'voice-07')
  assert b.sha(b.AUDIO/(s['id']+'.mp3'))==s['sourceSha256']
 for item in prov['assets']:
  path=root/'source-media'/item['file'];assert b.sha(path)==item['sha256'];assert subprocess.check_output(['git','hash-object',str(path)],text=True).strip()==item['gitBlob']
 assert b.sha(b.g.LOGO)==prov['logoSha256']
 for item in prov['environmentPlates']:assert b.sha(b.REPO/item['path'])==item['sha256']
 music=[e for e in plan['events'] if e['type']=='music'];assert len(music)==3
 assert all(e['duration']==(35 if kind=='youtube' else 12) for e in music)
 assert [s['index'] for s in shots]==list(range(len(shots)))
 assert all(a['end']==c['start'] for a,c in zip(shots,shots[1:]))
 assert abs(sum(s['frames'] for s in shots)/b.FPS[kind]-plan['duration'])<.025
 checks=[]
 for e in plan['events']:
  margin=.5;duration=e['duration']-margin*2;actual=audio(video,e['start']+margin,duration)
  id=e.get('id',e['scene']);expected=audio(root/'normalized'/(id+'.wav'),margin,duration);n=min(len(expected),len(actual));expected=expected[:n];actual=actual[:n]
  corr=float(np.dot(expected,actual)/np.sqrt(np.dot(expected,expected)*np.dot(actual,actual)));rms=float(np.sqrt(np.mean(actual**2)))
  assert corr>.97,(kind,id,corr);assert rms>.004,(kind,id,rms)
  checks.append(dict(type=e['type'],id=id,start=e['start'],duration=e['duration'],sourceToDecodedOutputCorrelation=corr,rms=rms))
 for cue in plan['captions']+plan['ctas']:
  assert not any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in music)
 volume=subprocess.run([b.FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
 peak=float(re.search(r'max_volume:\s*([+-]?[0-9.]+) dB',volume.stderr).group(1));assert peak<=-.3
 decoded=audio(video);rms=float(np.sqrt(np.mean(decoded**2)))
 frames=root/'qa-frames';frames.mkdir(exist_ok=True)
 for i,t in enumerate([.2,3.,8.]+[e['start']+4 for e in music]+[plan['duration']-5]):b.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,frames/f'{i:02d}.png'])
 pairs=[]
 for i,t in enumerate((music[0]['start']+1,music[0]['start']+2)):
  path=frames/f'motion-{i}.png';b.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,path]);pairs.append(Image.open(path).convert('RGB'))
 bg=(450,650,850,900) if kind=='reel' else (500,180,900,380)
 spectrum=(110,1325,900,1410) if kind=='reel' else (975,800,1775,915)
 assert ImageChops.difference(pairs[0].crop(bg),pairs[1].crop(bg)).getbbox(),'Background camera movement absent'
 assert ImageChops.difference(pairs[0].crop(spectrum),pairs[1].crop(spectrum)).getbbox(),'Actual audio spectrum absent'
 report=dict(status='technical_QA_passed_pending_final_user_listening',kind=kind,video=video.name,sha256=b.sha(video),bytes=video.stat().st_size,
  duration=meta['duration'],resolution=list(meta['size']),fps=meta['fps'],fullDecode='PASS',sourceAndLogoHashes='PASS',
  freshSpeechSourceHashes='PASS',narrationVoices={'female':'voice-06','male':'voice-07'},voicePitchOrSpeedChanged=False,
  humanRecordingUsed=False,personalCloneUsed=False,presenterImagesUsed=False,musicSamples=3,musicSecondsEach=plan['musicSecondsEach'],
  musicTotalSeconds=sum(e['duration'] for e in music),musicCameraShots=sum(1 for s in shots if plan['events'][s['eventIndex']]['type']=='music'),
  encodedCameraAndSpectrumMotion='PASS',decodedAudioChecks=checks,decodedPeakDbFS=peak,overallRmsDbFS=round(20*math.log10(rms),2),
  captionTiming=plan['captionTiming'],cameraTiming=plan['cameraTiming'],copyrightCleared=False,youtubePublished=False,instagramPublished=False,
  limitations='Voice identity approval covers the 008 samples, not a new listening sign-off on 010. Music windows are signal-selected, not certified chorus or semantic edits. AI still environments animated in 2D, not 3D footage. No current-song-trend, rights-clearance or virality claim.')
 (root/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);validate(p.parse_args().kind)

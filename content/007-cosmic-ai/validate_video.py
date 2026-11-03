"""Decode exported files; validate actual audio, native geometry and provenance.
No aural pronunciation, aesthetic approval, current trend or rights-clearance claim.
"""
import argparse,json,math,re,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops
import imageio_ffmpeg
import build_video as b

def audio(path,start=0,duration=None,seek_before_input=False):
 cmd=[b.FF,'-v','error']
 if seek_before_input:cmd+=['-ss',str(start)]
 cmd+=['-i',str(path)]
 if not seek_before_input:cmd+=['-ss',str(start)]
 if duration is not None:cmd+=['-t',str(duration)]
 cmd+=['-map','0:a:0','-ac','1','-ar','16000','-f','s16le','-']
 return np.frombuffer(subprocess.check_output(cmd),dtype='<i2').astype(float)/32768

def correlation(a,c):
 n=min(len(a),len(c));a=a[:n];c=c[:n]
 return float(np.dot(a,c)/max(1e-12,np.sqrt(np.dot(a,a)*np.dot(c,c))))

def validate(kind):
 root=b.REPO/f'rendered/video-007-cosmic/{kind}';plan=json.loads((root/'timeline.json').read_text());prov=json.loads((root/'source-provenance.json').read_text())
 video=root/f'ahangban-cosmic-{kind}.mp4'
 assert prov['allSpeechSynthetic'] and not prov['humanRecordingUsed'] and not prov['personalCloneUsed']
 assert b.sha(b.base.LOGO)==prov['logoSha256'];assert b.sha(b.HERE/'fonts/Lalezar-Regular.ttf')==prov['fontSha256']
 for item in prov['assets']:
  p=root/'source-media'/item['file'];assert b.sha(p)==item['sha256']
  assert subprocess.check_output(['git','hash-object',str(p)],text=True).strip()==item['gitBlob']
 for item in prov['speech']:
  assert item['voice']==('voice-05' if item['speaker']=='female' else 'voice-04')
  assert b.sha(b.AUDIO/(item['id']+'.mp3'))==item['sourceSha256']
  assert b.sha(root/'normalized'/(item['id']+'.wav'))==item['normalizedSha256']
 subprocess.run([b.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(video));meta=next(reader);reader.close()
 assert tuple(meta['size'])==b.SIZES[kind];assert abs(meta['fps']-b.FPS[kind])<.01
 assert abs(meta['duration']-plan['duration'])<.1
 events=plan['events'];music=[e for e in events if e['type']=='music'];assert len(music)==5
 assert all(abs(e['duration']-(20 if kind=='youtube' else 8))<.001 for e in music)
 checks=[]
 for e in events:
  file=(e['id'] if e['type']=='speech' else e['scene'])+'.wav';margin=.45;duration=e['duration']-margin*2
  actual=audio(video,e['start']+margin,duration);expected=audio(root/'normalized'/file,margin,duration)
  corr=correlation(actual,expected);rms=float(np.sqrt(np.mean(actual**2)))
  assert corr>.97,(kind,e,corr);assert rms>.004,(kind,e,rms)
  checks.append({'type':e['type'],'id':e.get('id',e['scene']),'outputStart':e['start'],'duration':e['duration'],
   'decodedOutputToFreshPreparedAudioCorrelation':corr,'rms':rms})
 for c in plan['captions']:
  assert any(e['type']=='speech' and e['start']<=c['start']<c['end']<=e['end'] for e in events)
 for cta in plan['ctas']:
  assert not any(max(cta['start'],e['start'])<min(cta['end'],e['end']) for e in music)
 volume=subprocess.run([b.FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
 peak=float(re.search(r'max_volume:\s*([+-]?[0-9.]+) dB',volume.stderr).group(1));assert peak<=-.3
 decoded=audio(video);rms=float(np.sqrt(np.mean(decoded**2)));assert rms>.005
 frames=root/'qa-frames';frames.mkdir(exist_ok=True)
 for i,t in enumerate([.2,2.,12.]+[e['start']+3 for e in music]+[plan['duration']-3]):
  b.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,frames/f'{i:02d}.jpg'])
 pair=[]
 for i,t in enumerate((music[0]['start']+1,music[0]['start']+2)):
  p=frames/f'motion-{i}.png';b.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,p]);pair.append(Image.open(p).convert('RGB'))
 region=(400,200,1000,650) if kind=='youtube' else (450,750,850,1000)
 assert ImageChops.difference(pair[0].crop(region),pair[1].crop(region)).getbbox(),'Cinematic background motion absent'
 bands=b.base.spectrum(root/'audio.wav',b.FPS[kind],plan['duration']);assert bands.max()>.3 and bands.std()>.02
 report={'status':'technical_QA_passed_pending_user_listening_and_aesthetic_review','kind':kind,'video':video.name,
  'sha256':b.sha(video),'bytes':video.stat().st_size,'resolution':list(meta['size']),'fps':meta['fps'],'duration':meta['duration'],
  'fullDecode':'PASS','sourceHashes':'PASS','selectedFreshSyntheticSpeech':'PASS','allSpeechSynthetic':True,
  'humanRecordingUsed':False,'personalCloneUsed':False,'presenterImagesUsed':False,'musicSamples':5,
  'musicSecondsEach':20 if kind=='youtube' else 8,'actualDecodedAudioChecks':checks,'decodedPeakDbFS':peak,
  'overallRmsDbFS':round(20*math.log10(rms),2),'cinematicBackgroundMotion':'PASS','actualAudioSpectrum':'PASS',
  'captionTiming':'Proportional four-word groups, not forced aligned','openTypePersianShaping':'HarfBuzz + FreeType, original Unicode; no presentation-form tofu',
  'copyrightCleared':False,'youtubePublished':False,'instagramPublished':False,
  'limitations':'No independent aural/pronunciation sign-off, current-song-trend verification or virality guarantee. Synthetic imagery is animated 2D, not generated live-action footage.'}
 (root/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);validate(p.parse_args().kind)

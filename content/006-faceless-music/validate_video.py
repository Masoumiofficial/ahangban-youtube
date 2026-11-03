"""Independent technical QA for faceless horizontal and vertical exports.
No aural/phonetic or rights-clearance claim. Frames extracted for manual review.
"""
import argparse,hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from PIL import Image,ImageChops
import build_video as build

def audio_pcm(path,start=0,duration=None,rate=16000):
 args=[build.FF,'-v','error','-i',str(path),'-ss',str(start)]
 if duration is not None:args+=['-t',str(duration)]
 data=subprocess.check_output(args+['-map','0:a:0','-ac','1','-ar',str(rate),'-f','s16le','-'])
 return np.frombuffer(data,dtype='<i2').astype(float)/32768

def validate(root,kind):
 plan=json.loads((root/'timeline.json').read_text());prov=json.loads((root/'source-provenance.json').read_text())
 video=root/f'ahangban-faceless-{kind}.mp4'
 assert build.sha(build.SOURCE)==build.SOURCE_SHA==prov['sourceEpisodeSha256']
 assert build.sha(build.LOGO)==prov['logoSha256']
 assert not prov['presenterImagesUsed'] and not prov['studioImagesUsed'] and not prov['voicesRegenerated']
 for art in prov['assets']:
  p=root/'source-media'/Path(art['path']).name
  assert build.sha(p)==art['sha256']
  blob=subprocess.check_output(['git','hash-object',str(p)],cwd=build.REPO,text=True).strip()
  assert blob==art['gitBlob']
 subprocess.run([build.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(video));meta=next(reader);reader.close()
 assert tuple(meta['size'])==build.SIZES[kind];assert abs(meta['fps']-build.FPS[kind])<.01
 assert abs(meta['duration']-plan['duration'])<.15
 events=plan['events'];previous=0
 for e in events:
  assert e['start']>=previous-.0001;assert e['end']>e['start'];previous=e['end']
 assert len([e for e in events if e['type']=='music'])==5
 audio=audio_pcm(video)
 volume=subprocess.run([build.FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
 peak_db=float(re.search(r'max_volume:\s*([+-]?[0-9.]+) dB',volume.stderr).group(1))
 assert peak_db<=-.3,'Insufficient decoded audio headroom'
 rms=float(np.sqrt(np.mean(audio**2)));assert rms>.005,'Unexpected silence'
 audio_checks=[]
 if kind=='youtube':
  def digest(path):
   return subprocess.check_output([build.FF,'-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()
  received=digest(video);expected=digest(build.SOURCE)
  assert received==expected,'Full YouTube audio must be stream-copied unchanged'
  audio_checks.append({'copiedAACPayloadMatchesOriginal':True,'payloadSha256':expected.split('=')[-1]})
 else:
  # Check actual decoded output, not just WAV prep or the intended edit list.
  for e in events:
   if e['type']=='hold':continue
   margin=min(.25,e['duration']/5);duration=e['duration']-2*margin
   a=audio_pcm(build.SOURCE,e['sourceStart']+margin,duration)
   b=audio_pcm(video,e['start']+margin,duration)
   n=min(len(a),len(b));a=a[:n];b=b[:n]
   corr=float(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))
   level=float(np.sqrt(np.mean(b*b)))
   assert corr>.95,(e,corr);assert level>.002,(e,level)
   audio_checks.append({'type':e['type'],'scene':e['scene'],'sourceStart':e['sourceStart'],
    'outputStart':e['start'],'correlationToExistingAudio':corr,'rms':level})
 # Confirm real frame-to-frame movement in the artwork region during music.
 checks=[];frames=root/'qa-frames';frames.mkdir(exist_ok=True)
 samples=[1.,7.,42.,75.,111.,145.,178.,190.] if kind=='youtube' else [1.,6.,11.,16.,21.,26.,30.]
 for t in samples:
  p=frames/f'{t:05.1f}.png';build.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,p])
 music=next(e for e in events if e['type']=='music');pair=[]
 for n,t in enumerate((music['start']+1,music['start']+2)):
  p=frames/f'motion-{n}.png';build.run(['-ss',t,'-i',video,'-frames:v',1,'-update',1,p]);pair.append(Image.open(p).convert('RGB'))
 region=(160,170,860,870) if kind=='youtube' else (120,550,850,1270)
 assert ImageChops.difference(pair[0].crop(region),pair[1].crop(region)).getbbox(),'Artwork did not move'
 level_data=build.spectrum(root/'audio.wav',build.FPS[kind],plan['duration'])
 assert level_data.max()>.3 and float(level_data.std())>.02
 for c in plan['captions']:
  assert c['start']<c['end']<=plan['duration'];assert c['text'].strip()
 cmd=build.command(root,kind,plan['duration'])
 assert cmd[cmd.index('-map')+1]=='0:v:0' # No source episode video is ever mapped.
 report={'status':'technical_QA_passed_pending_user_listening_and_visual_review','kind':kind,
  'video':video.name,'sha256':build.sha(video),'bytes':video.stat().st_size,
  'resolution':list(meta['size']),'fps':meta['fps'],'duration':meta['duration'],
  'fullDecode':'PASS','sourceAndCoverHashes':'PASS','presenterImagesUsed':False,
  'studioImagesUsed':False,'voicesRegenerated':False,'decodedStereoPeakDbFS':peak_db,
  'overallRmsDbFS':round(20*np.log10(rms),2),'audioChecks':audio_checks,
  'artworkMotion':'PASS','realAudioSpectrumVariation':'PASS','speechCaptionCount':len(plan['captions']),
  'musicSamples':5,'captionTiming':'Existing estimated cues; not forced aligned',
  'copyrightCleared':False,'youtubePublished':False,'instagramPublished':False,
  'manualReview':'Extracted encoded frames require visual inspection. Aural cut-boundary/pronunciation review remains with user.'}
 (root/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['youtube','reel'],required=True);p.add_argument('--root',type=Path)
 a=p.parse_args();validate((a.root or build.REPO/f'rendered/video-006-faceless/{a.kind}').resolve(),a.kind)

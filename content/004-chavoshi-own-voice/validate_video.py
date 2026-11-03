"""Technical QA only: no claim of aural pronunciation review or rights clearance."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,wave
import imageio_ffmpeg
from PIL import Image,ImageChops,ImageStat

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
FF=imageio_ffmpeg.get_ffmpeg_exe()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--media-root',type=Path,default=REPO/'rendered/video-004-own-voice');args=p.parse_args()
 root=args.media_root.resolve();video=root/'ahangban-first-video-final.mp4'
 timeline=json.loads((root/'timeline.json').read_text());events=timeline['events']
 provenance=json.loads((root/'source-provenance.json').read_text())
 manifest=json.loads((root/'production-manifest.json').read_text())
 assert manifest['status'] in ('rendered_pending_QA','technical_QA_passed_pending_user_review')
 assert manifest['youtubePublished'] is False
 assert manifest['ownVoiceCloned'] is False and manifest['thirdPartyVoiceUpload'] is False
 assert sha(HERE/'dialogue.fa.json')==manifest['dialogueSha256']
 assert sha(video)==manifest['videoSha256']
 studio=REPO/'studio/ahangban-signature'
 for key,path in [('studioMasterSha256','master/MASTER-VIEW-001.png'),('presenterCompositeSha256','productions/HOSTS-VIEW-002.png'),
                  ('logoCoreSha256','overlays/AHANGBAN-LOGO-CORE.png'),('logoGlowSha256','overlays/AHANGBAN-LOGO-GLOW.png')]:
  assert sha(studio/path)==manifest[key]
 assert len(events)==16 and len([e for e in events if e['type']=='music'])==5
 assert len([e for e in events if e.get('speaker')=='female'])==7
 assert len([e for e in events if e.get('speaker')=='male'])==4
 for i,e in enumerate(events):
  assert e['duration']>0 and abs(e['end']-e['start']-e['duration'])<.00001
  if i:assert abs(e['start']-events[i-1]['end']-.25)<.00001
  if e['type']=='music':assert abs(e['duration']-12)<.00001
 assert abs(timeline['duration']-events[-1]['end']-.25)<.00001
 import tempfile
 import build_video as current
 assert provenance['recordingSourceSha256']==current.SOURCE_SHA
 assert sha(current.SOURCE)==current.SOURCE_SHA
 for clip in provenance['speech']:
  assert sha(root/clip['file'])==clip['sha256']
  assert sha(REPO/clip['source'])==clip['sourceSha256']
  if clip['speaker']=='male':
   assert clip['voice']=='user_recording' and clip['source']==provenance['recordingSource']
   assert clip['sourceSha256']==current.SOURCE_SHA
   assert [clip['sourceStart'],clip['sourceEnd']]==list(current.CUTS[clip['id']])
   # Re-extract and compare actual PCM to prove it is the supplied human take,
   # not an old or synthetic male clip relabelled as the user's voice.
   with tempfile.TemporaryDirectory(dir=root) as tmp:
    check=Path(tmp)/'check.wav'
    current.extract_user_turn(current.SOURCE,check,clip['sourceStart'],clip['sourceEnd'])
    with wave.open(str(check)) as a,wave.open(str(root/clip['file'])) as b:
     assert a.readframes(a.getnframes())==b.readframes(b.getnframes())
  else:
   assert clip['voice']=='voice-00' and clip['source'].startswith('rendered/video-004-own-voice/audio/')
 for source in provenance['music']:
  assert sha(root/source['file'])==source['sha256']
  blob=subprocess.check_output(['git','hash-object',str(root/source['file'])],text=True).strip()
  assert blob==source['gitBlob']
 with wave.open(str(root/'mixed.wav')) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(48000,2,2)
  assert abs(w.getnframes()/w.getframerate()-timeline['duration'])<.00001
  data=w.readframes(w.getnframes())
 for e in events:
  start=round(e['end']*48000)*4;end=round((e['end']+.25)*48000)*4
  assert not any(data[start:end]), 'Speech and music must be separated by the declared silence'
 captions=timeline['captions'];last=0
 for c in captions:
  assert c['start']>=last and c['end']>c['start'] and c['end']<=timeline['duration']
  assert any(e['type']=='speech' and e['start']<=c['start'] and c['end']<=e['end'] for e in events)
  last=c['end']
 srt=(root/'subtitles.fa.srt').read_text()
 assert srt.count(' --> ')==len(captions)
 gen=imageio_ffmpeg.read_frames(str(video));meta=next(gen);gen.close()
 assert tuple(meta['size'])==(1920,1080) and abs(meta['fps']-25)<.001
 assert abs(meta['duration']-timeline['duration'])<.15
 print('QA: inputs, voices, timeline, captions and metadata passed; decoding full MP4...',flush=True)
 decode=subprocess.run([FF,'-hide_banner','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
 assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
 peak=subprocess.run([FF,'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
 match=re.search(r'max_volume:\s*([\-\d.]+) dB',peak.stderr);assert match
 maxvolume=float(match.group(1));assert maxvolume<=-.2,f'Peak too near clipping: {maxvolume}'
 frames=root/'qa-frames';frames.mkdir(exist_ok=True)
 firstmale=next(e for e in events if e.get('speaker')=='male')
 firstmusic=next(e for e in events if e['type']=='music')
 sampletimes={'studio':6,'male':firstmale['start']+2,'music':firstmusic['start']+3,
              'recap':events[-1]['start']+3,'neon-high':1.5,'neon-low':4.5}
 for name,t in sampletimes.items():
  subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(frames/(name+'.jpg'))],check=True)
 high=Image.open(frames/'neon-high.jpg').crop((720,145,1200,280))
 low=Image.open(frames/'neon-low.jpg').crop((720,145,1200,280))
 difference=ImageStat.Stat(ImageChops.difference(high,low)).mean
 assert max(difference)>.05, 'Logo glow should vary over time'
 report={'status':'technical_QA_passed_pending_user_review','video':video.name,'videoSha256':sha(video),
  'bytes':video.stat().st_size,'duration':meta['duration'],'resolution':list(meta['size']),'fps':meta['fps'],
  'speechTurns':11,'femaleVoice':'voice-00 unchanged, new rewritten narration','maleVoice':'Actual user-recorded Sajad, four re-extracted PCM checks passed',
  'musicSamples':5,'musicSampleDuration':12,'captionCues':len(captions),'decodedPeakDbFS':maxvolume,
  'fullDecode':'passed','exactPinnedSourceBlobs':'passed','selectedSpeechHashes':'passed','nonOverlappingTimeline':'passed',
  'neonFrameMeanDifferenceRGB':difference,'captionTiming':'estimated; needs user review',
  'notVerified':['Pronunciation and phonetic accuracy','Word-level caption alignment','Third-party music/image rights','Aural take boundaries and spoken wording versus script','User final visual/audio approval'],
  'presenterMotion':'Static image, no lip sync','ownVoiceCloned':False,'thirdPartyVoiceUpload':False,'youtubePublished':False}
 (root/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 manifest['status']=report['status'];(root/'production-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print('PASS:',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()

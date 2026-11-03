"""Regression checks, never a subjective naturalness or rights certification."""
import json,unittest
from PIL import Image
import numpy as np
import build_revision as r

def load(name):return json.loads((r.HERE/name).read_text())
class RevisionTests(unittest.TestCase):
 def test_rejected_original_video_and_assets_preserved(self):
  old=json.loads((r.EPISODE/'delivery/manifest.json').read_text())
  for item in old['outputs'].values():
   self.assertEqual(r.sha(r.REPO/item['video']),item['sha256']);self.assertEqual(r.sha(r.REPO/item['cover']),item['coverSha256'])
 def test_three_short_fresh_utterances_preserve_voice_identities(self):
  report=load('delivery/voice-preview-manifest.json');self.assertEqual(len(report['timeline']),3)
  self.assertFalse(set(report['newSpeechSourceHashes'])&set(report['previousAudioSha256']))
  for row in report['timeline']:
   self.assertEqual(row['voice'],{'female':'voice-06','male':'voice-07'}[row['speaker']]);self.assertLessEqual(len(row['text'].split()),16)
   self.assertEqual(r.sha(r.HERE/'audio'/(row['id']+'.mp3')),row['sourceSha256'])
 def test_dry_speech_has_no_processing_that_masks_performance(self):
  d=load('delivery/voice-preview-manifest.json');self.assertTrue(d['previous010PerformanceRejected'])
  for flag in ('musicUsed','soundEffectsUsed','humanRecordingUsed','personalCloneUsed','voicePitchChanged','voiceSpeedChanged','internalPausesEdited','preciseEngineEmotionOrWordStressControlAvailable'):self.assertFalse(d[flag])
  self.assertEqual(r.sha(r.REPO/d['output']),d['sha256']);self.assertLess(abs(r.decode(r.REPO/d['output'])).max(),.99)
 def test_homography_maps_original_corners_without_generated_faces(self):
  dst=[(21,15),(490,25),(510,510),(15,480)];src=[(0,0),(820,0),(820,820),(0,820)];h=r.homography_inverse(dst,src)
  for (x,y),(u,v) in zip(dst,src):
   self.assertAlmostEqual((h[0]*x+h[1]*y+h[2])/(h[6]*x+h[7]*y+1),u,places=6)
   self.assertAlmostEqual((h[3]*x+h[4]*y+h[5])/(h[6]*x+h[7]*y+1),v,places=6)
  for tr in r.b.TRACKS:self.assertEqual(r.sha(r.SOURCE/tr['cover']),tr['coverSha256'])
 def test_cover_sizes_hashes_logo_and_vertical_safe_bounds(self):
  m=load('delivery/cover-manifest.json');self.assertTrue(m['originalArtworkUsed']);self.assertFalse(m['artworkRegenerated']);self.assertEqual(m['logoSha256'],r.sha(r.b.g.LOGO))
  for k,size in [('youtube',(1280,720)),('reel',(1080,1920))]:
   a=m['outputs'][k]
   with Image.open(r.REPO/a['file']) as image:self.assertEqual(image.size,size)
   self.assertEqual(r.sha(r.REPO/a['file']),a['sha256'])
  for x,y,z,h in m['outputs']['reel']['titleBoundsAtNativeSize']:
   self.assertGreaterEqual(x,88);self.assertLessEqual(z,918);self.assertGreaterEqual(y,300);self.assertLessEqual(h,1570)
 def test_background_never_recurses_or_blends_unrelated_rooms(self):
  old=r.b.background
  try:
   r.b.background=lambda *args: self.fail('Backdrop must not call overridden background')
   self.assertEqual(r.backdrop('youtube',2).size,(1920,1080))
  finally:r.b.background=old
 def test_preview_is_not_misrepresented_as_final_approved_episode(self):
  m=load('delivery/demo-manifest.json');self.assertFalse(m['fullEpisodeRebuilt']);self.assertTrue(m['previous010SpeechRejected']);self.assertTrue(m['finalUserListeningPending'])
  for f in ('humanRecordingUsed','voiceSpeedOrPitchChanged','copyrightCleared','youtubePublished','instagramPublished'):self.assertFalse(m[f])
  self.assertEqual(r.sha(r.REPO/m['video']),m['sha256']);self.assertLess(m['duration'],45)
 def test_no_narration_captions_over_music_and_contiguous_edits(self):
  p=load('delivery/demo-timeline.json');self.assertEqual(sum(e['duration'] for e in p['events'] if e['type']=='music'),22)
  self.assertTrue(all(a['end']<=c['start'] for a,c in zip(p['events'],p['events'][1:])))
  for cue in p['captions']:
   self.assertFalse(any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in p['events'] if e['type']=='music'))
  shots=r.b.make_shots(p);self.assertTrue(all(a['end']==c['start'] for a,c in zip(shots,shots[1:])))
 def test_real_fft_and_separate_depth_layer_motion(self):
  p=load('delivery/demo-timeline.json');s=next(s for s in r.b.make_shots(p) if p['events'][s['eventIndex']]['type']=='music');root=r.WORK/'youtube'
  cmd=r.shot_command(root,'youtube',s,p['events'][s['eventIndex']],root/'caption.ffconcat');graph=cmd[cmd.index('-filter_complex')+1]
  for x in ('[3:a]','showfreqs=','mode=line','[art][5:v]','12*sin(t*.38)','16*sin(t*.22)','zoompan='):self.assertIn(x,graph)
 def test_encoded_preview_qa_does_not_certify_voice_naturalness(self):
  q=load('delivery/qa-report.json');self.assertEqual(q['fullDecode'],'PASS');self.assertEqual(q['cameraAndAudioSpectrumMotion'],'PASS');self.assertLessEqual(q['decodedPeakDbFS'],-.3)
  self.assertTrue(all(a['sourceToDecodedOutputCorrelation']>.97 for a in q['audioChecks']))
  for f in ('newVoicePerformanceApproved','published','copyrightCleared','fullEpisodeRebuilt','preciseEmotionOrWordStressControl'):self.assertFalse(q[f])
if __name__=='__main__':unittest.main()

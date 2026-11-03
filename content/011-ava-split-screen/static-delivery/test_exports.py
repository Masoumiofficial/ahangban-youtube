import unittest,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class StaticExports(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=json.loads((HERE/'delivery/manifest.json').read_text())
 def test_complete_native_outputs(self):
  for k,size,fps,frames in [('youtube',[1920,1080],25,3644),('reel',[1080,1920],30,1426)]:
   q=self.m['outputs'][k];self.assertEqual(q['size'],size);self.assertEqual(q['fps'],fps);self.assertEqual(q['decodedFrames'],frames);self.assertTrue(q['fullVideoDecodePassed'])
 def test_actual_files_match_qa(self):
  for q in self.m['outputs'].values():self.assertEqual(sha(ROOT/q['file']),q['sha256'])
 def test_source_audio_is_encoded_byte_identical(self):
  for q in self.m['outputs'].values():self.assertTrue(q['exactSourceAACRetained']);self.assertTrue(q['aacPacketHash'].startswith('SHA256='))
 def test_only_female_narration(self):
  self.assertEqual(self.m['voice'],'voice-06')
  for q in self.m['outputs'].values():self.assertEqual(q['allNarrationVoice'],'voice-06');self.assertFalse(q['maleNarrationUsed'])
 def test_protected_previous_exports_unchanged(self):
  previous=json.loads((ROOT/'content/010-night-playlist/final-female/delivery/manifest.json').read_text())
  for k,v in previous['outputs'].items():self.assertEqual(sha(ROOT/v['video']),v['sha256']);self.assertEqual(self.m['outputs'][k]['sourceSha256'],v['sha256'])
 def test_static_ava_not_claimed_as_lipsync(self):
  self.assertFalse(self.m['actorAnimated']);self.assertFalse(self.m['requestedNaturalMotionDelivered']);self.assertFalse(self.m['userExplicitlyChoseStaticFallback']);self.assertTrue(self.m['staticFallbackDisclosedBeforeBuild'])
  for q in self.m['outputs'].values():self.assertFalse(q['modelInferenceExecuted']);self.assertFalse(q['lipHeadEyeListeningMotionGenerated'])
 def test_face_fixed_and_faithful(self):
  for q in self.m['outputs'].values():self.assertLess(q['fixedFaceRegionTemporalMeanDifference'],3);self.assertLess(q['meanDifferenceFromFixedPlate'],6)
 def test_original_music_panel_is_moving(self):
  for q in self.m['outputs'].values():self.assertGreater(q['musicPanelMeanDifference'],.25);self.assertTrue(q['musicPanelMotionRetained'])
 def test_full_music_durations(self):
  for k,d in [('youtube',35),('reel',12)]:
   p=json.loads((ROOT/f'content/010-night-playlist/final-female/delivery/{k}/timeline.json').read_text());songs=[e for e in p['events'] if e['type']=='music'];self.assertEqual(len(songs),3);self.assertTrue(all(e['duration']==d for e in songs));self.assertEqual(self.m['outputs'][k]['musicSecondsEach'],d)
 def test_no_speech_captions_on_music(self):
  for k in ('youtube','reel'):
   p=json.loads((HERE/f'delivery/{k}/render-plan.json').read_text());self.assertFalse(any(e['caption'] for e in p['intervals'] if e['type']=='music'))
 def test_delivery_text_discloses_static_and_website(self):
  tracks=json.loads((ROOT/'content/010-night-playlist/tracks.json').read_text())
  for k in ('youtube','reel'):
   text=(HERE/f'delivery/{k}/upload-description.txt').read_text();self.assertIn('تصویر ثابت',text);self.assertIn('ahangban.ir',text)
   for t in tracks:self.assertIn(t['url'],text)
 def test_no_clipped_duplicate_source_subtitle(self):
  self.assertTrue(self.m['outputs']['youtube']['sourceSpeechCaptionCropClean'])
  p=json.loads((HERE/'delivery/youtube/render-plan.json').read_text());self.assertTrue(p['sourceSpeechCaptionCropGuard'])
 def test_no_publication_or_user_external_job(self):
  self.assertFalse(self.m['publishAuthorized']);self.assertFalse(self.m['postedToYouTubeOrInstagram']);self.assertFalse(self.m['externalExecutionRequiredFromUser']);self.assertFalse(self.m['newTTSGenerated'])
if __name__=='__main__':unittest.main()

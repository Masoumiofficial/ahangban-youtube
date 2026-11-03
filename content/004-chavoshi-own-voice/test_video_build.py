"""Own-recording render checks, separate from model-cloning research."""
import hashlib,json,tempfile,unittest
from pathlib import Path
import build_video as build

class OwnVoiceRenderTests(unittest.TestCase):
 def test_human_source_is_exact_supplied_file(self):
  self.assertEqual(build.sha(build.SOURCE),build.SOURCE_SHA)
  self.assertEqual(set(build.CUTS),{'02','10','11','06'})
  last=0
  for start,end in build.CUTS.values():
   self.assertGreater(start,last);self.assertGreater(end,start)
   self.assertLessEqual(end,49.11);last=end
 def test_rewritten_female_audio_is_required(self):
  female=next(r for r in json.loads((build.HERE/'dialogue.fa.json').read_text()) if r['speaker']=='female')
  with tempfile.TemporaryDirectory() as temp:
   with self.assertRaisesRegex(FileNotFoundError,'old narration must not be reused'):
    build.prepare_inputs(Path(temp),[],[female])
 def test_final_command_does_not_claim_cloned_or_synthetic_sajad(self):
  with tempfile.TemporaryDirectory() as temp:
   cmd=build.command(Path(temp),199.22)
   self.assertTrue(cmd[-1].endswith('/'+build.VIDEO))
   comment=next(x for x in cmd if x.startswith('comment='))
   self.assertIn('Actual user-recorded Sajad',comment)
   self.assertIn('synthetic Ava',comment)
   self.assertNotIn('voice-02',comment)
 def test_delivered_manifest_is_real_recording_and_black_suit(self):
  manifest=json.loads((build.HERE/'delivery/production-manifest.json').read_text())
  self.assertEqual(manifest['userRecordingSha256'],build.SOURCE_SHA)
  self.assertEqual(manifest['presenterCompositeSha256'],build.sha(build.PRESENTER))
  self.assertFalse(manifest['ownVoiceCloned'])
  self.assertFalse(manifest['youtubePublished'])
  video=build.REPO/'downloads/ahangban-first-video-final.mp4'
  self.assertEqual(manifest['videoSha256'],build.sha(video))
if __name__=='__main__':unittest.main()

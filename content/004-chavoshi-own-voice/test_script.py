"""Check the current human-recording handoff, without generating any speech."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
load=lambda name:json.loads((ROOT/name).read_text())
class ScriptTests(unittest.TestCase):
 def test_recording_lines_match_full_dialogue(self):
  rows=load('dialogue.fa.json');male=load('recording-lines.fa.json')
  self.assertEqual(male,[r for r in rows if r['speaker']=='male'])
  self.assertEqual([r['id'] for r in male],['02','10','11','06'])
  self.assertEqual(len(rows),11)
  self.assertEqual(sum(r['speaker']=='female' for r in rows),7)
  for row in male:self.assertIn(row['text'],(ROOT/'recording-lines.fa.txt').read_text())
 def test_historical_slots_and_all_texts_rewritten(self):
  previous=json.loads((ROOT.parent/'003-chavoshi-studio/dialogue.fa.json').read_text())
  revised=load('dialogue.fa.json')
  self.assertEqual([(r['id'],r['speaker'],r['scene']) for r in revised],[(r['id'],r['speaker'],r['scene']) for r in previous])
  for old,new in zip(previous,revised):self.assertNotEqual(old['text'],new['text'])
 def test_plan_hashes_and_pending_audio_are_truthful(self):
  plan=load('production-plan.json')
  for key,name in [('dialogueSha256','dialogue.fa.json'),('recordingLinesSha256','recording-lines.fa.json')]:
   self.assertEqual(plan[key],hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
  for key in ('ownVoiceReceived','ownVoiceCloned','ownVoiceIntegrated','nextVideoRendered','youtubePublished'):
   self.assertFalse(plan[key])
  self.assertTrue(plan['previousRecordingScriptSuperseded'])
 def test_review_document_contains_every_line_and_five_music_cues(self):
  document=(ROOT/'script.fa.md').read_text()
  for row in load('dialogue.fa.json'):self.assertIn(row['text'],document)
  self.assertEqual(document.count('[پخش نمونهٔ ۱۲ثانیه‌ای'),5)
if __name__=='__main__':unittest.main()

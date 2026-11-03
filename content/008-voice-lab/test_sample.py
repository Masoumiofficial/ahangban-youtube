import json,unittest
import numpy as np
import build_sample as b

class VoiceLabTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((b.HERE/'sample-manifest.json').read_text())
 def test_audition_is_not_performance_approval_and_video_is_paused(self):
  self.assertTrue(self.m['selectionIsNotFullPerformanceApproval']);self.assertTrue(self.m['videoProductionPaused'])
  self.assertTrue(self.m['previous007SpeechAndHookRejected'])
  self.assertEqual(self.m['auditionSelections'],{'female':'voice-06','male':'voice-07'})
  for flag in ('humanRecordingUsed','personalCloneUsed','musicUsed','effectsUsed'):self.assertFalse(self.m[flag])
 def test_all_export_and_source_hashes(self):
  for item in self.m['outputs']:self.assertEqual(b.sha(b.REPO/item['file']),item['sha256'])
  for item in self.m['timeline']:self.assertEqual(b.sha(b.HERE/'audio'/item['file']),item['sourceSha256'])
  self.assertEqual(b.sha(b.REPO/'downloads/ahangban-voice-lab-pronunciation.mp3'),b.sha(b.HERE/'audio/female-pronunciation.mp3'))
 def test_actual_dialogue_keeps_both_fresh_voices_and_timing(self):
  actual=np.array(b.decode(b.REPO/'downloads/ahangban-voice-lab-dialogue.mp3'),dtype=float)
  self.assertLess(abs(len(actual)/(b.RATE*2)-self.m['dialogueDuration']),.01)
  self.assertLess(float(abs(actual).max()),32767)
  for item in self.m['timeline']:
   expected=np.array(b.decode(b.HERE/'audio'/item['file']),dtype=float)
   start=round(item['start']*b.RATE)*2;length=len(expected);received=actual[start:start+length]
   trim=round(.2*b.RATE)*2;expected=expected[trim:-trim];received=received[trim:-trim]
   corr=float(np.dot(expected,received)/np.sqrt(np.dot(expected,expected)*np.dot(received,received)))
   self.assertGreater(corr,.97)
 def test_question_opens_sample_not_imperative(self):
  opening=self.m['timeline'][0]['text'];self.assertTrue(opening.startswith('چرا '));self.assertIn('؟',opening)
  self.assertNotIn('فقط یکی رو انتخاب کن',opening)
  self.assertEqual([item['voice'] for item in self.m['timeline']],['voice-06','voice-07'])

if __name__=='__main__':unittest.main()

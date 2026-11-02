import json,unittest
from pathlib import Path
import numpy as np
import build_video as b
import persian_display as pd

class CosmicProductionTests(unittest.TestCase):
 def plans(self):
  return [json.loads((b.REPO/f'rendered/video-007-cosmic/{k}/timeline.json').read_text()) for k in ('youtube','reel')]
 def test_only_selected_fresh_synthetic_voices(self):
  self.assertEqual(b.AUDIO,b.HERE/'audio')
  for r in b.DIALOGUE:
   self.assertEqual(r['voice'],'voice-05' if r['speaker']=='female' else 'voice-04')
   self.assertTrue((b.AUDIO/(r['id']+'.mp3')).is_file())
 def test_speech_never_over_music(self):
  for p in self.plans():
   events=p['events']
   self.assertTrue(all(a['end']<=c['start'] for a,c in zip(events,events[1:])))
   self.assertTrue(p['allSpeechSynthetic']);self.assertFalse(p['humanRecordingUsed'])
 def test_music_lengths_and_offsets(self):
  for p in self.plans():
   events=[e for e in p['events'] if e['type']=='music'];self.assertEqual(len(events),5)
   for e,tr in zip(events,b.TRACKS):
    self.assertEqual(e['scene'],tr['id']);self.assertEqual(e['duration'],20 if p['kind']=='youtube' else 8)
    self.assertEqual(e['sourceStart'],tr['excerptStart']+(2 if p['kind']=='reel' else 0))
 def test_native_formats_and_own_audio_mapping(self):
  for k in ('youtube','reel'):
   cmd=b.command(Path('/example'),k,100)
   self.assertIn('1920x1080' if k=='youtube' else '1080x1920',cmd)
   self.assertEqual(cmd[cmd.index('-map')+1],'0:v:0');self.assertIn('1:a:0',cmd)
   self.assertIn('/example/audio.wav',cmd);self.assertNotIn(str(b.base.SOURCE),cmd)
 def test_hook_precedes_logo_slate_or_any_music(self):
  for p in self.plans():
   self.assertEqual(p['events'][0]['id'],'01');self.assertEqual(p['events'][0]['start'],0)
  reel=self.plans()[1];self.assertLess(next(e['start'] for e in reel['events'] if e['type']=='music'),8)
 def test_youtube_bloated_intro_removed(self):
  p=self.plans()[0];self.assertLess(next(e['start'] for e in p['events'] if e['type']=='music'),22)
  self.assertNotIn('02',[e.get('id') for e in p['events']]);self.assertNotIn('03',[e.get('id') for e in p['events']])
 def test_no_music_caption_or_cta_overlap(self):
  for p in self.plans():
   for cue in p['captions']+p['ctas']:
    self.assertFalse(any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in p['events'] if e['type']=='music'))
 def test_website_and_media_name_really_spoken(self):
  for p in self.plans():
   text=' '.join(e.get('text','') for e in p['events'])
   self.assertIn('رسانهٔ آهنگ‌بان',text);self.assertIn('دات آی آر',text)
 def test_all_display_glyphs_available_without_tofu(self):
  for row in b.DIALOGUE:
   for word in row['text'].split():self.assertTrue(all(g[0]!=0 for g in pd.shape(word,70)))
  for tr in b.TRACKS:self.assertTrue(all(g[0]!=0 for g in pd.shape(tr['title'],120)))
 def test_display_font_is_original_not_presentation_form_rewrite(self):
  self.assertEqual(b.sha(b.HERE/'fonts/Lalezar-Regular.ttf'),'7b80807bc831f141de0f7dcf6816412bf0c548968d548c5156ca388733390ea9')
 def test_original_logo_and_all_sources_pinned(self):
  for k in ('youtube','reel'):
   root=b.REPO/f'rendered/video-007-cosmic/{k}';prov=json.loads((root/'source-provenance.json').read_text())
   self.assertEqual(prov['logoSha256'],b.sha(b.base.LOGO));self.assertEqual(len(prov['assets']),10)
   self.assertFalse(prov['humanRecordingUsed']);self.assertFalse(prov['personalCloneUsed'])
 def test_delivery_actual_hashes_geometry_and_ai_only(self):
  manifest=json.loads((b.HERE/'delivery/manifest.json').read_text())
  self.assertTrue(manifest['allNarrationSynthetic']);self.assertFalse(manifest['humanRecordingUsed'])
  self.assertFalse(manifest['youtubePublished']);self.assertFalse(manifest['instagramPublished'])
  for kind,item in manifest['outputs'].items():
   self.assertEqual(b.sha(b.REPO/item['video']),item['sha256']);self.assertEqual(tuple(item['resolution']),b.SIZES[kind])
   qa=json.loads((b.HERE/f'delivery/{kind}/qa-report.json').read_text())
   self.assertTrue(all(c['decodedOutputToFreshPreparedAudioCorrelation']>.97 for c in qa['actualDecodedAudioChecks']))
 def test_edited_chapters_each_ten_seconds_minimum(self):
  manifest=json.loads((b.HERE/'delivery/manifest.json').read_text());lines=(b.HERE/'delivery/youtube/chapters.txt').read_text().splitlines()
  times=[int(s.split()[0].split(':')[0])*60+int(s.split()[0].split(':')[1]) for s in lines]
  self.assertEqual(times[0],0);self.assertGreaterEqual(len(times),3)
  self.assertTrue(all(c-a>=10 for a,c in zip(times,times[1:]+[manifest['outputs']['youtube']['duration']])))

if __name__=='__main__':unittest.main()

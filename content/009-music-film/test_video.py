import json,unittest
from PIL import Image
import build_video as b

class MusicFilmTests(unittest.TestCase):
 def plan(self,k):return json.loads((b.REPO/f'rendered/video-009-music-film/{k}/timeline.json').read_text())
 def test_approved_source_performances_identical(self):
  old=json.loads((b.HERE.parent/'008-voice-lab/sample-manifest.json').read_text())
  for s in old['timeline']:
   id='01' if s['speaker']=='female' else '02'
   self.assertEqual(b.sha(b.AUDIO/(id+'.mp3')),s['sourceSha256'])
  review=json.loads((b.HERE/'voice-approval.json').read_text());self.assertTrue(review['videoProductionAuthorized'])
 def test_only_approved_voice_identities_and_no_human_fallback(self):
  for row in b.DIALOGUE:
   self.assertEqual(row['voice'],'voice-06' if row['speaker']=='female' else 'voice-07')
   self.assertTrue((b.AUDIO/(row['id']+'.mp3')).is_file())
  for k in ('youtube','reel'):
   p=self.plan(k);self.assertTrue(p['allNarrationSynthetic']);self.assertFalse(p['humanRecordingUsed']);self.assertFalse(p['voicePitchOrSpeedChanged'])
 def test_music_genuinely_longer(self):
  for k,d in [('youtube',30),('reel',12)]:
   events=[e for e in self.plan(k)['events'] if e['type']=='music']
   self.assertEqual(len(events),5);self.assertTrue(all(e['duration']==d for e in events))
   self.assertEqual(sum(e['duration'] for e in events),150 if k=='youtube' else 60)
 def test_question_and_fast_music_entry(self):
  for k in ('youtube','reel'):
   p=self.plan(k);self.assertTrue(p['events'][0]['text'].startswith('چرا '));self.assertIn('؟',p['events'][0]['text'])
   self.assertLess(next(e['start'] for e in p['events'] if e['type']=='music'),12)
 def test_music_never_has_narration_captions_or_ctas(self):
  for k in ('youtube','reel'):
   p=self.plan(k);self.assertTrue(all(a['end']<=c['start'] for a,c in zip(p['events'],p['events'][1:])))
   for cue in p['captions']+p['ctas']:
    self.assertFalse(any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in p['events'] if e['type']=='music'))
 def test_music_windows_come_from_original_files(self):
  for k in ('youtube','reel'):
   for e,t in zip([e for e in self.plan(k)['events'] if e['type']=='music'],b.TRACKS):
    self.assertEqual(e['sourceFile'],t['file']);self.assertEqual(e['sourceStart'],t['excerptStart']+(2 if k=='reel' else 0))
 def test_frame_quantized_edits_are_contiguous(self):
  for k in ('youtube','reel'):
   p=self.plan(k);shots=b.make_shots(p);self.assertTrue(all(a['end']==c['start'] for a,c in zip(shots,shots[1:])))
   self.assertLess(abs(sum(s['frames'] for s in shots)/b.FPS[k]-p['duration']),.025)
   self.assertEqual(sum(p['events'][s['eventIndex']]['type']=='music' for s in shots),20 if k=='youtube' else 15)
 def test_real_spectrum_and_native_render_not_random_bars(self):
  for k in ('youtube','reel'):
   root=b.REPO/f'rendered/video-009-music-film/{k}';p=self.plan(k);s=next(s for s in b.make_shots(p) if p['events'][s['eventIndex']]['type']=='music')
   cmd=b.shot_command(root,k,s,p['events'][s['eventIndex']],root/'dummy.ffconcat');graph=cmd[cmd.index('-filter_complex')+1]
   self.assertIn('[3:a]',graph);self.assertIn('showfreqs=',graph);self.assertIn('zoompan=',graph)
   self.assertIn('1080x1920' if k=='reel' else '1920x1080',graph);self.assertIn('light-wipe.png',' '.join(cmd))
 def test_glyphs_and_caption_safe_bounds(self):
  for k in ('youtube','reel'):
   root=b.REPO/f'rendered/video-009-music-film/{k}';p=self.plan(k);film=b.Artwork(k,root,p)
   for cue in p['captions']:
    bounds=film.caption_image(cue['text']).getbbox();self.assertIsNotNone(bounds)
    if k=='reel':self.assertGreaterEqual(bounds[0],88);self.assertLessEqual(bounds[2],920);self.assertLessEqual(bounds[3],1518)
   for t in b.TRACKS:self.assertTrue(all(g[0]!=0 for g in b.pd.shape(t['title'],100)))
 def test_brand_really_spoken_and_official_logo_unchanged(self):
  for k in ('youtube','reel'):
   text=' '.join(e.get('text','') for e in self.plan(k)['events']);self.assertIn('رسانهٔ آهنگ‌بان',text);self.assertIn('دات آی آر',text)
   prov=json.loads((b.REPO/f'rendered/video-009-music-film/{k}/source-provenance.json').read_text());self.assertEqual(b.sha(b.g.LOGO),prov['logoSha256'])
 def test_delivery_hashes_and_actual_decoded_audio_pass(self):
  m=json.loads((b.HERE/'delivery/manifest.json').read_text())
  for k,item in m['outputs'].items():
   self.assertEqual(b.sha(b.REPO/item['video']),item['sha256']);self.assertEqual(tuple(item['resolution']),b.SIZES[k])
   q=json.loads((b.HERE/f'delivery/{k}/qa-report.json').read_text());self.assertEqual(q['fullDecode'],'PASS')
   self.assertTrue(all(c['sourceToDecodedOutputCorrelation']>.97 for c in q['decodedAudioChecks']))
   self.assertLessEqual(q['decodedPeakDbFS'],-.3)
 def test_no_publication_or_rights_guarantee(self):
  m=json.loads((b.HERE/'delivery/manifest.json').read_text())
  for flag in ('youtubePublished','instagramPublished','copyrightCleared','humanRecordingUsed','personalCloneUsed','voicePitchOrSpeedChanged'):self.assertFalse(m[flag])
 def test_publish_chapters_minimum_ten_seconds(self):
  lines=(b.HERE/'delivery/youtube/chapters.txt').read_text().splitlines();times=[int(l.split()[0].split(':')[0])*60+int(l.split()[0].split(':')[1]) for l in lines]
  self.assertEqual(times[0],0);self.assertGreaterEqual(len(times),3)
  self.assertTrue(all(z-a>=10 for a,z in zip(times,times[1:]+[self.plan('youtube')['duration']])))

if __name__=='__main__':unittest.main()

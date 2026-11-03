"""Native-output, timeline and independent decoded-QA regression checks."""
import json,unittest
from pathlib import Path
import build_video as b

def load(name):return json.loads((b.HERE/name).read_text())
class NightVideoTests(unittest.TestCase):
 def test_three_real_music_windows_and_timing(self):
  for k,d in [('youtube',35),('reel',12)]:
   p=load(f'delivery/{k}/timeline.json');events=[e for e in p['events'] if e['type']=='music']
   self.assertEqual(len(events),3);self.assertEqual(sum(e['duration'] for e in events),3*d)
   for e,t in zip(events,b.TRACKS):
    self.assertEqual(e['duration'],d);self.assertEqual(e['sourceFile'],t['file']);self.assertEqual(e['title'],t['title'])
    self.assertEqual(e['sourceStart'],t['excerptStart'] if k=='youtube' else t['verticalExcerptStart'])
 def test_question_led_short_opening_and_spoken_brand(self):
  for k,entryLimit in [('youtube',14),('reel',7)]:
   p=load(f'delivery/{k}/timeline.json');self.assertIn('؟',p['events'][0]['text']);self.assertLess(next(e['start'] for e in p['events'] if e['type']=='music'),entryLimit)
   words=' '.join(e.get('text','') for e in p['events']);self.assertIn('رسانهٔ آهنگ‌بان',words);self.assertIn('دات آی آر',words)
 def test_no_speech_captions_or_ctas_over_music(self):
  for k in ('youtube','reel'):
   p=load(f'delivery/{k}/timeline.json');self.assertTrue(all(a['end']<=c['start'] for a,c in zip(p['events'],p['events'][1:])))
   for cue in p['captions']+p['ctas']:
    self.assertFalse(any(max(cue['start'],e['start'])<min(cue['end'],e['end']) for e in p['events'] if e['type']=='music'))
 def test_frame_quantized_contiguous_shots(self):
  for k in ('youtube','reel'):
   p=load(f'delivery/{k}/timeline.json');shots=b.make_shots(p)
   self.assertTrue(all(a['end']==c['start'] for a,c in zip(shots,shots[1:])))
   self.assertLess(abs(sum(s['frames'] for s in shots)/b.FPS[k]-p['duration']),.025)
   self.assertEqual(sum(p['events'][s['eventIndex']]['type']=='music' for s in shots),12 if k=='youtube' else 9)
 def test_actual_spectrum_and_native_render_commands(self):
  for k in ('youtube','reel'):
   p=load(f'delivery/{k}/timeline.json');root=b.REPO/f'rendered/video-010-night-playlist/{k}'
   s=next(s for s in b.make_shots(p) if p['events'][s['eventIndex']]['type']=='music');e=p['events'][s['eventIndex']]
   cmd=b.shot_command(root,k,s,e,root/'dummy.ffconcat');graph=cmd[cmd.index('-filter_complex')+1]
   for part in ('[3:a]','showfreqs=','zoompan=','1080x1920' if k=='reel' else '1920x1080'):self.assertIn(part,graph)
 def test_captions_fit_vertical_safe_area(self):
  for k in ('youtube','reel'):
   p=load(f'delivery/{k}/timeline.json');film=b.Artwork(k,b.REPO/f'rendered/video-010-night-playlist/{k}',p)
   for cue in p['captions']:
    bb=film.caption_image(cue['text']).getbbox();self.assertIsNotNone(bb)
    if k=='reel':self.assertGreaterEqual(bb[0],88);self.assertLessEqual(bb[2],920);self.assertLessEqual(bb[3],1518)
   for t in b.TRACKS:self.assertTrue(all(g[0]!=0 for g in b.pd.shape(t['title'],100)))
 def test_outputs_match_qa_hashes_resolutions_and_audio(self):
  m=load('delivery/manifest.json')
  for k,item in m['outputs'].items():
   self.assertEqual(b.sha(b.REPO/item['video']),item['sha256']);self.assertEqual(item['resolution'],list(b.SIZES[k]));self.assertEqual(item['fps'],b.FPS[k])
   q=load(f'delivery/{k}/qa-report.json');self.assertEqual(q['fullDecode'],'PASS');self.assertLessEqual(q['decodedPeakDbFS'],-.3)
   self.assertTrue(all(x['sourceToDecodedOutputCorrelation']>.97 for x in q['decodedAudioChecks']))
   self.assertEqual(q['encodedCameraAndSpectrumMotion'],'PASS');self.assertFalse(q['voicePitchOrSpeedChanged'])
 def test_logo_and_original_supplied_cover_provenance(self):
  for k in ('youtube','reel'):
   p=load(f'delivery/{k}/source-provenance.json');self.assertEqual(b.sha(b.g.LOGO),p['logoSha256']);self.assertEqual(p['sourceCommit'],b.MANIFEST['sourceCommit'])
   self.assertEqual(len(p['assets']),6)
   for e in p['environmentPlates']:self.assertEqual(b.sha(b.REPO/e['path']),e['sha256'])
 def test_chapters_and_all_three_user_links(self):
  dest=b.HERE/'delivery/youtube';times=[]
  for line in (dest/'chapters.txt').read_text().splitlines():
   mm,ss=line.split()[0].split(':');times.append(int(mm)*60+int(ss))
  self.assertEqual(times[0],0);self.assertEqual(len(times),5)
  self.assertTrue(all(z-a>=10 for a,z in zip(times,times[1:]+[load('delivery/youtube/timeline.json')['duration']])) )
  text=(dest/'upload-description.txt').read_text()
  for t in b.TRACKS:self.assertIn(t['url'],text);self.assertIn(t['title'],text)
 def test_no_publication_or_rights_claim(self):
  m=load('delivery/manifest.json');self.assertTrue(m['finalUserListeningPending'])
  for flag in ('publishAuthorized','youtubePublished','instagramPublished','copyrightCleared','humanRecordingUsed','personalCloneUsed','voicePitchOrSpeedChanged'):self.assertIs(m[flag],False)

if __name__=='__main__':unittest.main()

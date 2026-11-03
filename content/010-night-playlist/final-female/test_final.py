"""Female-only delivery regression and source checks; not subjective speech QA."""
import json,unittest
import numpy as np
from PIL import Image
import build_final as f

def load(path):return json.loads((f.HERE/path).read_text())
class FemaleFinalTests(unittest.TestCase):
 def test_user_casting_and_publication_scope(self):
  m=load('delivery/manifest.json');self.assertTrue(m['femaleOnlyAuthorizedByUser']);self.assertTrue(m['visualStyleApprovedByUser']);self.assertTrue(m['coversApprovedByUser'])
  for flag in ['maleNarrationUsed','voiceSpeedOrPitchChanged','humanRecordingUsed','personalCloneUsed','publishAuthorized','youtubePublished','instagramPublished','copyrightCleared']:self.assertFalse(m[flag])
 def test_all_eight_sources_are_female06_and_hash_locked(self):
  self.assertEqual(len(f.ROWS),8)
  for row in f.ROWS:
   self.assertEqual(row['speaker'],'female');self.assertEqual(row['voice'],'voice-06');self.assertEqual(f.sha(f.AUDIO/row['file']),row['sha256'])
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/source-provenance.json');self.assertFalse(p['maleNarrationUsed'])
   self.assertTrue(all(r['speaker']=='female' and r['voice']=='voice-06' for r in p['speech']))
 def test_reviewed_female_performances_reused_exactly(self):
  rows=[r for r in f.ROWS if r['exactReviewedPerformanceReuse']];self.assertEqual({r['id'] for r in rows},{'hook','transition'})
  for row in rows:self.assertEqual(f.sha(f.REPO/row['reviewedSource']),f.sha(f.AUDIO/row['file']))
 def test_name_correction_is_explicit_not_a_claim_of_listening(self):
  row=next(r for r in f.ROWS if r['id']=='intro');self.assertIn('سیاوَش قُمیشی',row['ttsText']);self.assertNotIn('ساوش',row['ttsText']);self.assertNotIn('قَمیشی',row['ttsText'])
  p=load('delivery/youtube/source-provenance.json')['pronunciationCorrection'];self.assertFalse(p['auralVerificationByAgent']);self.assertTrue(p['wholeUtteranceRegenerated'])
 def test_approved_covers_and_old_deliveries_are_byte_identical(self):
  m=load('delivery/manifest.json')
  for kind,a in m['outputs'].items():
   self.assertEqual(f.sha(f.REPO/a['cover']),f.sha(f.COVERS[kind]));self.assertEqual(f.sha(f.REPO/a['cover']),a['coverSha256'])
  for old in [f.EPISODE/'delivery/manifest.json',f.r.HERE/'delivery/demo-manifest.json']:
   j=json.loads(old.read_text())
   if 'outputs' in j:
    for a in j['outputs'].values():self.assertEqual(f.sha(f.REPO/a['video']),a['sha256'])
   else:self.assertEqual(f.sha(f.REPO/j['video']),j['sha256'])
 def test_full_music_lengths_not_preview_windows(self):
  for kind,d in [('youtube',35),('reel',12)]:
   p=load(f'delivery/{kind}/timeline.json');music=[e for e in p['events'] if e['type']=='music'];self.assertEqual(len(music),3);self.assertEqual(sum(e['duration'] for e in music),3*d)
   for e,tr in zip(music,f.b.TRACKS):
    self.assertEqual(e['duration'],d);self.assertEqual(e['sourceFile'],tr['file']);self.assertEqual(e['sourceStart'],tr['excerptStart'] if kind=='youtube' else tr['verticalExcerptStart'])
 def test_no_speech_or_captions_over_music(self):
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/timeline.json');self.assertTrue(all(a['end']<=z['start'] for a,z in zip(p['events'],p['events'][1:])))
   for c in p['captions']:
    self.assertFalse(any(max(c['start'],e['start'])<min(c['end'],e['end']) for e in p['events'] if e['type']=='music'))
 def test_normalization_never_changes_duration_or_word_timing(self):
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/source-provenance.json')
   for row in p['speech']:
    raw=f.r.decode(f.AUDIO/row['file']);norm=f.b.pcm(f.WORK/kind/'normalized'/(row['id']+'.wav'))
    self.assertEqual(raw.shape,norm.shape);self.assertLess(np.max(abs(raw*row['constantGain']-norm)),2/32768)
 def test_native_exports_and_independent_audio_qa(self):
  m=load('delivery/manifest.json')
  for kind,a in m['outputs'].items():
   self.assertEqual(a['resolution'],list(f.b.SIZES[kind]));self.assertEqual(a['fps'],f.b.FPS[kind]);self.assertEqual(f.sha(f.REPO/a['video']),a['sha256'])
   q=load(f'delivery/{kind}/qa-report.json');self.assertEqual(q['fullDecode'],'PASS');self.assertLessEqual(q['decodedPeakDbFS'],-.3);self.assertEqual(q['encodedCameraAndRealFFTMovement'],'PASS');self.assertTrue(all(x['sourceToDecodedOutputCorrelation']>.97 for x in q['audioChecks']))
 def test_contiguous_native_shots_and_actual_fft_graph(self):
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/timeline.json');shots=f.b.make_shots(p);self.assertTrue(all(a['end']==z['start'] for a,z in zip(shots,shots[1:])));self.assertLess(abs(sum(s['frames'] for s in shots)/f.b.FPS[kind]-p['duration']),.025)
   s=next(s for s in shots if p['events'][s['eventIndex']]['type']=='music');cmd=f.r.shot_command(f.WORK/kind,kind,s,p['events'][s['eventIndex']],f.WORK/kind/'dummy.ffconcat');graph=cmd[cmd.index('-filter_complex')+1]
   for part in ['[3:a]','showfreqs=','mode=line','zoompan=','[art][5:v]']:self.assertIn(part,graph)
 def test_captions_fit_vertical_safe_area_and_brand_is_spoken(self):
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/timeline.json');film=f.FinalArtwork(kind,f.WORK/kind,p)
   words=' '.join(e.get('text','') for e in p['events']);self.assertIn('رسانهٔ آهنگ‌بان',words);self.assertIn('دات آی آر',words);self.assertIn('؟',p['events'][0]['text'])
   for c in p['captions']:
    bb=film.caption_image(c['text']).getbbox();self.assertIsNotNone(bb)
    if kind=='reel':self.assertGreaterEqual(bb[0],88);self.assertLessEqual(bb[2],920);self.assertLessEqual(bb[3],1518)
 def test_chapters_have_real_boundaries_and_all_user_links(self):
  dest=f.HERE/'delivery/youtube';times=[]
  for line in (dest/'chapters.txt').read_text().splitlines():
   mm,ss=line.split()[0].split(':');times.append(int(mm)*60+int(ss))
  self.assertEqual(times[0],0);self.assertGreaterEqual(len(times),4);self.assertTrue(all(z-a>=10 for a,z in zip(times,times[1:]+[load('delivery/youtube/timeline.json')['duration']])) )
  for t in f.b.TRACKS:self.assertIn(t['url'],(dest/'upload-description.txt').read_text())
 def test_original_logo_and_source_assets_remain_pinned(self):
  for kind in ['youtube','reel']:
   p=load(f'delivery/{kind}/source-provenance.json');self.assertEqual(p['logoSha256'],f.sha(f.b.g.LOGO));self.assertEqual(p['sourceCommit'],f.b.MANIFEST['sourceCommit'])
   for a in p['assets']:self.assertEqual(f.sha(f.b.SOURCE/a['file']),a['sha256'])
 def test_final_listening_not_falsely_certified(self):
  m=load('delivery/manifest.json');self.assertTrue(m['finalUserListeningPending']);self.assertFalse(m['nameIntroductionAudio']['aurallyVerifiedByAgent'])
  for kind in ['youtube','reel']:
   q=load(f'delivery/{kind}/qa-report.json');self.assertTrue(q['finalUserListeningPending']);self.assertFalse(q['pronunciationAurallyVerifiedByAgent'])
if __name__=='__main__':unittest.main()

"""Source/script/timeline checks; not a subjective listening approval."""
import hashlib,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
def load(p):return json.loads((HERE/p).read_text())
class NightPlanTests(unittest.TestCase):
 def test_authorization_never_implies_publication_or_rights(self):
  p=load('production-plan.json');self.assertTrue(p['topicApproved'] and p['productionAuthorized'])
  for k in ('publishAuthorized','published','copyrightCleared','speechOverMusic','officialLogoChanged','subscriptionPurchased','speechSpeedOrPitchChanges'):self.assertIs(p[k],False,k)
 def test_three_distinct_artists_and_corrected_first_title(self):
  t=load('tracks.json');self.assertEqual(len(t),3);self.assertEqual(len({x['artist'] for x in t}),3)
  self.assertEqual(t[0]['title'],'تو بارون که رفتی')
  self.assertIn('تو بارون که رفتی',load('dialogue.fa.json')[0]['text'])
  for tr in t:
   self.assertFalse(tr['rightsCleared']);self.assertLessEqual(tr['excerptStart']+35,tr['sourceDurationSeconds']);self.assertLessEqual(tr['verticalExcerptStart']+12,tr['sourceDurationSeconds'])
 def test_pinned_sources_and_user_web_links(self):
  m=load('source-manifest.json');self.assertEqual(len(m['assets']),6);self.assertEqual(len(m['sourceCommit']),40)
  for x in m['assets']:
   p=REPO/'rendered/video-010-night-playlist/source-media'/x['file'];data=p.read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),x['sha256']);self.assertEqual(len(data),x['bytes'])
   self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),x['gitBlob'])
  self.assertEqual(m['userSuppliedWebLinks'],[t['url'] for t in load('tracks.json')]);self.assertFalse(m['webPagesFetched'])
 def test_fresh_approved_voice_identity_audio_and_brand(self):
  count=0
  for file in ('dialogue.fa.json','dialogue.vertical.fa.json'):
   rows=load(file)
   for row in rows:
    self.assertEqual(row['voice'],{'female':'voice-06','male':'voice-07'}[row['speaker']]);self.assertTrue(row['audioGenerated']);count+=1
    self.assertEqual(hashlib.sha256((HERE/'audio'/(row['id']+'.mp3')).read_bytes()).hexdigest(),row['audioSha256'])
   text=' '.join(r['text'] for r in rows);self.assertIn('آهنگ‌بان',text);self.assertIn('دات آی آر',text);self.assertIn('؟',rows[0]['text']);self.assertIn('کامنت',text)
  self.assertEqual(count,8)
 def test_source_audit_does_not_claim_human_listening(self):
  a=load('source-audit.json');self.assertTrue(a['proposedTrackAudioFound']);self.assertTrue(a['proposedTrackCoversFound']);self.assertFalse(a['proposedTracksListenedTo'])
 def test_generated_background_hash(self):
  b=load('source-audit.json')['background'];self.assertEqual(hashlib.sha256((HERE/b['path']).read_bytes()).hexdigest(),b['sha256'])
 def test_native_resolution_targets(self):
  self.assertEqual(load('production-plan.json')['nativeSizes'],{'youtube':[1920,1080],'vertical':[1080,1920]})

if __name__=='__main__':unittest.main()

"""Preproduction checks, NOT rendered-video or listening QA."""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load(name):
    return json.loads((HERE/name).read_text())

class NightPlanTests(unittest.TestCase):
    def test_authorization_and_truthful_pending_state(self):
        p=load('production-plan.json')
        self.assertTrue(p['topicApproved'] and p['productionAuthorized'])
        for k in ('publishAuthorized','published','youtubeComplete','verticalComplete','newVoiceAudioGenerated','copyrightCleared'):
            self.assertIs(p[k],False,k)
        self.assertTrue(p['timingsAreEstimates'])

    def test_three_distinct_artists_without_invented_sources_or_offsets(self):
        tracks=load('tracks.json')
        self.assertEqual(len(tracks),3)
        self.assertEqual(len({t['artist'] for t in tracks}),3)
        for t in tracks:
            for k in ('audioPath','coverPath','sha256','excerptStartSeconds'):
                self.assertIsNone(t[k])
            self.assertFalse(t['rightsCleared'])
        audit=load('source-audit.json')
        self.assertFalse(audit['proposedTracksListenedTo'])
        self.assertFalse(audit['proposedTrackAudioFound'])

    def test_dialogue_preserves_selected_voice_references_and_brand(self):
        for file in ('dialogue.fa.json','dialogue.vertical.fa.json'):
            rows=load(file)
            for row in rows:
                self.assertEqual(row['voice'],{'female':'voice-06','male':'voice-07'}[row['speaker']])
                self.assertFalse(row['audioGenerated'])
            text=' '.join(r['text'] for r in rows)
            self.assertIn('آهنگ‌بان',text)
            self.assertIn('دات آی آر',text)
            self.assertIn('؟',rows[0]['text'])
            self.assertIn('کامنت',text)

    def test_native_targets_and_production_boundaries(self):
        p=load('production-plan.json')
        self.assertEqual(p['nativeSizes'],{'youtube':[1920,1080],'vertical':[1080,1920]})
        self.assertGreaterEqual(p['musicSecondsEach']['youtube'],30)
        self.assertTrue(p['faceless'])
        for k in ('speechOverMusic','speechSpeedOrPitchChanges','officialLogoChanged','subscriptionPurchased'):
            self.assertIs(p[k],False)

    def test_background_matches_recorded_hash_and_preview_exists(self):
        import hashlib
        bg=load('source-audit.json')['background']
        self.assertEqual(hashlib.sha256((HERE/bg['path']).read_bytes()).hexdigest(),bg['sha256'])
        preview=HERE/'delivery/opening-concept.jpg'
        self.assertTrue(preview.is_file())
        self.assertEqual(preview.read_bytes()[:2],b'\xff\xd8')
        self.assertIn('نه ویدیوی نهایی',(HERE/'build_preview.py').read_text())

if __name__=='__main__': unittest.main()

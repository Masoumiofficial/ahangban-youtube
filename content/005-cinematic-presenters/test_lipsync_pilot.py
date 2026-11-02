import json, unittest
from pathlib import Path
from unittest.mock import patch
import prepare_lipsync_pilot as pilot

class LocalPilotTests(unittest.TestCase):
    def test_route_respects_no_subscription_decision(self):
        route=json.loads((pilot.HERE/'local-route.json').read_text())
        for key in ('subscriptionAllowed','paidServiceAuthorized','paidComputeAuthorized',
                    'freeTrialOrPaymentCardAuthorized','thirdPartyFaceOrAudioUploadAuthorized',
                    'automaticNetworkDownload','modelInferenceExecuted','thirdPartyUploadExecuted'):
            self.assertIs(route[key],False,key)
    def test_uses_existing_speech_windows_for_both_hosts(self):
        timeline=json.loads(pilot.TIMELINE.read_text())
        jobs=pilot.pilot_jobs(timeline)
        self.assertEqual({j['speaker'] for j in jobs},{'male','female'})
        self.assertEqual([j['id'] for j in jobs],['02','05'])
        for job in jobs:
            event=next(e for e in timeline['events'] if e.get('id')==job['id'])
            self.assertEqual(job['start'],event['start'])
            self.assertLessEqual(job['end'],event['end'])
            self.assertGreater(job['end']-job['start'],1)
            self.assertLess(job['end']-job['start'],8)
    def test_public_standalone_face_voice_exports_are_rejected(self):
        with patch.object(pilot.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'ignored rendered'):
                pilot.prepare(pilot.REPO/'downloads/unapproved-lipsync-inputs')
            run.assert_not_called()
    def test_draft_face_contexts_are_in_source_and_separate(self):
        for roi in pilot.ROIS.values():
            left,top,right,bottom=roi
            self.assertTrue(0<=left<right<=1)
            self.assertTrue(0<=top<bottom<=1)
        self.assertLess(pilot.ROIS['male'][2],pilot.ROIS['female'][0])

if __name__=='__main__':unittest.main()

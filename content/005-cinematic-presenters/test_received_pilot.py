import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
import review_received_pilot as review

class ReceivedPilotTests(unittest.TestCase):
 def test_rejects_wrong_git_blob_before_extracting(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/'x.zip';p.write_bytes(b'not a real archive')
   with self.assertRaisesRegex(ValueError,'GitHub blob'):
    review.unpack(p,root,'0'*40)
 def test_rejects_unknown_or_traversal_entries(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/'x.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('../escape.txt','no')
   data=p.read_bytes();blob=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
   with self.assertRaisesRegex(ValueError,'Unexpected ZIP'):
    review.unpack(p,root,blob)
   self.assertFalse((root.parent/'escape.txt').exists())
 def test_review_is_not_full_episode_or_user_quality_approval(self):
  report=json.loads((review.camera.HERE/'received-pilot/review-report.json').read_text())
  for key in ('userApproval','lipSyncPhoneticOrAuralApproval','fullEpisodeRenderedWithLipSync',
              'headOrBodyAnimation','newCameraPerspective','agentExecutedModelInference','youtubePublished'):
   self.assertFalse(report[key],key)
  self.assertEqual(report['sourceGitBlob'],review.BLOB)
  for check in report['checks']:
   self.assertGreater(check['audioCheck']['zeroLagCorrelation'],.98)
  preview=review.REPO/'downloads'/report['preview']
  self.assertEqual(review.sha(preview),report['previewSha256'])
 def test_male_refinement_is_small_and_does_not_cover_eyes(self):
  settings=json.loads((review.camera.HERE/'colab/pilot-settings.json').read_text())
  reference,mask=review.reference_and_mask(settings,(1280,720))
  left,top,right,bottom=mask.getbbox()
  self.assertLess(right-left,100);self.assertLess(bottom-top,60)
  self.assertGreater(top,200)
  self.assertEqual(reference.size,(1280,720))

if __name__=='__main__':unittest.main()

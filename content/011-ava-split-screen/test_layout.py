import unittest,json,hashlib,importlib.util
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('ava_layout',HERE/'build_layout.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Layout(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=json.loads((HERE/'layout-manifest.json').read_text())
 def test_three_native_portrait_stills(self):
  self.assertEqual(len(self.m['outputs']),3)
  for row in self.m['outputs']:
   p=ROOT/row['path']
   with Image.open(p) as image:self.assertEqual(image.size,(1080,1920))
   self.assertEqual(sha(p),row['sha256'])
 def test_only_original_selected_tracks(self):
  self.assertEqual([r['track'] for r in self.m['outputs']],[t['id'] for t in b.TRACKS])
  for row,t in zip(self.m['outputs'],b.TRACKS):self.assertEqual(sha(b.SOURCE/t['cover']),row['coverSourceSha256']);self.assertEqual(row['coverSourceSha256'],t['coverSha256'])
 def test_unchanged_protected_masters_and_previous_deliveries(self):
  for path,s in self.m['protectedUnchanged'].items():self.assertEqual(sha(ROOT/path),s,path)
 def test_original_ava_reference_files_unchanged(self):
  lock=json.loads((ROOT/'studio/ahangban-signature/Presenters/character-lock.json').read_text())
  for r in lock['characters'][0]['references']:self.assertEqual(sha(ROOT/'studio/ahangban-signature'/r['path']),r['sha256'])
 def test_generated_actor_honest_provenance(self):
  self.assertTrue(self.m['actorAIgenerated']);self.assertTrue(self.m['userFaceApprovalPending']);self.assertTrue(self.m['originalFacePixelsNotClaimed']);self.assertEqual(sha(b.ACTOR),self.m['actorSourceSha256'])
 def test_chroma_removed_without_transparent_face(self):
  alpha=b.key_actor().getchannel('A');self.assertEqual(alpha.getpixel((0,0)),0);self.assertEqual(alpha.getpixel((512,280)),255)
 def test_no_animation_audio_or_publication_claim(self):
  self.assertEqual(self.m['status'],'STATIC_LAYOUT_ONLY_NOT_ANIMATED_VIDEO')
  for field in ('audioGenerated','lipSyncGenerated','headEyeOrBodyAnimationGenerated','publishAuthorized','newRoomGenerated'):self.assertFalse(self.m[field])
 def test_split_matches_reference_ratio_approximately(self):
  self.assertLess(abs(self.m['splitY']/1920-.533),.005)
if __name__=='__main__':unittest.main()

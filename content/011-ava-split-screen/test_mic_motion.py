import unittest,json,hashlib,zipfile,wave,io,ast,sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
import build_layout as b
import build_mic_revision as r
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class MicMotion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((HERE/'layout-v2-manifest.json').read_text());cls.bundle=json.loads((HERE/'motion/bundle.json').read_text());cls.z=ROOT/cls.bundle['path']
 def test_approved_actor_pixels_preserved(self):
  self.assertEqual(sha(b.ACTOR),'68854d222a57969ff89567530f8b4c8202d4f8b8855acac96a23e7628e861adf')
  self.assertEqual(r.studio_panel().crop(r.FACE).tobytes(),b.studio_panel().crop(r.FACE).tobytes())
  self.assertTrue(self.m['userApprovedFaceAndLayout']);self.assertFalse(self.m['userFaceApprovalPending'])
 def test_previous_layouts_not_overwritten(self):
  for path,s in self.m['previousLayoutOutputsUnchanged'].items():self.assertEqual(sha(ROOT/path),s)
 def test_original_protected_assets_preserved(self):
  for path,s in self.m['protectedUnchanged'].items():self.assertEqual(sha(ROOT/path),s)
 def test_gallery_above_prop_mask_unchanged(self):
  before=Image.open(b.STUDIO).convert('RGBA').crop(r.BOX)
  self.assertEqual(before.crop((0,0,960,372)).tobytes(),r.clean_studio().crop((0,0,960,372)).tobytes())
 def test_new_three_outputs_native_and_same_upper_panel(self):
  old=json.loads((HERE/'layout-manifest.json').read_text())['outputs']
  for a,z in zip(old,self.m['outputs']):
   self.assertEqual(sha(ROOT/z['path']),z['sha256'])
   with Image.open(ROOT/a['path']) as ai,Image.open(ROOT/z['path']) as zi:
    self.assertEqual(zi.size,(1080,1920));self.assertEqual(ai.crop((0,0,1080,1016)).tobytes(),zi.crop((0,0,1080,1016)).tobytes())
 def test_mic_no_face_occlusion_or_green_spill(self):
  mic=r.microphone();a=np.asarray(mic).astype(int);visible=a[:,:,3]>220
  self.assertLessEqual(int((a[:,:,1]-np.maximum(a[:,:,0],a[:,:,2]))[visible].max()),4)
  self.assertGreater(435,r.FACE[3])
 def test_input_bundle_integrity_and_approved_face(self):
  self.assertEqual(sha(self.z),self.bundle['sha256'])
  with zipfile.ZipFile(self.z) as z:
   m=json.loads(z.read('pilot-inputs.json'));self.assertEqual(hashlib.sha256(z.read(m['modelImage'])).hexdigest(),sha(b.ACTOR))
   for name,v in m['files'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),v['sha256'])
 def test_listening_conditioning_is_silence_not_male_singing(self):
  with zipfile.ZipFile(self.z) as z:
   with wave.open(io.BytesIO(z.read('listen-conditioning.wav'))) as w:
    self.assertEqual((w.getframerate(),w.getnchannels(),w.getnframes()),(16000,1,64640));self.assertFalse(any(w.readframes(w.getnframes())))
   with wave.open(io.BytesIO(z.read('listen-playback.wav'))) as w:self.assertTrue(any(w.readframes(w.getnframes())))
 def test_complete_speech_and_temporal_compression_compatible_lengths(self):
  m=json.loads((HERE/'motion/pilot-inputs.json').read_text());self.assertEqual(m['reviewedSpeechSourceSha256'],'87548f0636deaf4b5776ad24625b504dbe13679c134e5ed704ff3d645901a995')
  for j in m['jobs']:self.assertEqual((j['frames']-1)%4,0);self.assertAlmostEqual(j['frames']/25,j['duration'])
  self.assertEqual(m['jobs'][0]['completeSpeechSeconds'],4.48);self.assertFalse(m['inferenceExecuted'])
 def test_notebook_and_runner_syntax_no_execution_claim(self):
  n=json.loads((HERE/'motion/AhangBan-Ava-Motion-Pilot.ipynb').read_text())
  self.assertTrue(all(c.get('id') for c in n['cells']))
  for cell in n['cells']:
   if cell['cell_type']=='code':ast.parse(''.join(cell['source']));self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])
  script=(HERE/'motion/run_colab_pilot.py').read_text();ast.parse(script)
  self.assertIn('7e89489ca51c0d008fc1963ec6c03fc5bd0b9397',script);self.assertIn('confirm-free-or-local',script)
  self.assertFalse(self.m['motionInferenceExecuted']);self.assertFalse(self.m['publishAuthorized'])
if __name__=='__main__':unittest.main()

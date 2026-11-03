import unittest,hashlib,json,zipfile,wave,io,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
class WebPack(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=json.loads((HERE/'manifest.json').read_text());cls.b=json.loads((HERE/'bundle.json').read_text())
 def test_approved_image_exact(self):
  data=(ROOT/'downloads/ahangban-ava-web-image.png').read_bytes();self.assertEqual(sha(data),'68854d222a57969ff89567530f8b4c8202d4f8b8855acac96a23e7628e861adf')
 def test_audio_preserved(self):
  with zipfile.ZipFile(ROOT/'downloads/ahangban-ava-motion-pilot-inputs.zip') as z:self.assertEqual(z.read('talk-conditioning.wav'),(ROOT/'downloads/ahangban-ava-web-speech.wav').read_bytes())
 def test_audio_complete_duration(self):
  with wave.open(str(ROOT/'downloads/ahangban-ava-web-speech.wav')) as w:self.assertEqual((w.getnchannels(),w.getframerate(),w.getnframes()),(1,16000,77440))
  self.assertEqual(self.m['completeSpeechSeconds'],4.48)
 def test_bundle_hash(self):self.assertEqual(sha((ROOT/self.b['file']).read_bytes()),self.b['sha256'])
 def test_bundle_only_minimal_web_inputs(self):
  with zipfile.ZipFile(ROOT/self.b['file']) as z:
   self.assertEqual(set(z.namelist()),{'ava.png','speech.wav','prompt.txt','README.fa.md','provenance.json'})
   self.assertEqual(z.read('ava.png'),(ROOT/'downloads/ahangban-ava-web-image.png').read_bytes())
   self.assertNotIn('sing',z.read('prompt.txt').decode().split())
 def test_no_claim_of_execution_or_free_availability(self):
  for field in ('demoAvailabilityVerified','freeExecutionVerified','deployedVersionVerified','agentUploadedToDemo','agentInvokedModel','paidAccessAuthorized','publishAuthorized','newImageOrSpeechGenerated'):self.assertFalse(self.m[field])
  self.assertTrue(self.m['userInitiatedUploadRequired'])
 def test_packer_is_offline(self):
  tree=ast.parse((HERE/'prepare_web_pack.py').read_text());modules=[n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)]
  self.assertFalse(set(modules)&{'requests','urllib','httpx','gradio_client','subprocess'})
if __name__=='__main__':unittest.main()

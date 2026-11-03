"""Sparse input recovery tests; mocked Git stdout, no network or GPU."""
import contextlib,hashlib,io,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_colab_pilot as runner
DATA=b'fake approved bundle for restore tests'
EXPECTED={'sha256':hashlib.sha256(DATA).hexdigest()}
REL='downloads/ahangban-ava-motion-pilot-inputs.zip'
def git_result(data=DATA,returncode=0):
 def mock(cmd,**kw):
  kw['stdout'].write(data)
  return SimpleNamespace(returncode=returncode,stderr=b'fixture git error' if returncode else b'')
 return mock
class BundleTests(unittest.TestCase):
 def test_missing_sparse_bundle_restored_and_hash_checked(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run',side_effect=git_result()) as git,contextlib.redirect_stdout(io.StringIO()):
   z=runner.ensure_input_bundle(d,EXPECTED);self.assertEqual(z.read_bytes(),DATA)
   self.assertEqual(git.call_args.args[0],['git','show','HEAD:'+REL]);self.assertEqual(list(z.parent.glob('.ava-input-restore-*')),[])
 def test_existing_correct_bundle_never_replaced_or_git_called(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run') as git:
   z=Path(d)/REL;z.parent.mkdir();z.write_bytes(DATA);inode=z.stat().st_ino
   self.assertEqual(runner.ensure_input_bundle(d,EXPECTED),z);git.assert_not_called();self.assertEqual(z.stat().st_ino,inode)
 def test_existing_incorrect_bundle_preserved_and_fails(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run') as git:
   z=Path(d)/REL;z.parent.mkdir();z.write_bytes(b'KEEP USER FILE')
   with self.assertRaisesRegex(RuntimeError,'without overwriting'):runner.ensure_input_bundle(d,EXPECTED)
   self.assertEqual(z.read_bytes(),b'KEEP USER FILE');git.assert_not_called()
 def test_git_failure_does_not_leave_an_empty_bundle(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run',side_effect=git_result(b'',1)):
   with self.assertRaisesRegex(RuntimeError,'Cannot restore'):runner.ensure_input_bundle(d,EXPECTED)
   self.assertFalse((Path(d)/REL).exists());self.assertEqual(list((Path(d)/'downloads').iterdir()),[])
 def test_wrong_git_hash_not_installed_and_temporary_cleaned(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run',side_effect=git_result(b'WRONG')):
   with self.assertRaisesRegex(RuntimeError,'does not match'):runner.ensure_input_bundle(d,EXPECTED)
   self.assertFalse((Path(d)/REL).exists());self.assertEqual(list((Path(d)/'downloads').iterdir()),[])
 def test_output_and_weight_files_untouched(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run',side_effect=git_result()),contextlib.redirect_stdout(io.StringIO()):
   keep=Path(d)/'work/models/weight';keep.parent.mkdir(parents=True);keep.write_bytes(b'KEEP')
   output=Path(d)/'work/outputs/video.mp4';output.parent.mkdir(parents=True);output.write_bytes(b'VIDEO')
   runner.ensure_input_bundle(d,EXPECTED);self.assertEqual(keep.read_bytes(),b'KEEP');self.assertEqual(output.read_bytes(),b'VIDEO')
 def test_race_does_not_overwrite_a_different_file(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner.subprocess,'run',side_effect=git_result()):
   z=Path(d)/REL
   def race(source,dest):Path(dest).write_bytes(b'KEEP RACE');raise FileExistsError()
   with patch.object(runner.os,'link',side_effect=race),self.assertRaisesRegex(RuntimeError,'not overwritten'):runner.ensure_input_bundle(d,EXPECTED)
   self.assertEqual(z.read_bytes(),b'KEEP RACE');self.assertEqual(list(z.parent.glob('.ava-input-restore-*')),[])
if __name__=='__main__':unittest.main()

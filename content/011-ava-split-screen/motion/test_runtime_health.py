"""Read-only fixtures; no real model libraries, network, or CUDA used."""
import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import runtime_health as health
class RuntimeHealthTests(unittest.TestCase):
 def test_memory_and_events_read_without_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'meminfo').write_text('MemTotal: 12000000 kB\nMemAvailable: 9000000 kB\nSwapTotal: 0 kB\nUnused: 10\n')
   (root/'memory.max').write_text('12884901888');(root/'memory.events').write_text('oom 2\noom_kill 1\n')
   before={p:p.read_bytes() for p in root.iterdir()}
   with patch.object(health.subprocess,'run') as execute:r=health.collect(root,root,False)
   execute.assert_not_called();self.assertEqual(r['hostMemory']['MemAvailable'],'9000000 kB');self.assertEqual(r['cgroupMemory']['memory.events'],'oom 2\noom_kill 1')
   self.assertTrue(r['cgroupCountersAreCumulativeNotProofOfWhichProcessWasKilled']);self.assertFalse(r['modelExecuted']);self.assertEqual(before,{p:p.read_bytes() for p in root.iterdir()})
 def test_missing_sysfs_is_not_a_diagnostic_crash(self):
  with tempfile.TemporaryDirectory() as d:
   r=health.collect(d,d,False);self.assertEqual(r['hostMemory'],{});self.assertEqual(r['cgroupMemory'],{})
 def test_relocated_api_probe_no_network_and_no_inference(self):
  sample={'legacyImportAvailable':False,'relocatedImportAvailable':True,'relocatedSignature':'(model, state_dict, dtype=None)'}
  with tempfile.TemporaryDirectory() as d,patch.object(health.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(sample),'noise')) as execute:
   r=health.collect(d,d);self.assertEqual(r['loaderProbe'],sample)
   kwargs=execute.call_args.kwargs;self.assertEqual(kwargs['env']['HF_HUB_OFFLINE'],'1');self.assertEqual(kwargs['env']['USE_TF'],'0');self.assertEqual(kwargs['timeout'],45)
   self.assertNotIn('from_pretrained',health.PROBE)
 def test_probe_timeout_does_not_retry(self):
  with tempfile.TemporaryDirectory() as d,patch.object(health.subprocess,'run',side_effect=subprocess.TimeoutExpired('probe',45)) as execute:
   self.assertEqual(health.collect(d,d)['loaderProbe']['probeError'],'TimeoutExpired');self.assertEqual(execute.call_count,1)
 def test_probe_error_captured_without_claiming_oom(self):
  with tempfile.TemporaryDirectory() as d,patch.object(health.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','fixture import failed')):
   r=health.collect(d,d);self.assertEqual(r['loaderProbe']['error'],'fixture import failed');self.assertIn('not proven',r['killInterpretation'])
if __name__=='__main__':unittest.main()

"""CPU/stdlb-only tests. No weights, inference, installs, network, or real GPU calls."""
import ast,contextlib,importlib.util,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from process_tools import run_logged,LoggedProcessError
import diagnose_runtime as diagnostic
import run_colab_pilot as runner

class DiagnosticsTests(unittest.TestCase):
 def test_success_streams_and_persists_both_channels(self):
  with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()) as output:
   log=Path(d)/'log.txt'
   result=run_logged([sys.executable,'-c',"import sys;print('OUT',flush=True);print('ERR',file=sys.stderr,flush=True)"],log)
   self.assertEqual(result.returncode,0)
   self.assertEqual(log.read_text(),output.getvalue());self.assertIn('OUT',output.getvalue());self.assertIn('ERR',output.getvalue())
 def test_actual_child_exception_is_not_hidden(self):
  with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
   log=Path(d)/'log.txt'
   with self.assertRaises(LoggedProcessError) as caught:
    run_logged([sys.executable,'-c',"raise RuntimeError('REAL_CHILD_CAUSE')"],log)
   self.assertEqual(caught.exception.returncode,1)
   self.assertIn('RuntimeError: REAL_CHILD_CAUSE',str(caught.exception));self.assertIn(str(log),str(caught.exception))
   self.assertIn('Traceback',log.read_text())
 def test_existing_log_not_overwritten_and_child_not_started(self):
  with tempfile.TemporaryDirectory() as d:
   log=Path(d)/'log.txt';log.write_text('KEEP')
   with patch('process_tools.subprocess.Popen') as spawn,self.assertRaises(FileExistsError):run_logged(['no-execution'],log)
   spawn.assert_not_called();self.assertEqual(log.read_text(),'KEEP')
 def test_failure_tail_bounded_full_log_retained(self):
  with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
   log=Path(d)/'log.txt'
   with self.assertRaises(LoggedProcessError) as c:
    run_logged([sys.executable,'-c',"for i in range(100):print('line-%03d'%i)\nraise ValueError('last-cause')"],log)
   self.assertIn('line-000',log.read_text());self.assertNotIn('line-000',c.exception.tail);self.assertIn('last-cause',c.exception.tail)
 def test_no_shell_interpretation(self):
  with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
   log=Path(d)/'log';run_logged([sys.executable,'-c','import sys;print(sys.argv[1])','$(exit 99); literal'],log)
   self.assertIn('$(exit 99); literal',log.read_text())
 def test_read_only_diagnostics_preserve_existing_outputs(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'repo';work=Path(d)/'work';out=work/'outputs';out.mkdir(parents=True);video=out/'old.mp4';video.write_bytes(b'KEEP VIDEO')
   before=set(Path(d).rglob('*'))
   with patch.object(diagnostic.subprocess,'run') as run:
    result=diagnostic.collect(root,work,probe_gpu=False)
   run.assert_not_called();self.assertEqual(set(Path(d).rglob('*')),before);self.assertEqual(video.read_bytes(),b'KEEP VIDEO')
   self.assertTrue(result['outputsAlreadyExist']);self.assertFalse(result['modelExecutedByDiagnostics']);self.assertFalse(result['downloadsTriggered']);self.assertFalse(result['currentRuntimeErrorProvenByThisCheck'])
 def test_missing_torch_gpu_probe_reports_child_error(self):
  with tempfile.TemporaryDirectory() as d,patch.object(diagnostic.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','ModuleNotFoundError: torch')):
   result=diagnostic.collect(d,d)
   self.assertIn('ModuleNotFoundError',result['gpuProbe']['error'])
 def test_gpu_probe_timeout_does_not_retry(self):
  with tempfile.TemporaryDirectory() as d,patch.object(diagnostic.subprocess,'run',side_effect=subprocess.TimeoutExpired('probe',30)) as run:
   self.assertEqual(diagnostic.collect(d,d)['gpuProbe']['probeError'],'TimeoutExpired')
   self.assertEqual(run.call_count,1)
 def test_313_warns_without_claiming_known_cause(self):
  with tempfile.TemporaryDirectory() as d,patch.object(diagnostic.sys,'version_info',(3,13)):
   r=diagnostic.collect(d,d,False)
   self.assertFalse(r['pythonInUpstreamTestedRange']);self.assertFalse(r['currentRuntimeErrorProvenByThisCheck'])
 def test_failure_summary_contains_stage_and_real_error(self):
  with tempfile.TemporaryDirectory() as d,patch.object(runner,'WORK',Path(d)),patch.object(runner,'STAGE','test-stage'),patch.object(runner,'main',side_effect=ValueError('actual-error')),contextlib.redirect_stderr(io.StringIO()) as err:
   self.assertEqual(runner.cli(),1)
   saved=json.loads((Path(d)/'failure-summary.json').read_text())
   self.assertEqual(saved['stage'],'test-stage');self.assertEqual(saved['exceptionType'],'ValueError');self.assertEqual(saved['message'],'actual-error');self.assertFalse(saved['pipelineCompleted']);self.assertIn('ValueError: actual-error',err.getvalue())
 def test_summary_write_error_does_not_hide_original(self):
  with patch.object(runner,'main',side_effect=ValueError('original-cause')),patch.object(runner.Path,'mkdir',side_effect=PermissionError('disk')),contextlib.redirect_stderr(io.StringIO()) as err:
   self.assertEqual(runner.cli(),1)
   self.assertIn('original-cause',err.getvalue());self.assertIn('Could not save failure summary',err.getvalue())
 def test_stale_outputs_guard_does_not_download_or_execute(self):
  with tempfile.TemporaryDirectory() as d:
   work=Path(d);(work/'outputs').mkdir()
   with patch.object(runner,'WORK',work),patch.object(runner,'preflight',return_value={}),patch.object(runner,'inputs',return_value=(work,{})),patch.object(runner,'engine') as engine,patch.object(runner,'download_models') as download,patch.object(sys,'argv',['runner','--confirm-free-or-local']),patch.dict('os.environ',{},clear=False),contextlib.redirect_stdout(io.StringIO()):
    with self.assertRaisesRegex(RuntimeError,'Outputs already exist'):runner.main()
    engine.assert_not_called();download.assert_not_called()
 def test_notebook_syntax_and_logging(self):
  nb=json.loads((HERE/'AhangBan-Ava-Motion-Pilot.ipynb').read_text());cells={c['id']:''.join(c['source']) for c in nb['cells']}
  for c in nb['cells']:
   if c['cell_type']=='code':ast.parse(''.join(c['source']));self.assertEqual(c['outputs'],[]);self.assertIsNone(c['execution_count'])
  self.assertIn('run_logged',cells['ava-04']);self.assertIn("'-u'",cells['ava-04']);self.assertIn('diagnose_runtime.py',cells['ava-diagnostics'])
  self.assertIn("'--ff-only'",cells['ava-02']);self.assertNotIn('reset',cells['ava-02'].split('# Update')[0])
if __name__=='__main__':unittest.main()

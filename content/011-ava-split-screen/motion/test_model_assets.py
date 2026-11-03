"""Reproduce reported download-filter bug with fake flat files. No real weights/network."""
import contextlib,fnmatch,hashlib,io,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import model_assets as assets
import run_colab_pilot as runner

FILES=[*assets.BASE_REQUIRED,'diffusion_pytorch_model.safetensors',assets.TOKENIZER_PREFIX+'tokenizer_config.json',assets.TOKENIZER_PREFIX+'spiece.model','README.md','LICENSE.txt']

def populate(folder,files):
 for name in files:
  p=Path(folder)/name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(json.dumps({'dim':1536,'in_dim':36}).encode() if name=='config.json' else b'FAKE TEST FILE NOT REAL WEIGHTS')

class ModelAssetTests(unittest.TestCase):
 def test_reproduces_old_filter_fetching_only_docs(self):
  patterns=['transformer/*','vae/*','text_encoder/*','tokenizer/*','image_encoder/*','scheduler/*','model_index.json','*LICENSE*','README.md']
  self.assertEqual(sorted(p for p in FILES if any(fnmatch.fnmatchcase(p,q) for q in patterns)),['LICENSE.txt','README.md'])
 def test_flat_official_paths_selected_no_fake_subdirectories(self):
  selected=assets.base_files(FILES)
  self.assertTrue(set(assets.BASE_REQUIRED)<=set(selected));self.assertIn('diffusion_pytorch_model.safetensors',selected)
  self.assertFalse(any(p.startswith(('transformer/','vae/','text_encoder/')) for p in selected))
 def test_no_extra_model_variants_or_tokenizer_model_weights(self):
  selected=assets.base_files(FILES+['other-quantized.safetensors',assets.TOKENIZER_PREFIX+'pytorch_model.bin',assets.TOKENIZER_PREFIX+'model.safetensors'])
  self.assertNotIn('other-quantized.safetensors',selected);self.assertNotIn(assets.TOKENIZER_PREFIX+'pytorch_model.bin',selected);self.assertNotIn(assets.TOKENIZER_PREFIX+'model.safetensors',selected)
 def test_missing_metadata_component_stops_before_transfer(self):
  with self.assertRaisesRegex(assets.ModelLayoutError,'Wan2.1_VAE.pth'):assets.base_files([p for p in FILES if p!='Wan2.1_VAE.pth'])
 def test_incomplete_shards_rejected(self):
  with self.assertRaisesRegex(assets.ModelLayoutError,'Incomplete'):
   assets.base_files([p for p in FILES if p!='diffusion_pytorch_model.safetensors']+['diffusion_pytorch_model-00001-of-00002.safetensors'])
 def test_complete_shards_supported(self):
  names=['diffusion_pytorch_model-00001-of-00002.safetensors','diffusion_pytorch_model-00002-of-00002.safetensors']
  self.assertTrue(set(names)<=set(assets.base_files([p for p in FILES if p!='diffusion_pytorch_model.safetensors']+names)))
 def test_flat_validation_without_transformer_directory(self):
  with tempfile.TemporaryDirectory() as d:
   selected=assets.base_files(FILES);populate(d,selected)
   self.assertEqual(assets.validate_base(d,selected),Path(d));self.assertFalse((Path(d)/'transformer').exists())
 def test_retained_preferred_checkpoint_not_silently_loaded_or_deleted(self):
  with tempfile.TemporaryDirectory() as d:
   selected=assets.base_files(FILES);populate(d,selected);retained=Path(d)/'diffusion_pytorch_model.bin';retained.write_bytes(b'KEEP')
   with self.assertRaisesRegex(assets.ModelLayoutError,'Retained unselected'):assets.validate_base(d,selected)
   self.assertEqual(retained.read_bytes(),b'KEEP')
 def test_empty_or_missing_files_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   selected=assets.base_files(FILES);populate(d,selected);(Path(d)/'Wan2.1_VAE.pth').write_bytes(b'')
   with self.assertRaisesRegex(assets.ModelLayoutError,'missing/empty'):assets.validate_base(d,selected)
 def test_config_must_match_upstream_mapping(self):
  with tempfile.TemporaryDirectory() as d:
   selected=assets.base_files(FILES);populate(d,selected);(Path(d)/'config.json').write_text('{}')
   with self.assertRaisesRegex(assets.ModelLayoutError,'dim/in_dim'):assets.validate_base(d,selected)
 def test_hash_streams_and_matches_without_read_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   file=Path(d)/'large';data=b'fixture'*2000000;file.write_bytes(data)
   with patch.object(Path,'read_bytes',side_effect=AssertionError('Must stream')):self.assertEqual(assets.file_sha256(file),hashlib.sha256(data).hexdigest())
 def test_download_integration_cache_kept_metadata_pinned_no_real_network(self):
  with tempfile.TemporaryDirectory() as d:
   work=Path(d);base=work/'models/base';base.mkdir(parents=True);keep=base/'README.md';keep.write_text('KEEP OLD DOWNLOAD')
   # Fake revision-pinned service. Reuses preexisting fake Flash and encoder caches.
   flash=work/'models/flash';populate(flash,['echomimicv3-flash-pro/transformer/diffusion_pytorch_model.safetensors','echomimicv3-flash-pro/chinese-wav2vec2-base/config.json'])
   api=types.SimpleNamespace(model_info=lambda repo:types.SimpleNamespace(sha='mock-pinned-revision'),list_repo_files=lambda **kw:FILES)
   calls=[]
   def snapshot_download(**kw):
    calls.append(kw)
    if kw['repo_id']==assets.BASE_REPO:populate(kw['local_dir'],kw['allow_patterns'])
    return str(kw['local_dir'])
   hub=types.SimpleNamespace(HfApi=lambda **kw:api,snapshot_download=snapshot_download)
   with patch.dict(sys.modules,{'huggingface_hub':hub}),patch.object(runner,'WORK',work),contextlib.redirect_stdout(io.StringIO()):
    result=runner.download_models()
   self.assertEqual(result[0],base);self.assertEqual(keep.read_text(),'KEEP OLD DOWNLOAD');self.assertEqual(len(calls),2)
   self.assertTrue(set(assets.BASE_REQUIRED)<=set(calls[0]['allow_patterns']));self.assertEqual(calls[0]['revision'],'mock-pinned-revision');self.assertFalse(calls[0]['token'])
   self.assertFalse((work/'outputs').exists());audit=json.loads((work/'model-provenance.json').read_text());self.assertEqual(audit[0]['repository'],assets.BASE_REPO)
 def test_bad_remote_layout_never_starts_snapshot_download(self):
  api=types.SimpleNamespace(model_info=lambda repo:types.SimpleNamespace(sha='mock-pin'),list_repo_files=lambda **kw:['README.md'])
  hub=types.SimpleNamespace(HfApi=lambda **kw:api,snapshot_download=unittest.mock.Mock())
  with patch.dict(sys.modules,{'huggingface_hub':hub}),self.assertRaises(assets.ModelLayoutError):runner.download_models()
  hub.snapshot_download.assert_not_called()
 def test_prepare_models_only_does_not_preflight_engine_or_infer(self):
  with patch.object(sys,'argv',['runner','--confirm-free-or-local','--prepare-models-only']),patch.object(runner,'download_models',return_value=('base','flash','encoder')),patch.object(runner,'preflight') as preflight,patch.object(runner,'engine') as engine,patch.object(runner,'run') as execute,patch.dict('os.environ',{},clear=False),contextlib.redirect_stdout(io.StringIO()) as output:
   runner.main();preflight.assert_not_called();engine.assert_not_called();execute.assert_not_called();self.assertIn('MODEL_FILES_READY_NO_INFERENCE',output.getvalue())
 def test_download_only_requires_free_confirmation(self):
  with patch.object(sys,'argv',['runner','--prepare-models-only']),patch.object(runner,'download_models') as download:
   with self.assertRaisesRegex(RuntimeError,'confirmation required'):runner.main()
   download.assert_not_called()
if __name__=='__main__':unittest.main()

"""Official flat Wan checkpoint layout, per pinned EchoMimicV3 config/config.yaml.
No imports of Torch/HF, no network, model construction, or file writes in this module.
"""
import hashlib,json,re
from pathlib import Path

BASE_REPO='alibaba-pai/Wan2.1-Fun-V1.1-1.3B-InP'
CONFIG_SOURCE='https://github.com/antgroup/echomimic_v3/blob/7e89489ca51c0d008fc1963ec6c03fc5bd0b9397/config/config.yaml'
CONFIG_SHA256='21fe4409b664385a1c1cc5c23d92506ffb05ef3c374a18de9df67b715dca07e9'
BASE_REQUIRED=('config.json','Wan2.1_VAE.pth','models_t5_umt5-xxl-enc-bf16.pth','models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth')
TOKENIZER_PREFIX='google/umt5-xxl/'

class ModelLayoutError(RuntimeError):pass

def file_sha256(path):
 """Large T5/transformer files must NOT be read into RAM all at once."""
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def base_files(repo_files):
 """Resolve exact, revision-pinned filenames BEFORE any multi-GB transfers.
 Match the official custom Wan loader, not a Diffusers directory snapshot.
 """
 names=set(repo_files)
 if any(p.startswith('/') or '..' in p.split('/') or '\\' in p for p in names):raise ModelLayoutError('Unsafe model repository filename')
 missing=[p for p in BASE_REQUIRED if p not in names]
 # The upstream loader prefers a .bin if present, otherwise the single safetensor,
 # then all root safetensor shards. Prefer safetensors when choosing new downloads.
 if 'diffusion_pytorch_model.safetensors' in names:weights=['diffusion_pytorch_model.safetensors']
 else:
  shards={p:re.fullmatch(r'diffusion_pytorch_model-(\d+)-of-(\d+)\.safetensors',p) for p in names}
  shards={p:m for p,m in shards.items() if m}
  if shards:
   totals={int(m[2]) for m in shards.values()};indices={int(m[1]) for m in shards.values()}
   if len(totals)!=1 or len(shards)!=next(iter(totals)) or indices!=set(range(1,next(iter(totals))+1)):raise ModelLayoutError('Incomplete official transformer shard set in repository metadata; stop before downloading')
   weights=sorted(shards)
  elif 'diffusion_pytorch_model.bin' in names:weights=['diffusion_pytorch_model.bin']
  else:weights=[];missing.append('root diffusion_pytorch_model.safetensors/.bin (or complete shards)')
 tokenizer=sorted(p for p in names if p.startswith(TOKENIZER_PREFIX) and p.endswith(('.json','.model','.txt')))
 if TOKENIZER_PREFIX+'tokenizer_config.json' not in tokenizer:missing.append(TOKENIZER_PREFIX+'tokenizer_config.json')
 if not any(TOKENIZER_PREFIX+x in tokenizer for x in ('tokenizer.json','spiece.model')):missing.append(TOKENIZER_PREFIX+'tokenizer.json or spiece.model')
 if missing:raise ModelLayoutError('Official base layout does not match pinned config; missing: '+', '.join(missing)+'. No weights were requested. Source: '+CONFIG_SOURCE)
 return sorted(set(BASE_REQUIRED)|set(weights)|set(tokenizer))

def validate_base(folder,selected):
 folder=Path(folder);missing=[p for p in selected if not (folder/p).is_file() or (folder/p).stat().st_size==0]
 if missing:raise ModelLayoutError('Base download incomplete; missing/empty files: '+', '.join(missing)+'. Keep existing cache; do not create empty transformer/vae directories.')
 # Do not let the custom loader silently prefer a retained, unrequested file.
 for preferred in ('diffusion_pytorch_model.bin','diffusion_pytorch_model.safetensors'):
  if (folder/preferred).exists() and preferred not in selected:raise ModelLayoutError('Retained unselected checkpoint would override selected weights: '+preferred+'. Stop without deleting cache.')
 if 'diffusion_pytorch_model.safetensors' not in selected and 'diffusion_pytorch_model.bin' not in selected:
  extra=[p.name for p in folder.glob('*.safetensors') if p.name not in selected]
  if extra:raise ModelLayoutError('Unselected root safetensors would enter shard loading: '+', '.join(extra))
 try:config=json.loads((folder/'config.json').read_text())
 except (ValueError,OSError) as exc:raise ModelLayoutError('Unreadable base config.json') from exc
 if not isinstance(config,dict) or any(k not in config for k in ('dim','in_dim')):raise ModelLayoutError('Base config.json lacks dim/in_dim required by pinned Wan config mapping')
 return folder

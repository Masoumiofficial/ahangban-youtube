"""EXPERIMENTAL user-run free/local GPU pilot. NOT executed in Arena.
Official EchoMimicV3 Flash, not rejected MuseTalk. No API, billing, clone or TTS.
"""
import argparse,hashlib,json,os,subprocess,sys,zipfile,shutil,wave,traceback,warnings,uuid
from pathlib import Path
PIN='7e89489ca51c0d008fc1963ec6c03fc5bd0b9397'
UPSTREAM='https://github.com/antgroup/echomimic_v3.git'
HERE=Path(__file__).resolve().parent;WORK=Path('/content/ava-motion-pilot')
from model_assets import BASE_REPO,base_files,validate_base,file_sha256
sha=file_sha256
from process_tools import run_logged
STAGE='startup';COMMAND_NUMBER=0;RUN_ID=uuid.uuid4().hex
def stage(name):
 global STAGE
 STAGE=name;print('AVA_STAGE:',name,flush=True)
def run(cmd,**kwargs):
 global COMMAND_NUMBER
 COMMAND_NUMBER+=1
 return run_logged(cmd,WORK/'logs'/RUN_ID/f'command-{COMMAND_NUMBER:02d}.log',new_session=False,**kwargs)

def preflight():
 if sys.version_info[:2] not in ((3,10),(3,11)):
  warnings.warn('This model recipe has not been validated with Python '+sys.version.split()[0]+'. Upstream lists Python3.10/3.11; this is a compatibility risk, not an identified root cause.',RuntimeWarning)
 import torch
 if not torch.cuda.is_available():raise RuntimeError('No free GPU assigned. STOP. Do not purchase compute or upgrade.')
 p=torch.cuda.get_device_properties(0)
 if p.total_memory<12*2**30:raise RuntimeError('Less than 12GiB VRAM; STOP, no paid fallback.')
 return dict(gpu=p.name,vramGiB=round(p.total_memory/2**30,2),torch=torch.__version__,dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'float16',inferenceActuallyExecuted=False)
def inputs():
 WORK.mkdir(parents=True,exist_ok=True);z=HERE.parents[2]/'downloads/ahangban-ava-motion-pilot-inputs.zip'
 expected=json.loads((HERE/'bundle.json').read_text());assert sha(z)==expected['sha256']
 dest=WORK/'inputs';dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(z) as f:
  allowed={'ava.png','talk-playback.wav','talk-conditioning.wav','listen-conditioning.wav','listen-playback.wav','pilot-inputs.json'}
  assert set(f.namelist())==allowed
  for name in f.namelist():f.extract(name,dest)
 m=json.loads((dest/'pilot-inputs.json').read_text())
 for name,record in m['files'].items():assert sha(dest/name)==record['sha256']
 return dest,m

def download_models():
 from huggingface_hub import HfApi,snapshot_download
 api=HfApi(token=False);audit=[];models=WORK/'models'
 def hf(repo,folder,patterns=None):
  pin=api.model_info(repo).sha
  if patterns is None:
   patterns=base_files(api.list_repo_files(repo_id=repo,revision=pin,token=False))
  print('Downloading official model:',repo,'revision:',pin,flush=True)
  result=Path(snapshot_download(repo_id=repo,revision=pin,local_dir=models/folder,allow_patterns=patterns,token=False))
  if repo==BASE_REPO:validate_base(result,patterns)
  audit.append(dict(provider='HuggingFace',repository=repo,revision=pin,requestedFiles=patterns,files=[dict(path=str(p.relative_to(result)),sha256=sha(p),bytes=p.stat().st_size) for p in ([result/name for name in patterns] if repo==BASE_REPO else result.rglob('*')) if p.is_file() and '.cache' not in p.parts]))
  return result
 base=hf(BASE_REPO,'base')
 flash=hf('BadToBest/EchoMimicV3','flash',['echomimicv3-flash-pro/diffusion_pytorch_model.safetensors','echomimicv3-flash-pro/transformer/*','echomimicv3-flash-pro/chinese-wav2vec2-base/*','*LICENSE*','README.md'])
 weights=list(flash.glob('echomimicv3-flash-pro/**/diffusion_pytorch_model.safetensors'))
 if len(weights)!=1:raise RuntimeError('Official Flash checkpoint layout differs from reviewed source. Stop; no unofficial fallback.')
 encoders=list(flash.glob('echomimicv3-flash-pro/**/chinese-wav2vec2-base'))
 if encoders:encoder=encoders[0]
 else:
  # Official encoder source explicitly linked in upstream README. Public weights only;
  # NO reference face/audio is uploaded to ModelScope or HuggingFace.
  from modelscope import snapshot_download as ms_download
  encoder=Path(ms_download('TencentGameMate/chinese-wav2vec2-base',revision='master',cache_dir=str(models/'modelscope')))
  audit.append(dict(provider='ModelScope',repository='TencentGameMate/chinese-wav2vec2-base',requestedRevision='master',immutableRevisionNotResolved=True,files=[dict(path=str(p.relative_to(encoder)),sha256=sha(p),bytes=p.stat().st_size) for p in encoder.rglob('*') if p.is_file()]))
 if not encoder.is_dir():raise RuntimeError('Missing official audio encoder: '+str(encoder))
 (WORK/'model-provenance.json').write_text(json.dumps(audit,indent=2)+'\n')
 return base,weights[0],encoder

def engine():
 path=WORK/'engine'
 if not path.exists():run(['git','clone','--no-checkout',UPSTREAM,path])
 run(['git','checkout','--detach',PIN],cwd=path)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==PIN
 src=path/'infer_flash.py';text=src.read_text();before=sha(src)
 # Official pipeline explicitly defines model_cpu_offload_seq. Upstream CLI declares
 # GPU_memory_mode but still moves whole pipeline onto CUDA twice. Bounded patch:
 # use Accelerate model CPU offload instead; don't promise untested VRAM/CPU usage.
 needle='    pipeline.to(device=device)'
 if text.count(needle)!=2:raise RuntimeError('Upstream memory-management preimage changed')
 text=text.replace(needle,'    pipeline.enable_model_cpu_offload(gpu_id=torch.cuda.current_device())',1)
 text=text.replace(needle,'    # Keep CPU offload hooks; do not move the entire pipeline to CUDA.',1)
 marker='        print(f"missing keys: {len(m)}, unexpected keys: {len(u)}")'
 if text.count(marker)!=2:raise RuntimeError('Upstream checkpoint-loading preimage changed')
 text=text.replace(marker,marker+'\n        del state_dict\n        import gc\n        gc.collect()')
 patched=path/'infer_flash_ahangban.py';patched.write_text(text)
 (WORK/'engine-provenance.json').write_text(json.dumps(dict(repository=UPSTREAM,revision=PIN,upstreamFileSha256=before,patchedFileSha256=sha(patched),localChanges=['Enable existing pipeline CPU offload instead of two full-CUDA moves','Release checkpoint state_dict after loading to limit RAM peaks'],runtimeTestedInArena=False),indent=2)+'\n')
 return path,patched

def validate_video(file,job):
 import imageio_ffmpeg,numpy as np
 reader=imageio_ffmpeg.read_frames(str(file),pix_fmt='rgb24');meta=next(reader);w,h=meta['size'];count=0;first=None;variation=0.
 for buf in reader:
  a=np.frombuffer(buf,np.uint8).reshape(h,w,3)[int(h*.12):int(h*.56),int(w*.31):int(w*.7)].astype(np.float32)
  if first is None:first=a
  else:variation=max(variation,float(np.mean(np.abs(a-first))))
  count+=1
 if count!=job['frames'] or abs(meta['fps']-25)>.05:raise RuntimeError('Wrong native frame count or FPS')
 if variation<.7:raise RuntimeError('No substantial face-region temporal variation; not a successful animation test')
 if abs(meta['duration']-job['duration'])>.15:raise RuntimeError('Truncated/padded utterance or wrong video duration')
 return dict(file=str(file.relative_to(WORK)),sha256=sha(file),frames=count,fps=meta['fps'],nativeSize=[w,h],maxFaceRegionDifference=variation,technicalTemporalVariationOnly=True,identityAndPersianPhonemeSyncHumanReviewPending=True,listeningClosedMouthHumanReviewPending=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--confirm-free-or-local',action='store_true');parser.add_argument('--prepare-models-only',action='store_true',help='Download/validate official weights only. No engine, GPU model, or video inference.');args=parser.parse_args()
 if not args.confirm_free_or_local:raise RuntimeError('Explicit free/local-runtime confirmation required; no metered compute.')
 os.environ.update(HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 if args.prepare_models_only:
  stage('model_downloads');base,weights,encoder=download_models()
  print('MODEL_FILES_READY_NO_INFERENCE',flush=True);return
 stage('preflight');report=preflight()
 stage('input_validation');source,m=inputs();out=WORK/'outputs'
 stage('stale_output_guard')
 if out.exists():raise RuntimeError('Outputs already exist; stop rather than silently reusing stale model videos. Use a fresh runtime for a fresh run.')
 stage('engine_setup');path,script=engine()
 stage('model_downloads');base,weights,encoder=download_models();results=[]
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 for job in m['jobs']:
  stage('inference:'+job['id'])
  folder=out/job['id'];folder.mkdir(parents=True,exist_ok=False)
  run([sys.executable,script,'--config_path','config/config.yaml','--model_name',base,'--transformer_path',weights,'--wav2vec_model_dir',encoder,'--image_path',source/m['modelImage'],'--audio_path',source/job['conditioning'],'--prompt',job['prompt'],'--save_path',folder,'--num_inference_steps','8','--video_length',job['frames'],'--sample_size','768','768','--fps','25','--weight_dtype',report['dtype'],'--seed','43','--negative_prompt','Different face, changed identity, changed clothes, distorted mouth, extra teeth, warped face, green skin, camera movement, large head turn, singing during silence, extra fingers.'],cwd=path)
  video=folder/'ava_output.mp4'
  if not video.is_file():raise RuntimeError('No newly rendered video returned')
  stage('validate:'+job['id']);checked=validate_video(video,job)
  # Never play synthetic conditioning silence in the listening preview. Replace only
  # audio, retaining the actual generated video frames and original approved playback.
  import imageio_ffmpeg
  stage('playback:'+job['id'])
  ff=imageio_ffmpeg.get_ffmpeg_exe();playback=folder/f"{job['id']}-playback.mp4"
  run([ff,'-v','error','-y','-i',video,'-i',source/job['playback'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',job['duration'],'-movflags','+faststart',playback])
  checked.update(playback=str(playback.relative_to(WORK)),playbackSha256=sha(playback));results.append(checked)
 stage('package_results')
 report.update(status='TWO_MODEL_CLIPS_RENDERED_REVIEW_REQUIRED',inferenceActuallyExecuted=True,model='EchoMimicV3 Flash',sourceInputs=m,results=results,paidFallbackUsed=False,publishAuthorized=False,qualityApproved=False)
 (WORK/'pilot-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 bundle=WORK/'ava-motion-pilot-results.zip'
 with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
  for file in [WORK/'pilot-results.json',WORK/'model-provenance.json',WORK/'engine-provenance.json',*(out.rglob('*.mp4'))]:z.write(file,str(file.relative_to(WORK)))
 print('Model inference returned two clips, NOT a final/approved film. Human identity, Persian sync and listening review required.\n'+str(bundle))
def cli():
 try:main()
 except Exception as exc:
  print('AVA_FAILURE_STAGE:',STAGE,file=sys.stderr,flush=True)
  traceback.print_exc()
  data=dict(stage=STAGE,exceptionType=type(exc).__name__,message=str(exc),python=sys.version.split()[0],pipelineCompleted=False,logFile=str(getattr(exc,'log_path','')),reportedMissingBaseTransformerCause='incorrect directory-based download filter and guard; official pinned config uses flat files')
  try:
   WORK.mkdir(parents=True,exist_ok=True)
   (WORK/'failure-summary.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  except OSError as log_error:
   print('Could not save failure summary:',log_error,file=sys.stderr,flush=True)
  return 1
 return 0
if __name__=='__main__':sys.exit(cli())

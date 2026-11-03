"""Read-only runtime checks. No model downloads/inference, installs, cleanup, or upload."""
from pathlib import Path
import argparse,hashlib,importlib.metadata as metadata,json,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PACKAGES=('torch','torchvision','numpy','diffusers','transformers','accelerate','huggingface-hub','modelscope','decord','moviepy','imageio-ffmpeg')
GPU_PROBE="""import json,torch
print(json.dumps(dict(torch=torch.__version__,cudaAvailable=torch.cuda.is_available(),gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,vramGiB=round(torch.cuda.get_device_properties(0).total_memory/2**30,2) if torch.cuda.is_available() else None)))
"""
def package_versions():
 result={}
 for name in PACKAGES:
  try:result[name]=metadata.version(name)
  except metadata.PackageNotFoundError:result[name]=None
 return result

def collect(root=ROOT,work=Path('/content/ava-motion-pilot'),probe_gpu=True):
 root=Path(root);work=Path(work);py=sys.version_info[:2];zip_path=root/'downloads/ahangban-ava-motion-pilot-inputs.zip';bundle=root/'content/011-ava-split-screen/motion/bundle.json'
 result=dict(status='DIAGNOSTICS_ONLY_NOT_MODEL_RESULT',python=sys.version.split()[0],executable=sys.executable,pythonInUpstreamTestedRange=py in ((3,10),(3,11)),pythonCompatibilityNote='Upstream lists Python3.10/3.11; other versions are untested, NOT proof of the original root cause.',packageVersions=package_versions(),inputZipPresent=zip_path.is_file(),outputsAlreadyExist=(work/'outputs').exists(),reportedBaseLayoutBugKnown=True,currentRuntimeErrorProvenByThisCheck=False,modelExecutedByDiagnostics=False,downloadsTriggered=False,filesDeleted=False)
 if zip_path.is_file() and bundle.is_file():
  try:result['inputZipHashMatches']=hashlib.sha256(zip_path.read_bytes()).hexdigest()==json.loads(bundle.read_text())['sha256']
  except (ValueError,KeyError,OSError) as e:result['inputZipCheckError']=type(e).__name__
 failure=work/'failure-summary.json'
 if failure.is_file():
  try:
   f=json.loads(failure.read_text());result['savedFailure']={k:f.get(k) for k in ('stage','exceptionType','message','logFile','pipelineCompleted')}
  except (ValueError,OSError):result['savedFailure']='unreadable'
 else:result['savedFailure']=None
 if probe_gpu:
  try:
   p=subprocess.run([sys.executable,'-c',GPU_PROBE],capture_output=True,text=True,timeout=30)
   if p.returncode==0:result['gpuProbe']=json.loads(p.stdout.strip().splitlines()[-1])
   else:result['gpuProbe']={'returncode':p.returncode,'error':p.stderr[-2500:]}
  except (subprocess.TimeoutExpired,ValueError,IndexError,OSError) as e:result['gpuProbe']={'probeError':type(e).__name__}
 if result['outputsAlreadyExist']:result['staleOutputNote']='The existing safety guard would refuse a fresh full run. Do not delete outputs or assume this was the original error.'
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--skip-gpu-probe',action='store_true');a=p.parse_args();print(json.dumps(collect(probe_gpu=not a.skip_gpu_probe),ensure_ascii=False,indent=2))
if __name__=='__main__':main()

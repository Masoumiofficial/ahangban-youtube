"""Read-only evidence after SIGKILL: host/cgroup RAM and relocated loader API.
No weights loaded/read, GPU allocations, installs, network, cleanup, or inference.
"""
from pathlib import Path
import json,os,subprocess,sys
CGROUP_FILES=('memory.max','memory.current','memory.peak','memory.events','memory/memory.limit_in_bytes','memory/memory.usage_in_bytes','memory/memory.failcnt')
PROBE="""import inspect,json
from diffusers.models import modeling_utils
from diffusers.models import model_loading_utils
old=getattr(modeling_utils,'load_model_dict_into_meta',None)
new=getattr(model_loading_utils,'load_model_dict_into_meta',None)
print(json.dumps({'legacyImportAvailable':callable(old),'relocatedImportAvailable':callable(new),'relocatedSignature':str(inspect.signature(new)) if callable(new) else None}))
"""
def bounded_read(path):
 try:
  with Path(path).open(encoding='utf-8') as f:return f.read(8192)
 except OSError:return None

def collect(proc=Path('/proc'),cgroup=Path('/sys/fs/cgroup'),probe_loader=True):
 result=dict(status='READ_ONLY_AFTER_SIGKILL_NOT_A_RENDER',modelExecuted=False,weightsReadOrDownloaded=False,filesDeleted=False,killInterpretation='-9 means SIGKILL. RAM exhaustion is suspected, not proven by the exit code alone.',cgroupCountersAreCumulativeNotProofOfWhichProcessWasKilled=True)
 text=bounded_read(Path(proc)/'meminfo') or ''
 result['hostMemory']={k:v.strip() for line in text.splitlines() if ':' in line for k,v in [line.split(':',1)] if k in ('MemTotal','MemAvailable','SwapTotal','SwapFree')}
 result['cgroupMemory']={name:value.strip() for name in CGROUP_FILES if (value:=bounded_read(Path(cgroup)/name)) is not None}
 result['hostMemoryMayDifferFromContainerLimit']=True
 if probe_loader:
  env=dict(os.environ);env.update(USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
  try:
   p=subprocess.run([sys.executable,'-c',PROBE],capture_output=True,text=True,timeout=45,env=env)
   result['loaderProbe']=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else dict(returncode=p.returncode,error=p.stderr[-2500:])
  except (OSError,ValueError,IndexError,subprocess.TimeoutExpired) as e:result['loaderProbe']={'probeError':type(e).__name__}
 return result
if __name__=='__main__':print(json.dumps(collect(),ensure_ascii=False,indent=2))

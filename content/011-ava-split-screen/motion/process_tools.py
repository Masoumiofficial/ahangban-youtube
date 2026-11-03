"""Stream child stderr/stdout into notebook AND a local log. No network or inference."""
from collections import deque
from pathlib import Path
import os,signal,subprocess

class LoggedProcessError(RuntimeError):
 def __init__(self,returncode,log_path,tail):
  self.returncode=returncode;self.log_path=Path(log_path);self.tail=tail
  super().__init__(f'Child process exited with code {returncode}. Full local log: {log_path}\n--- child output tail ---\n{tail}')

def run_logged(cmd,log_path,*,cwd=None,env=None,new_session=True):
 """No shell, no env dump, no retries, no file deletion; keep actual failing output."""
 path=Path(log_path);path.parent.mkdir(parents=True,exist_ok=True);tail=deque(maxlen=50)
 child_env=dict(os.environ if env is None else env);child_env['PYTHONUNBUFFERED']='1'
 with path.open('x',encoding='utf-8') as log:
  proc=subprocess.Popen([str(x) for x in cmd],cwd=cwd,env=child_env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,start_new_session=(new_session and os.name=='posix'))
  try:
   for line in proc.stdout:
    print(line,end='',flush=True);log.write(line);log.flush();tail.append(line)
   code=proc.wait()
  except BaseException:
   if proc.poll() is None:
    if new_session and os.name=='posix':os.killpg(proc.pid,signal.SIGTERM)
    else:proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
     if new_session and os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
     else:proc.kill()
     proc.wait()
   raise
  finally:proc.stdout.close()
 if code:raise LoggedProcessError(code,path,''.join(tail))
 return subprocess.CompletedProcess([str(x) for x in cmd],code)

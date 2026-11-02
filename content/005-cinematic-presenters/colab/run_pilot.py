"""Short real MuseTalk inference for a USER-RUN free Colab session.
Not executed in Arena. No APIs, billing, Drive mount, voice synthesis or upload.
Adapted model calls from Tencent Music's MIT-licensed MuseTalk (see NOTICE).
Manual boxes + bounded mouth matte replace pose detection and face parsing.
"""
import argparse, hashlib, json, math, os, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from prepare_lipsync_pilot import prepare
from build_camera_demo import SOURCE, EPISODE, crop_box, studio

SETTINGS=HERE/'pilot-settings.json'
PRIVATE=REPO/'rendered/colab-lipsync'
ASSET_HASHES={
 'downloads/ahangban-first-video-final.mp4':'2efd5ba3cb0731ff256e707a7ef5ba508da6c364eee3e364cf9f1c5f452ee0e5',
 'studio/ahangban-signature/productions/HOSTS-VIEW-002.png':'8840148a415fc5b5d0e322822ce8c0dbaac8671298d5f0a8522ab19bc8e46050',
 'studio/ahangban-signature/overlays/AHANGBAN-LOGO-CORE.png':'34936480af9e5663e9bd871ac3efbcc5cbb0c9b96cc1092f682775b78f52435c',
 'studio/ahangban-signature/overlays/AHANGBAN-LOGO-GLOW.png':'ad9e31c46d9ae19e1d84c566ee50653d895c8648a8635e7d8f76ecb78680e63e'}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def verify_assets():
 for rel,expected in ASSET_HASHES.items():
  if sha(REPO/rel)!=expected:raise RuntimeError('Wrong reference asset: '+rel)

def mouth_mask(size,config):
 """Bounded feathered matte; zero contribution at/below mic protection line."""
 mask=Image.new('L',size)
 ImageDraw.Draw(mask).ellipse(config['mouthEllipse'],fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(2))
 ImageDraw.Draw(mask).rectangle((0,config['protectFromY'],size[0],size[1]),fill=0)
 return mask

def blend_patch(base,generated,job,config):
 left,top,right,bottom=job['sourceCropPixels']
 original=base.crop((left,top,right,bottom))
 if generated.size!=original.size:raise ValueError('Generated context moved or resized')
 mask=mouth_mask(original.size,config)
 combined=Image.composite(generated,original,mask)
 im=base.copy();im.paste(combined,(left,top))
 return im

def prepare_inputs():
 verify_assets()
 report=prepare(PRIVATE/'inputs')
 cfg=json.loads(SETTINGS.read_text())
 for job in report['inputs']:
  role=job['speaker'];file=PRIVATE/'inputs'/f'{role}-playback.wav'
  subprocess.run([studio.FF,'-v','error','-y','-i',str(EPISODE),'-ss',f'{job["start"]:.9f}',
   '-t',f'{job["duration"]:.9f}','-map','0:a:0','-ar','48000','-ac','2','-c:a','pcm_s16le',str(file)],check=True)
  job['playbackAudio']=file.name
  im=Image.open(PRIVATE/'inputs'/job['image']).convert('RGB')
  overlay=im.copy();d=ImageDraw.Draw(overlay)
  d.rectangle(cfg['hosts'][role]['faceBox'],outline='cyan',width=2)
  d.ellipse(cfg['hosts'][role]['mouthEllipse'],outline='yellow',width=2)
  d.line((0,cfg['hosts'][role]['protectFromY'],im.width,cfg['hosts'][role]['protectFromY']),fill='red',width=2)
  overlay.save(PRIVATE/'inputs'/f'{role}-calibration.png')
 report['colabConsent']='User approved free Colab pilot; files fetched from own public repository into user-started Google runtime'
 report['thirdPartyUpload']=True # Authorized processing of fetched faces/audio by Google Colab.
 report['outboundUploadFromRuntime']=False
 report['cloudProcessingEnvironment']='User-run Google Colab (not local laptop); source faces/audio are fetched into Google'
 (PRIVATE/'inputs/pilot-inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('Prepared conditioning audio (16k), original playback audio (48k), calibration images.')

def download_models(muse):
 from huggingface_hub import HfApi,snapshot_download
 cfg=json.loads(SETTINGS.read_text())
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=muse,text=True).strip()
 if revision!=cfg['musetalkRevision']:raise RuntimeError('Unexpected MuseTalk checkout')
 # Official, public model repositories ONLY. No login, token, mirror, proxy,
 # unofficial checkpoint or training data. Revisions resolved and recorded first.
 sources=[('TMElyralab/MuseTalk',muse/'models',['musetalkV15/unet.pth','musetalkV15/musetalk.json','LICENSE*','README.md']),
  ('stabilityai/sd-vae-ft-mse',muse/'models/sd-vae',['config.json','diffusion_pytorch_model.bin','LICENSE*','README.md']),
  ('openai/whisper-tiny',muse/'models/whisper',['config.json','pytorch_model.bin','preprocessor_config.json','LICENSE*','README.md'])]
 audit=[]
 for repo,dest,patterns in sources:
  pin=HfApi(token=False).model_info(repo).sha
  snapshot_download(repo_id=repo,revision=pin,allow_patterns=patterns,local_dir=dest,token=False)
  audit.append({'repository':repo,'revision':pin,'files':[{'name':str(p.relative_to(dest)),'sha256':sha(p)} for p in dest.rglob('*') if p.is_file() and '.cache' not in p.parts]})
 for path in ('musetalkV15/unet.pth','musetalkV15/musetalk.json','sd-vae/config.json',
              'sd-vae/diffusion_pytorch_model.bin','whisper/config.json','whisper/pytorch_model.bin','whisper/preprocessor_config.json'):
  p=muse/'models'/path
  if not p.is_file() or p.stat().st_size<16:raise RuntimeError('Missing model component: '+path)
 PRIVATE.mkdir(parents=True,exist_ok=True)
 (PRIVATE/'model-provenance.json').write_text(json.dumps(audit,indent=2)+'\n')
 print('Only UNet, VAE and Whisper downloaded. No pose, detector or face-parsing weights.')

def infer(muse):
 import cv2,numpy as np,torch
 from transformers import WhisperModel
 cfg=json.loads(SETTINGS.read_text())
 if not torch.cuda.is_available():raise RuntimeError('No free GPU assigned. Stop; do not purchase compute.')
 device=torch.device('cuda:0');props=torch.cuda.get_device_properties(0)
 if props.total_memory/1024**3<cfg['minimumVramGiB']:raise RuntimeError('GPU too small for this pilot; no paid fallback.')
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=muse,text=True).strip()!=cfg['musetalkRevision']:
  raise RuntimeError('Wrong MuseTalk version')
 verify_assets()
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 sys.path.insert(0,str(muse));os.chdir(muse)
 from musetalk.utils.utils import load_all_model
 from musetalk.utils.audio_processor import AudioProcessor
 torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed'])
 torch.backends.cudnn.benchmark=False
 out=PRIVATE/'outputs';out.mkdir(parents=True,exist_ok=True)
 # Remove previous success markers so a failed rerun cannot serve stale results.
 for path in (out/'pilot-results.json',out/'male-studio-pilot.mp4',out/'female-studio-pilot.mp4'):
  path.unlink(missing_ok=True)
 with torch.inference_mode():
  vae,unet,pe=load_all_model(unet_model_path=str(muse/'models/musetalkV15/unet.pth'),
   unet_config=str(muse/'models/musetalkV15/musetalk.json'),device=device)
  vae.vae=vae.vae.half().to(device).eval();unet.model=unet.model.half().to(device).eval();pe=pe.half().to(device).eval()
  whisper=WhisperModel.from_pretrained(str(muse/'models/whisper'),local_files_only=True).half().to(device).eval()
  processor=AudioProcessor(feature_extractor_path=str(muse/'models/whisper'))
  jobs=json.loads((PRIVATE/'inputs/pilot-inputs.json').read_text())['inputs']
  base=Image.open(SOURCE).convert('RGBA')
  for name in ('AHANGBAN-LOGO-GLOW.png','AHANGBAN-LOGO-CORE.png'):
   base=Image.alpha_composite(base,Image.open(studio.STUDIO/'overlays'/name).convert('RGBA'))
  base=base.convert('RGB');results=[]
  for job in jobs:
   role=job['speaker'];settings=cfg['hosts'][role];input_dir=PRIVATE/'inputs'
   if sha(input_dir/job['audio'])!=job['audioSha256'] or sha(input_dir/job['image'])!=job['imageSha256']:
    raise RuntimeError('Pilot conditioning inputs have changed')
   context=cv2.imread(str(input_dir/job['image']))
   x1,y1,x2,y2=settings['faceBox']
   if not (0<=x1<x2<=context.shape[1] and 0<=y1<y2<=context.shape[0]):raise ValueError('Invalid manual face box')
   face=cv2.resize(context[y1:y2,x1:x2],(256,256),interpolation=cv2.INTER_LANCZOS4)
   latent=vae.get_latents_for_unet(face)
   features,length=processor.get_audio_feature(str(input_dir/job['audio']))
   chunks=processor.get_whisper_chunk(features,device,torch.float16,whisper,length,fps=cfg['fps'])
   count=math.ceil(job['duration']*cfg['fps'])
   if abs(len(chunks)-count)>1:raise RuntimeError('Audio/feature frame count mismatch')
   destination=out/f'{role}-studio-pilot.mp4'
   cmd=[studio.FF,'-v','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(cfg['fps']),
        '-i','pipe:0','-i',str(input_dir/job['playbackAudio']),'-map','0:v:0','-map','1:a:0',
        '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-threads','2',
        '-c:a','aac','-b:a','192k','-t',str(job['duration']),'-movflags','+faststart',
        '-metadata','comment=Experimental AI lip sync, manual mouth matte; existing recorded Sajad/synthetic Ava audio. User review required. No YouTube publication.',str(destination)]
   process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
   generated_change=False;temporal_change=False;first_signature=None
   try:
    for start in range(0,count,cfg['batchSize']):
     indices=range(start,min(start+cfg['batchSize'],count))
     audio=torch.stack([chunks[min(i,len(chunks)-1)] for i in indices])
     latents=torch.cat([latent]*len(indices),dim=0)
     predicted=unet.model(latents,torch.tensor([0],device=device),encoder_hidden_states=pe(audio)).sample
     if not torch.isfinite(predicted).all():raise RuntimeError('Non-finite model prediction; stop and review precision/settings')
     decoded=vae.decode_latents(predicted)
     for index,result in zip(indices,decoded):
      generated=context.copy();generated[y1:y2,x1:x2]=cv2.resize(result,(x2-x1,y2-y1),interpolation=cv2.INTER_LANCZOS4)
      generated=Image.fromarray(cv2.cvtColor(generated,cv2.COLOR_BGR2RGB))
      combined=blend_patch(base,generated,job,settings)
      if ImageChops.difference(combined,base).getbbox():generated_change=True
      signature=hashlib.sha256(combined.crop(tuple(job['sourceCropPixels'])).tobytes()).hexdigest()
      if first_signature is None:first_signature=signature
      elif signature!=first_signature:temporal_change=True
      frame=combined.transform((1280,720),Image.Transform.EXTENT,crop_box(base.size,settings['camera']),Image.Resampling.BICUBIC)
      if index in (0,count//2):frame.save(out/f'{role}-frame-{index:04d}.jpg',quality=95)
      process.stdin.write(frame.tobytes())
   finally:
    process.stdin.close();code=process.wait()
   if code:raise subprocess.CalledProcessError(code,cmd)
   if not generated_change or not temporal_change:raise RuntimeError('No changing mouth-region animation; not a successful test')
   subprocess.run([studio.FF,'-v','error','-i',str(destination),'-f','null','-'],check=True)
   results.append({'speaker':role,'file':destination.name,'duration':job['duration'],'frames':count,
    'sha256':sha(destination),'mouthRegionChanged':generated_change,'temporalMouthChange':temporal_change,'fullDecode':'PASS',
    'mouthMaskBoundingBox':mouth_mask((context.shape[1],context.shape[0]),settings).getbbox(),
    'lipSyncQuality':'UNVERIFIED: human listening and visual review required'})
   print('Rendered for review:',destination,flush=True)
 report={'status':'rendered_pilot_pending_user_lipsync_and_identity_review','engine':'MuseTalk V1.5 custom static-face pilot',
  'musetalkRevision':cfg['musetalkRevision'],'gpu':props.name,'torch':torch.__version__,'seed':cfg['seed'],
  'sourceEpisodeSha256':sha(EPISODE),'sourceImageSha256':sha(SOURCE),'results':results,
  'paidServiceUsed':False,'voiceRegenerated':False,'headOrBodyAnimation':False,'newCameraPerspective':False,
  'youtubePublished':False,'note':'Small experimental mouth patches only. Not full-episode production or automatic quality approval.'}
 (out/'pilot-results.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','models','infer'])
 p.add_argument('--musetalk',type=Path,default=Path('/content/MuseTalk'))
 args=p.parse_args()
 if args.stage=='prepare':prepare_inputs()
 elif args.stage=='models':download_models(args.musetalk.resolve())
 else:infer(args.musetalk.resolve())

"""Prepare direct WEB upload files, offline. Does not contact or invoke any demo."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 pilot=ROOT/'downloads/ahangban-ava-motion-pilot-inputs.zip'
 expected=json.loads((HERE.parent/'motion/bundle.json').read_text());assert sha(pilot.read_bytes())==expected['sha256']
 with zipfile.ZipFile(pilot) as z:
  m=json.loads(z.read('pilot-inputs.json'));image=z.read('ava.png');speech=z.read('talk-conditioning.wav')
 assert sha(image)==m['approvedActorSourceSha256']==m['files']['ava.png']['sha256']
 assert sha(speech)==m['files']['talk-conditioning.wav']['sha256']
 prompt=m['jobs'][0]['prompt']
 outputs={'downloads/ahangban-ava-web-image.png':image,'downloads/ahangban-ava-web-speech.wav':speech}
 for name,data in outputs.items():(ROOT/name).write_bytes(data)
 provenance=dict(status='WEB_UPLOAD_INPUTS_ONLY_NO_INFERENCE',demo='https://modelscope.cn/studios/BadToBest/EchoMimicV3',demoAvailabilityVerified=False,freeExecutionVerified=False,deployedVersionVerified=False,agentUploadedToDemo=False,agentInvokedModel=False,userInitiatedUploadRequired=True,processingNotice='User upload would send the synthetic Ava image/voice to third-party ModelScope demo, not previous Google Colab. No account access or auto-upload.',paidAccessAuthorized=False,publishAuthorized=False,modelImageSha256=sha(image),conditioningAudioSha256=sha(speech),sourceImageApproved=True,voice='voice-06',newImageOrSpeechGenerated=False,completeSpeechSeconds=4.48,fileDurationSeconds=4.84,sourcePilotBundleSha256=sha(pilot.read_bytes()),files={k:dict(sha256=sha(v),bytes=len(v)) for k,v in outputs.items()})
 (HERE/'manifest.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 files={'ava.png':image,'speech.wav':speech,'prompt.txt':(prompt+'\n').encode(),'README.fa.md':(HERE/'README.fa.md').read_bytes(),'provenance.json':(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n').encode()}
 target=ROOT/'downloads/ahangban-ava-web-upload.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in files.items():
   info=zipfile.ZipInfo(name,date_time=(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
 (HERE/'bundle.json').write_text(json.dumps(dict(file=str(target.relative_to(ROOT)),bytes=target.stat().st_size,sha256=sha(target.read_bytes())),indent=2)+'\n')
 print('Prepared direct web inputs only; no inference:',target.name)
if __name__=='__main__':main()

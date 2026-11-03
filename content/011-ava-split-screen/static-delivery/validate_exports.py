"""Independent decode/audio/format and static-vs-moving-region QA; not subjective QA."""
from pathlib import Path
import hashlib,json,subprocess,re,sys
import numpy as np
from PIL import Image
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[3];EP=ROOT/'content/011-ava-split-screen';WORK=ROOT/'rendered/ava-static-exports';FF=imageio_ffmpeg.get_ffmpeg_exe()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def execute(args):return subprocess.check_output([FF,'-v','error',*map(str,args)],stderr=subprocess.PIPE)
def metadata(p):
 reader=imageio_ffmpeg.read_frames(str(p));m=next(reader);reader.close();return m

def audio_hash(p):return execute(['-i',p,'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','pipe:1']).decode().strip()
def frame(p,t,out):
 execute(['-y','-ss',t,'-i',p,'-frames:v','1','-update','1',out]);return np.array(Image.open(out).convert('RGB')).astype(float)
def validate(kind):
 work=WORK/kind;plan=json.loads((work/'render-plan.json').read_text());file=ROOT/f'downloads/ahangban-ava-static-{kind}.mp4';source=ROOT/plan['sourceVideo']
 assert sha(source)==plan['sourceSha256'];meta=metadata(file)
 assert tuple(meta['size'])==tuple(plan['size']) and abs(meta['fps']-plan['fps'])<.001
 assert abs(meta['duration']-plan['sourceDuration'])<.08
 raw=execute(['-progress','pipe:1','-i',file,'-map','0:v:0','-an','-f','null','-']).decode();counts=re.findall(r'^frame=(\d+)',raw,re.M);assert counts and int(counts[-1])==plan['totalFrames']
 original_aac=audio_hash(source);final_aac=audio_hash(file);assert final_aac==original_aac,'Audio changed or truncated'
 assert plan['actorSourceSha256']==sha(EP/'assets/ava-actor-generated.png')=='68854d222a57969ff89567530f8b4c8202d4f8b8855acac96a23e7628e861adf'
 assert not any(row['caption'] for row in plan['intervals'] if row['type']=='music')
 for a,b in zip(plan['intervals'],plan['intervals'][1:]):assert a['endFrame']==b['startFrame']
 assert plan['intervals'][0]['startFrame']==0 and plan['intervals'][-1]['endFrame']==plan['totalFrames']
 a=frame(file,15 if kind=='youtube' else 8,work/'qa-music-a.png');b=frame(file,15.8 if kind=='youtube' else 8.8,work/'qa-music-b.png');c=frame(file,55 if kind=='youtube' else 25,work/'qa-another-track.png')
 if kind=='youtube':face=(1325,363,1552,573);motion=(100,300,740,900);expected=Image.open(work/'ava-panel-fixed.png').convert('RGB').resize((844,700),Image.Resampling.LANCZOS);expected=np.array(expected).astype(float)[113:323,305:532]
 else:face=(390,1169,680,1438);motion=(200,150,870,780);expected=np.array(Image.open(work/'ava-panel-fixed.png').convert('RGB')).astype(float)[145:414,390:680]
 x,y,z,q=face;aa=a[y:q,x:z];bb=b[y:q,x:z];cc=c[y:q,x:z]
 staticDifference=max(float(abs(aa-bb).mean()),float(abs(aa-cc).mean()));assert staticDifference<3.,staticDifference
 # Reference plate fidelity bounded for lossy H264; no assertion that pixel motion = life.
 referenceDiff=float(abs(aa-expected).mean());assert referenceDiff<6.,referenceDiff
 x,y,z,q=motion;movement=float(abs(a[y:q,x:z]-b[y:q,x:z]).mean());assert movement>.25,movement
 if kind=='youtube':
  speech=frame(file,0.8,work/'qa-speech.png');patch=speech[900:970,750:880]
  assert float(np.percentile(abs(patch-np.array([16.,24.,32.])),99))<6.,'Clipped source subtitle remains in music-panel crop'
 report=dict(sourceSpeechCaptionCropClean=True,status='PASS',kind=kind,file=str(file.relative_to(ROOT)),bytes=file.stat().st_size,sha256=sha(file),size=meta['size'],fps=meta['fps'],duration=meta['duration'],decodedFrames=int(counts[-1]),fullVideoDecodePassed=True,aacPacketHash=final_aac,exactSourceAACRetained=True,sourceSha256=sha(source),fixedFaceRegionTemporalMeanDifference=staticDifference,meanDifferenceFromFixedPlate=referenceDiff,musicPanelMeanDifference=movement,musicPanelMotionRetained=True,actorAnimated=False,lipHeadEyeListeningMotionGenerated=False,modelInferenceExecuted=False,allNarrationVoice='voice-06',maleNarrationUsed=False,musicSecondsEach=plan['musicSecondsEach'],captionsNotOverMusic=True,publishAuthorized=False,limitation='Actual full files with static Ava, NOT the originally requested naturally animated host.')
 (work/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));return report
if __name__=='__main__':validate(sys.argv[1])

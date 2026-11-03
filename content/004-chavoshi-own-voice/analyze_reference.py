"""Local technical checks and a private, conservative clone-reference export.
No network, transcription, identity inference, provider upload or cloning.
Requires imageio-ffmpeg. Derived audio stays under ignored rendered/.
"""
from pathlib import Path
import argparse,array,hashlib,json,math,re,shutil,subprocess,wave
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[2]
FF=imageio_ffmpeg.get_ffmpeg_exe()

def analyze(source,out):
 out.mkdir(parents=True,exist_ok=True)
 result=subprocess.run([FF,'-hide_banner','-i',str(source),'-vn','-af',
  'silencedetect=noise=-38dB:d=0.7,volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
 log=result.stderr
 decoded=subprocess.run([FF,'-v','error','-i',str(source),'-f','f32le','-c:a','pcm_f32le','-'],capture_output=True,check=True)
 samples=array.array('f',decoded.stdout)
 # Explicitly check decoded format instead of guessing from the m4a extension.
 assert re.search(r'Audio: aac.*48000 Hz, stereo',log)
 duration=len(samples)/(48000*2)
 starts=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)]
 ends=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
 assert len(starts)==len(ends)
 silence=sum(b-a for a,b in zip(starts,ends))
 peak=max(abs(x) for x in samples)
 mean=float(re.findall(r'mean_volume: ([\-\d.]+) dB',log)[-1])
 reference=out/'sajad-clone-reference.wav'
 subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-i',str(source),
  '-map_metadata','-1','-vn','-ac','1','-ar','48000','-af','volume=-3dB',
  '-c:a','pcm_s16le',str(reference)],check=True)
 with wave.open(str(reference)) as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(48000,1,2)
  assert abs(w.getnframes()/48000-duration)<.05
 report={'source':'studio/ahangban-signature/Presenters/Sajad/sajad.m4a',
  'sourceGitRevision':'ee2851d','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'sourceBytes':source.stat().st_size,'durationSeconds':duration,'codec':'AAC LC',
  'sampleRate':48000,'channels':2,'decodedMeanVolumeDbFS':mean,
  'decodedFloatPeakDbFS':20*math.log10(peak),
  'decodedSamplesAbsAtLeast1':sum(abs(x)>=1 for x in samples),
  'silenceThresholdDb':-38,'minimumDetectedSilenceSeconds':.7,
  'detectedSilenceSeconds':silence,'estimatedNonSilenceSeconds':duration-silence,
  'silenceIntervals':[{'start':a,'end':b} for a,b in zip(starts,ends)],
  'privateReference':'rendered/user-voice/sajad/sajad-clone-reference.wav',
  'referenceSha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
  'referenceProcessing':'Decode to 48kHz mono PCM16, -3dB gain, strip metadata; preserve all pauses. No denoising, pitch change, or claim of clipping repair.',
  'qualityCaution':'A few decoded AAC samples exceed full scale; this can be AAC overshoot, not proof of audible clipping. Gain reduction does not repair existing distortion.',
  'reviewLimitations':['No aural/phonetic review','No transcript verification','No speaker-count or identity verification','Noise/echo quality not established by silence statistics'],
  'cloneCreated':False,'providerUploadPerformed':False,'nextVideoRendered':False}
 (out/'audio-reference-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'studio/ahangban-signature/Presenters/Sajad/sajad.m4a')
 p.add_argument('--private-out',type=Path,default=ROOT/'rendered/user-voice/sajad')
 p.add_argument('--report-copy',type=Path);a=p.parse_args()
 # Prevent accidental derived/raw audio exports into public source directories.
 private=a.private_out.resolve();allowed=(ROOT/'rendered').resolve()
 if not private.is_relative_to(allowed):p.error('--private-out must be inside ignored rendered/')
 report=analyze(a.source.resolve(),private)
 if a.report_copy:a.report_copy.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

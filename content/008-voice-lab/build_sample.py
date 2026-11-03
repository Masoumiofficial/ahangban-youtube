"""Voice-only review. Constant gain and 280 ms between speakers; no video/music.
No EQ, compressor, reverb, pitch shift, time stretch or forced-alignment claims.
"""
import array,hashlib,json,math,shutil,subprocess,wave
from pathlib import Path
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];FF=imageio_ffmpeg.get_ffmpeg_exe();RATE=48000
ROWS=[
 {'file':'female-question.mp3','speaker':'female','voice':'voice-06','text':'چرا بعضی آهنگا رو هر چقدر می‌شنویم، باز دلمون می‌خواد از اول پخششون کنیم؟ مثلاً کجایی؛ تو با صداش ارتباط می‌گیری یا با حرفی که می‌زنه؟'},
 {'file':'male-response.mp3','speaker':'male','voice':'voice-07','text':'شاید هم یه خاطره رو یادت میاره. هم صدا مهمه، هم اون چیزی که آهنگ یادت می‌اندازه. ولی جوابش برای همه یکی نیست. تو کجایی رو که می‌شنوی، اول چی میاد توی ذهنت؟'},
 {'file':'female-pronunciation.mp3','speaker':'female','voice':'voice-06','text':'کجایی. سنگ صبور. امیر بی‌گزند. برقص آ. بیست هزار آرزو. رسانهٔ آهنگ‌بان. آهنگ‌بان دات آی آر.'}]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def decode(path):
 data=subprocess.check_output([FF,'-v','error','-i',str(path),'-ac','2','-ar',str(RATE),'-f','s16le','-'])
 pcm=array.array('h');pcm.frombytes(data);return pcm

def main():
 work=REPO/'rendered/voice-lab-008';work.mkdir(parents=True,exist_ok=True)
 output=REPO/'downloads/ahangban-voice-lab-dialogue.mp3';chunks=[];timeline=[];cursor=0.
 for row in ROWS[:2]:
  source=HERE/'audio'/row['file'];pcm=decode(source)
  assert pcm and len(pcm)%2==0
  rms=math.sqrt(sum(v*v for v in pcm)/len(pcm));peak=max(abs(v) for v in pcm);assert rms>20
  gain=min((.1*32768)/rms,(.84*32767)/max(peak,1))
  adjusted=array.array('h',(round(v*gain) for v in pcm));chunks.append(adjusted.tobytes());duration=len(pcm)/(RATE*2)
  timeline.append(dict(row,start=cursor,end=cursor+duration,sourceSha256=sha(source),constantGain=gain))
  cursor+=duration
  if len(timeline)==1:chunks.append(bytes(round(.28*RATE)*2*2));cursor+=.28
 wav=work/'dialogue.wav'
 with wave.open(str(wav),'wb') as w:w.setparams((2,2,RATE,0,'NONE','not compressed'));w.writeframes(b''.join(chunks))
 subprocess.run([FF,'-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(output)],check=True)
 pronunciation=REPO/'downloads/ahangban-voice-lab-pronunciation.mp3';source=HERE/'audio'/ROWS[2]['file'];shutil.copy2(source,pronunciation)
 for path in (output,pronunciation):
  pcm=decode(path);assert max(abs(v) for v in pcm)<32767;assert sum(v*v for v in pcm)/len(pcm)>400
 result={'status':'voice_only_sample_pending_user_listening','auditionSelections':{'female':'voice-06','male':'voice-07'},
  'selectionIsNotFullPerformanceApproval':True,'previous007SpeechAndHookRejected':True,'videoProductionPaused':True,
  'humanRecordingUsed':False,'personalCloneUsed':False,'musicUsed':False,'effectsUsed':False,
  'processing':'Constant per-speaker gain only; 280ms between speakers. Original pauses, speed and pitch preserved.',
  'dialogueDuration':cursor,'timeline':timeline,'pronunciationScript':ROWS[2],
  'outputs':[{ 'file':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size} for p in (output,pronunciation)],
  'technicalChecks':'Both MP3s decode, non-silent, no decoded clipping. Not aural or pronunciation approval.'}
 (HERE/'sample-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

"""Audit user-returned Colab pilot and refine Sajad's compositing only.
No model weights/inference, new speech, external upload or YouTube publication.
"""
import argparse,array,hashlib,json,math,subprocess,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import imageio_ffmpeg
import build_camera_demo as camera

REPO=camera.REPO
BLOB='06757ce5358114e1d0cf6db78cf6607bc19e28b4'
ALLOWED={'male-studio-pilot.mp4','female-studio-pilot.mp4','pilot-results.json','model-provenance.json'}
SOURCE=REPO/'downloads/ahangban-first-video-final.mp4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def unpack(path,root,expected_blob):
 data=path.read_bytes()
 blob=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
 if blob!=expected_blob:raise ValueError('Input does not match the GitHub blob supplied by the user')
 with zipfile.ZipFile(path) as z:
  names=[i.filename for i in z.infolist()]
  if len(names)!=4 or set(names)!=ALLOWED:raise ValueError('Unexpected ZIP contents')
  if sum(i.file_size for i in z.infolist())>100_000_000:raise ValueError('Oversized ZIP')
  if z.testzip() is not None:raise ValueError('ZIP CRC failure')
  for name in names:(root/name).write_bytes(z.read(name))
 return blob

def audio_match(video,start,duration):
 def read(path,offset):
  return array.array('h',subprocess.check_output([camera.studio.FF,'-v','error','-i',str(path),
   '-ss',str(offset),'-t',str(duration),'-map','0:a:0','-ac','1','-ar','16000','-f','s16le','-']))
 a=read(SOURCE,start);b=read(video,0);count=min(len(a),len(b));a=a[:count];b=b[:count]
 ea=sum(x*x for x in a);eb=sum(x*x for x in b)
 corr=sum(x*y for x,y in zip(a,b))/math.sqrt(ea*eb)
 if corr<.98:raise ValueError('Unexpected source audio or timing')
 return {'zeroLagCorrelation':corr,'samplesCompared':count,'review':'Audio content correspondence, NOT phonetic lip-sync approval'}

def reference_and_mask(settings,source_size):
 # Pixel coordinates relative to the original male pilot context, not output frame.
 # Restrict the edit to lips and immediate edge, restoring the chin/outer beard.
 im=Image.open(camera.SOURCE).convert('RGBA')
 for name in ('AHANGBAN-LOGO-GLOW.png','AHANGBAN-LOGO-CORE.png'):
  im=Image.alpha_composite(im,Image.open(camera.studio.STUDIO/'overlays'/name).convert('RGBA'))
 bbox=camera.crop_box(im.size,settings['hosts']['male']['camera'])
 reference=im.convert('RGB').transform(source_size,Image.Transform.EXTENT,bbox,Image.Resampling.BICUBIC)
 context=Image.new('L',(311,354));ImageDraw.Draw(context).ellipse((148,174,221,207),fill=255)
 context=context.filter(ImageFilter.GaussianBlur(2))
 full=Image.new('L',im.size);full.paste(context,(1405,907))
 mask=full.transform(source_size,Image.Transform.EXTENT,bbox,Image.Resampling.BICUBIC)
 return reference,mask

def refine_male(root,settings,duration):
 reader=imageio_ffmpeg.read_frames(str(root/'male-studio-pilot.mp4'))
 meta=next(reader);size=tuple(meta['size'])
 reference,mask=reference_and_mask(settings,size)
 reference.save(root/'male-original-reference.png');mask.save(root/'male-refined-mask.png')
 dest=root/'male-refined.mp4'
 cmd=[camera.studio.FF,'-v','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}',
  '-r','25','-i','pipe:0','-i',str(root/'male-studio-pilot.mp4'),'-map','0:v:0','-map','1:a:0',
  '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-threads','2','-c:a','copy',
  '-t',str(duration),'-movflags','+faststart','-metadata',
  'comment=User-returned real Colab lip sync; locally narrowed lip matte to preserve original Sajad beard. No new model inference.',str(dest)]
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE);count=0
 try:
  for data in reader:
   frame=Image.frombytes('RGB',size,data)
   result=Image.composite(frame,reference,mask)
   if count in (25,50,75):result.save(root/f'male-refined-{count:03d}.png')
   process.stdin.write(result.tobytes());count+=1
 finally:
  reader.close();process.stdin.close();code=process.wait()
 if code:raise subprocess.CalledProcessError(code,cmd)
 return dest,{'inputFrames':count,'refinedLipEllipseInInputContext':[148,174,221,207],
  'screenSpaceMaskBoundingBox':mask.getbbox(),'method':'Recomposite existing generated pixels only inside smaller feathered lip mask onto exact original reference',
  'newModelInference':False,'audio':'AAC copied from received male clip without re-encoding',
  'limitation':'May constrain jaw opening; human review needed. Not claimed as a final approved lip-sync result.'}

def review(path,root,expected_blob):
 root.mkdir(parents=True,exist_ok=True)
 blob=unpack(path,root,expected_blob)
 received=json.loads((root/'pilot-results.json').read_text())
 if received['sourceEpisodeSha256']!=sha(SOURCE):raise ValueError('Wrong source episode')
 if received['sourceImageSha256']!=sha(camera.SOURCE):raise ValueError('Wrong source image')
 settings=json.loads((camera.HERE/'colab/pilot-settings.json').read_text())
 jobs={r['speaker']:r for r in received['results']}
 if set(jobs)!={'male','female'}:raise ValueError('Both hosts required')
 checks=[]
 for role in ('male','female'):
  job=jobs[role];p=root/job['file']
  if job['file']!=f'{role}-studio-pilot.mp4' or sha(p)!=job['sha256']:raise ValueError('Wrong returned clip')
  subprocess.run([camera.studio.FF,'-v','error','-i',str(p),'-f','null','-'],check=True)
  reader=imageio_ffmpeg.read_frames(str(p));meta=next(reader);reader.close()
  if tuple(meta['size'])!=(1280,720) or meta['fps']!=25:raise ValueError('Unexpected video format')
  start=16.01 if role=='male' else 91.67485416666666
  checks.append({'speaker':role,'bytes':p.stat().st_size,'sha256':sha(p),'fullDecode':'PASS',
   'resolution':list(meta['size']),'fps':meta['fps'],'reportedDuration':job['duration'],
   'containerDuration':meta['duration'],'audioCheck':audio_match(p,start,job['duration'])})
 male,refinement=refine_male(root,settings,jobs['male']['duration'])
 review_video=root/'ahangban-lipsync-pilot-reviewed.mp4'
 # Two short inputs only. Re-encode to make one easy-to-review MP4, never a full episode.
 subprocess.run([camera.studio.FF,'-v','warning','-y','-filter_complex_threads','2','-i',str(male),
  '-i',str(root/'female-studio-pilot.mp4'),'-filter_complex',
  '[0:v]setpts=PTS-STARTPTS[v0];[0:a]asetpts=PTS-STARTPTS[a0];[1:v]setpts=PTS-STARTPTS[v1];[1:a]asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]',
  '-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','20','-threads','2',
  '-c:a','aac','-b:a','192k','-pix_fmt','yuv420p','-movflags','+faststart','-metadata',
  'comment=Two-host lip-sync PILOT review: Sajad beard-preserving local matte refinement, then original returned Ava. No full-episode render or YouTube publication.',str(review_video)],check=True)
 subprocess.run([camera.studio.FF,'-v','error','-i',str(review_video),'-f','null','-'],check=True)
 reader=imageio_ffmpeg.read_frames(str(review_video));preview_meta=next(reader);reader.close()
 report={'status':'returned_real_pilot_technically_verified_local_matte_refined_pending_user_review',
  'sourceUrl':'https://github.com/Masoumiofficial/ahangban-youtube/blob/main/ahangban-lipsync-pilot.zip',
  'sourceGitBlob':blob,'sourceZipSha256':sha(path),'checks':checks,'reportedGpu':received['gpu'],
  'reportedTorch':received['torch'],'musetalkRevision':received['musetalkRevision'],
  'modelProvenance':'Received model-provenance.json; weight hashes recorded by user Colab, not re-downloaded/independently checked here',
  'visualReview':'Sampled returned frames show mouth changes; Sajad lip/chin beard texture differs from original. Narrower local mouth matte restores original beard outside lips. Ava microphone appears unchanged in sampled frames.',
  'refinement':refinement,'preview':review_video.name,'previewSha256':sha(review_video),
  'previewOrder':['Sajad, locally refined mouth matte','Ava, original returned clip'],
  'previewMetadata':{'resolution':list(preview_meta['size']),'fps':preview_meta['fps'],'duration':preview_meta['duration'],'fullDecode':'PASS'},
  'lipSyncPhoneticOrAuralApproval':False,'userApproval':False,'fullEpisodeRenderedWithLipSync':False,
  'headOrBodyAnimation':False,'newCameraPerspective':False,'agentExecutedModelInference':False,'youtubePublished':False}
 (root/'review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return review_video

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input-zip',type=Path,default=REPO/'rendered/received-lipsync-pilot/ahangban-lipsync-pilot.zip')
 p.add_argument('--output-root',type=Path,default=REPO/'rendered/received-lipsync-pilot');p.add_argument('--source-blob',default=BLOB)
 a=p.parse_args();review(a.input_zip.resolve(),a.output_root.resolve(),a.source_blob)

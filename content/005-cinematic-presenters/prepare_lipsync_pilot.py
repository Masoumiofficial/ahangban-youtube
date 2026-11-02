"""Prepare LOCAL pilot inputs only. Does NOT implement or run lip sync.
Never downloads weights, uses a service, changes a voice or publishes private cuts.
"""
import argparse, hashlib, json, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from build_camera_demo import REPO, SOURCE, EPISODE, studio

HERE=Path(__file__).resolve().parent
TIMELINE=HERE.parent/'004-chavoshi-own-voice/delivery/timeline.json'
# Manual draft source-image face context. NOT approved compositing masks.
ROIS={'male':(.366,.420,.447,.584),'female':(.553,.422,.638,.588)}

def pilot_jobs(timeline):
    events={e['id']:e for e in timeline['events'] if e['type']=='speech'}
    male=events['02'];female=events['05']
    # Complete first sentence from the existing pause-estimated subtitle window.
    cap=next(c for c in timeline['captions'] if abs(c['start']-female['start'])<.0001)
    return [dict(speaker='male',id='02',start=male['start'],end=male['end'],text=male['text']),
            dict(speaker='female',id='05',start=female['start'],end=cap['end']+.035,text=cap['text'])]

def prepare(output):
    # The existing ignore rule is a deliberate privacy boundary: no standalone
    # user voice exports or face processing inputs in public downloads/.
    output=output.resolve();private=REPO/'rendered'
    if not output.is_relative_to(private):raise ValueError('Pilot inputs must stay under ignored rendered/')
    output.mkdir(parents=True,exist_ok=True)
    timeline=json.loads(TIMELINE.read_text());image=Image.open(SOURCE).convert('RGB')
    report={'status':'inputs_prepared_ONLY_no_lipsync_inference','engineExecuted':False,
            'voiceRegenerated':False,'thirdPartyUpload':False,'subscriptionAllowed':False,
            'sourceEpisodeSha256':hashlib.sha256(EPISODE.read_bytes()).hexdigest(),
            'sourceImageSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'inputs':[]}
    for job in pilot_jobs(timeline):
        role=job['speaker'];crop=tuple(round(v*image.size[i%2]) for i,v in enumerate(ROIS[role]))
        face=output/f'{role}-single-face-input.png'
        context=image.crop(crop)
        # Suppress gallery portraits in the corners so face detection cannot
        # pick a background singer. This is engine context, NOT a paste-back mask.
        w,h=context.size
        oval=(.18*w,.02*h,.96*w,.85*h) if role=='male' else (.07*w,.03*h,.88*w,.77*h)
        mask=Image.new('L',context.size);ImageDraw.Draw(mask).ellipse(oval,fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(2))
        neutral=Image.new('RGB',context.size,(28,32,36))
        neutral.paste(context,(0,0),mask);neutral.save(face)
        audio=output/f'{role}-speech.wav';duration=job['end']-job['start']
        subprocess.run([studio.FF,'-v','error','-y','-i',str(EPISODE),'-ss',f'{job["start"]:.9f}',
            '-t',f'{duration:.9f}','-map','0:a:0','-ac','1','-ar','16000','-c:a','pcm_s16le',str(audio)],check=True)
        with wave.open(str(audio)) as w:
            assert w.getnchannels()==1 and w.getframerate()==16000 and w.getsampwidth()==2
            assert abs(w.getnframes()/w.getframerate()-duration)<1/16000+.00001
        report['inputs'].append({**job,'duration':duration,'audio':audio.name,'image':face.name,
            'audioSha256':hashlib.sha256(audio.read_bytes()).hexdigest(),
            'imageSha256':hashlib.sha256(face.read_bytes()).hexdigest(),
            'sourceCropPixels':crop,'backgroundPortraitsSuppressed':True,
            'inputIsolationMaskIsNotCompositingMask':True,'compositeMaskApproved':False,
            'review':'Audio boundary estimated from timeline, not aural confirmation; face context requires visual calibration'})
    (output/'pilot-inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('INPUTS ONLY; no mouth animation or model inference:',output)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,default=REPO/'rendered/lipsync-pilot-inputs')
    prepare(p.parse_args().output_root)

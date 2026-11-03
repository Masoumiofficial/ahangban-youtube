"""Mic-only local composition revision. Approved actor pixels/pose are NOT regenerated."""
import json,hashlib
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import build_layout as b
MIC=b.HERE/'assets/microphone-natural.png';WORK=b.ROOT/'rendered/ava-mic-revision';BOX=(1950,730,2910,1526)
FACE=(390,145,680,414)
def microphone():
 a=np.array(Image.open(MIC).convert('RGB')).astype(np.float32)
 excess=a[:,:,1]-np.maximum(a[:,:,0],a[:,:,2]);alpha=1-np.clip((excess-16)/105,0,1)
 a[:,:,1]=np.minimum(a[:,:,1],np.maximum(a[:,:,0],a[:,:,2])+1)
 rgba=Image.fromarray(np.dstack((np.uint8(np.clip(a,0,255)),np.uint8(alpha*255))),'RGBA')
 rgba.thumbnail((660,360),Image.Resampling.LANCZOS);return rgba
def clean_studio():
 original=Image.open(b.STUDIO).convert('RGB').crop(BOX);mask=Image.new('L',original.size);d=ImageDraw.Draw(mask)
 # The existing props alone, all below the gallery; no portrait or wall architecture edits.
 d.ellipse((17,460,150,595),fill=255);d.rectangle((109,430,165,600),fill=255)
 d.polygon([(73,443),(184,442),(191,558),(76,563)],fill=255)
 d.line([(128,446),(128,400),(142,384),(164,389),(181,406),(171,460)],fill=255,width=15)
 d.line([(159,413),(437,387),(452,409)],fill=255,width=27)
 d.line([(172,438),(441,397)],fill=255,width=19)
 d.line([(443,402),(418,742)],fill=255,width=33)
 d.polygon([(397,707),(459,701),(469,796),(398,796)],fill=255)
 d.polygon([(107,373),(454,372),(472,429),(166,460),(107,460)],fill=255)
 d.ellipse((10,420,199,614),fill=255)
 # Enforce immutable gallery pixels, whose bottom is above this mask boundary.
 d.rectangle((0,0,960,371),fill=0)
 rgb=np.array(original);m=np.array(mask)
 clean=cv2.inpaint(rgb,m,5,cv2.INPAINT_TELEA)
 # Telea may pull bright chair pixels into the dark wall around a large filter.
 # Clone ONLY original clean wall texture through the same bounded prop mask,
 # above desk level; no AI room/portrait generation and no master overwrite.
 wall=original.crop((912,372,952,735)).resize((960,363),Image.Resampling.BICUBIC)
 wall_array=np.array(wall);region=clean[372:735];area=m[372:735]>0
 region[area]=wall_array[area];clean[372:735]=region
 assert np.array_equal(clean[m==0],rgb[m==0])
 WORK.mkdir(parents=True,exist_ok=True);Image.fromarray(clean).save(WORK/'clean-prop-area.png');mask.save(WORK/'old-prop-mask.png')
 return Image.fromarray(clean).convert('RGBA')
def studio_panel():
 original=clean_studio();size=(1080,896);bg=original.resize(size,Image.Resampling.LANCZOS)
 actor=b.key_actor();actor.thumbnail((930,930),Image.Resampling.LANCZOS);bg.alpha_composite(actor,((1080-actor.width)//2,8))
 # Retain original desk/mixer only; do NOT reintroduce the old boom over her neck.
 mask=Image.new('L',(1365,768));d=ImageDraw.Draw(mask);d.rectangle((0,522,1365,768),fill=255)
 d.polygon([(608,518),(613,505),(743,505),(756,523),(756,536),(607,535)],fill=255)
 mask=mask.resize((3840,2160),Image.Resampling.LANCZOS).crop(BOX).resize(size,Image.Resampling.LANCZOS)
 bg=Image.composite(original.resize(size,Image.Resampling.LANCZOS),bg,mask)
 mic=microphone();shadow=Image.new('RGBA',size);s=Image.new('RGBA',mic.size,(0,0,0,0));s.putalpha(mic.getchannel('A').point(lambda a:round(a*.16)));shadow.alpha_composite(s,(-154,440));shadow=shadow.filter(ImageFilter.GaussianBlur(4));bg=Image.alpha_composite(bg,shadow);bg.alpha_composite(mic,(-160,435))
 assert bg.crop(FACE).tobytes()==b.studio_panel().crop(FACE).tobytes(),'Approved face pixels changed'
 bg.save(WORK/'approved-face-mic-v2-panel.png');return bg

def main():
 previous={r['path']:b.sha(b.ROOT/r['path']) for r in json.loads((b.HERE/'layout-manifest.json').read_text())['outputs']}
 b.main(studio_panel,'ahangban-ava-layout-v2','layout-v2-manifest.json')
 p=b.HERE/'layout-v2-manifest.json';m=json.loads(p.read_text());m.update(userFaceApprovalPending=False,userApprovedFaceAndLayout=True,approvalSource='آره خوبه فقط میکروفون رو یکم طبیعی تر بکن',micRevisionRequested=True,micRevisionUserReviewPending=True,microphoneSourceSha256=b.sha(MIC),micActorOcclusion='Below and left of face, no face overlap',approvedFaceROI=list(FACE),approvedActorSourceUnchanged=True,previousLayoutOutputsUnchanged=previous,backgroundRepair='Bounded old-prop mask below gallery only: original clean wall texture clone above desk plus Telea at base; original master unchanged',motionUserAuthorized=True,motionInferenceExecuted=False)
 assert all(b.sha(b.ROOT/k)==v for k,v in previous.items())
 p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

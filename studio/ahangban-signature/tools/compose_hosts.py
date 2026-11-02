"""Composite reviewed presenter silhouettes without regenerating the approved set.
Coordinates describe the 1365x768 generation plate. No empty-master overwrite.
"""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
ROOT=Path(__file__).resolve().parents[1]
SIZE=(3840,2160)
POLYGONS={
 'Sajad': [(464,521),(466,470),(472,431),(480,418),(507,406),(530,394),(530,383),(526,373),(524,359),(527,346),(527,335),(532,325),(543,319),(558,317),(574,321),(584,328),(589,339),(589,355),(593,358),(591,369),(586,376),(586,389),(599,402),(625,411),(635,422),(644,451),(651,480),(651,521)],
 'Ava': [(742,521),(747,479),(757,443),(767,423),(785,413),(792,396),(795,376),(798,349),(802,335),(814,324),(830,319),(848,322),(861,332),(870,349),(872,373),(878,393),(886,413),(905,424),(916,445),(922,477),(930,521)]
}
OFFSETS={'Sajad':(7,0),'Ava':(-25,0)}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 base=Image.open(ROOT/'master/MASTER-VIEW-001.png').convert('RGBA')
 source=Image.open(ROOT/'working/HOSTS-VIEW-001-generated.png').convert('RGBA')
 assert source.size==(1365,768)
 hosts=Image.new('RGBA',source.size)
 for name,points in POLYGONS.items():
  mask=Image.new('L',source.size);ImageDraw.Draw(mask).polygon(points,fill=255)
  mask=mask.filter(ImageFilter.GaussianBlur(.55))
  # Slightly smaller seated scale, anchored at the same desk line. Keep the
  # supplied face geometry; harmonize only exposure, color and edge softness.
  person=ImageEnhance.Brightness(source.convert('RGB')).enhance(.94)
  person=ImageEnhance.Contrast(person).enhance(.97)
  person=ImageEnhance.Color(person).enhance(.96).convert('RGBA')
  person.putalpha(mask)
  box=mask.getbbox();person=person.crop(box)
  person=person.resize((round(person.width*.95),round(person.height*.95)),Image.Resampling.LANCZOS)
  dx,dy=OFFSETS[name]
  position=(round((box[0]+box[2]-person.width)/2)+dx,box[3]-person.height+dy)
  # Restrained contact shadow against the existing chair/back wall.
  shadow=Image.new('RGBA',person.size,(0,0,0,0))
  shadow.putalpha(person.getchannel('A').filter(ImageFilter.GaussianBlur(2.5)).point(lambda a:round(a*.12)))
  hosts.alpha_composite(shadow,(position[0]+2,position[1]+2))
  hosts.alpha_composite(person,position)
 # Original desk and foreground equipment must occlude the presenters.
 foreground=Image.new('L',source.size);d=ImageDraw.Draw(foreground)
 d.rectangle((0,522,1365,768),fill=255)
 d.polygon([(539,515),(544,506),(555,503),(580,502),(590,509),(594,522),(539,533)],fill=255)
 d.polygon([(608,518),(613,505),(743,505),(756,523),(756,536),(607,535)],fill=255)
 d.rectangle((772,507,846,534),fill=255)
 d.ellipse((704,430,737,469),fill=255)
 d.rectangle((735,418,745,468),fill=255)
 d.line([(739,424),(744,402),(750,399),(850,397),(854,404),(845,530)],fill=255,width=6)
 d.line([(747,409),(846,399)],fill=255,width=3)
 hosts.putalpha(ImageChops.subtract(hosts.getchannel('A'),foreground))
 hosts=hosts.resize(SIZE,Image.Resampling.LANCZOS)
 out=ROOT/'productions';out.mkdir(exist_ok=True)
 hosts.save(out/'HOSTS-VIEW-001-layer.png')
 result=Image.alpha_composite(base,hosts).convert('RGB')
 result.save(out/'HOSTS-VIEW-001.png')
 result.resize((1600,900),Image.Resampling.LANCZOS).save(out/'HOSTS-VIEW-001-preview.jpg',quality=94)
 # Pixel-exact base preservation outside presenter alpha, not a visual claim.
 delta=ImageChops.difference(result,base.convert('RGB'))
 outside=hosts.getchannel('A').point(lambda a:255 if a==0 else 0)
 assert not ImageChops.multiply(delta,Image.merge('RGB',(outside,)*3)).getbbox()
 info={'version':'1.1','status':'user_requested_realism_revision_for_video','realismAdjustments':{'seatedScale':0.95,'exposureMultiplier':0.94,'contrastMultiplier':0.97,'saturationMultiplier':0.96,'contactShadowOpacity':0.12},'camera':'Same approved frontal master; no new camera angle',
  'base':'master/MASTER-VIEW-001.png','baseSha256':sha(ROOT/'master/MASTER-VIEW-001.png'),
  'seatingFromCamera':{'left':'Sajad','right':'Ava'},
  'source':'working/HOSTS-VIEW-001-generated.png','sourceSha256':sha(ROOT/'working/HOSTS-VIEW-001-generated.png'),
  'layer':'productions/HOSTS-VIEW-001-layer.png','layerSha256':sha(out/'HOSTS-VIEW-001-layer.png'),
  'composite':'productions/HOSTS-VIEW-001.png','compositeSha256':sha(out/'HOSTS-VIEW-001.png'),
  'checks':['Empty master unchanged','Pixels outside presenter alpha exactly match approved master','Original equipment foreground restored'],
  'limitations':['AI-generated presenter appearance requires user review; not an identity-exact 3D rig','Presenter source generated at 1365x768 and resampled to 4K; not native 4K human detail','Static image only; no voice, lip sync, neon animation or video integration']}
 (out/'shot-manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 print('PASS: hosts composited; approved set preserved outside silhouettes; base untouched.')
if __name__=='__main__':main()

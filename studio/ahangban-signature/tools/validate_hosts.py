"""Validate the host composite without treating automated checks as face QA."""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--shot',choices=['001','002'],default='001');args=parser.parse_args()
 manifest='shot-manifest-002.json' if args.shot=='002' else 'shot-manifest.json'
 info=json.loads((ROOT/'productions'/manifest).read_text())
 env=json.loads((ROOT/'environment-lock.json').read_text())
 assert env['approvalStatus']=='approved' and env['additionalCameraViewsGenerated']==0
 assert sha(ROOT/'Presenters/character-lock.json')==env['presenterIdentityLockSha256']
 people=json.loads((ROOT/'Presenters/character-lock.json').read_text())
 assert people['seatAssignment']['left']=='Sajad' and people['seatAssignment']['right']=='Ava'
 for pathkey,hashkey in [('base','baseSha256'),('source','sourceSha256'),('layer','layerSha256'),('composite','compositeSha256')]:
  assert sha(ROOT/info[pathkey])==info[hashkey],pathkey
 assert info['baseSha256']==env['masterSha256']
 base=Image.open(ROOT/info['base']).convert('RGBA')
 hosts=Image.open(ROOT/info['layer']).convert('RGBA')
 output=Image.open(ROOT/info['composite']).convert('RGB')
 assert base.size==hosts.size==output.size==(3840,2160)
 expected=Image.alpha_composite(base,hosts).convert('RGB')
 assert output.tobytes()==expected.tobytes()
 alpha=hosts.getchannel('A');outside=alpha.point(lambda a:255 if a==0 else 0)
 delta=ImageChops.difference(output,base.convert('RGB'))
 assert not ImageChops.multiply(delta,Image.merge('RGB',(outside,)*3)).getbbox()
 assert not alpha.crop((0,0,3840,850)).getbbox(), 'No room/logo edits'
 assert not alpha.crop((0,1500,3840,2160)).getbbox(), 'Desk/floor remain original'
 assert alpha.crop((1200,850,1900,1500)).getbbox() and alpha.crop((1950,850,2650,1500)).getbbox()
 if args.shot=='002':
  assert sha(ROOT/info['wardrobeEditSource'])==info['wardrobeEditSourceSha256']
  previous=Image.open(ROOT/'productions/HOSTS-VIEW-001.png').convert('RGB')
  # Sajad's face and all of Ava must remain pixel-identical to the approved composition.
  assert output.crop((1450,885,1710,1125)).tobytes()==previous.crop((1450,885,1710,1125)).tobytes(), 'Face changed'
  assert output.crop((1950,850,2750,1490)).tobytes()==previous.crop((1950,850,2750,1490)).tobytes(), 'Ava changed'
  assert output.tobytes()!=previous.tobytes(), 'Wardrobe edit missing'
 print('PASS: same approved empty master; separate two-host layer; exact compositing; set unchanged outside silhouettes; left Sajad / right Ava. Face approval remains manual.')
if __name__=='__main__':main()

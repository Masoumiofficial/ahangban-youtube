import importlib.util,json,unittest
from pathlib import Path
from PIL import Image,ImageChops

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('colab_pilot',HERE/'colab/run_pilot.py')
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)

class ColabPilotTests(unittest.TestCase):
 def setUp(self):self.settings=json.loads(pilot.SETTINGS.read_text())
 def test_existing_assets_match_exact_approved_versions(self):
  pilot.verify_assets()
 def test_manual_masks_preserve_mic_and_eyes(self):
  for role,config in self.settings['hosts'].items():
   mask=pilot.mouth_mask((326,359),config)
   self.assertIsNotNone(mask.getbbox())
   self.assertIsNone(mask.crop((0,config['protectFromY'],326,359)).getbbox())
   self.assertIsNone(mask.crop((0,0,326,130)).getbbox())
 def test_compositing_changes_only_one_small_patch(self):
  base=Image.new('RGB',(1000,1000),(10,20,30))
  patch=Image.new('RGB',(326,359),(200,190,180))
  job={'sourceCropPixels':[200,300,526,659]}
  config=self.settings['hosts']['female']
  result=pilot.blend_patch(base,patch,job,config)
  delta=ImageChops.difference(base,result)
  x,y,r,b=delta.getbbox()
  self.assertTrue(200<=x<r<=526)
  self.assertTrue(300<=y<b<=300+config['protectFromY'])
  self.assertIsNone(delta.crop((0,0,200,1000)).getbbox())
  self.assertEqual(base.getpixel((350,480)),(10,20,30)) # source not mutated
 def test_geometry_is_only_calibrated_for_two_known_hosts(self):
  self.assertEqual(set(self.settings['hosts']),{'male','female'})
  self.assertEqual(self.settings['batchSize'],2)
  for config in self.settings['hosts'].values():
   left,top,right,bottom=config['faceBox']
   self.assertTrue(0<=left<right<=311)
   self.assertTrue(0<=top<bottom<=354)
 def test_notebook_code_compiles_and_is_not_reported_as_executed(self):
  path=HERE/'colab/AhangBan-LipSync-Pilot.ipynb'
  if not path.exists():self.skipTest('Notebook generated after runner commit is pinned')
  nb=json.loads(path.read_text())
  for index,cell in enumerate(nb['cells']):
   if cell['cell_type']=='code':
    compile(''.join(cell['source']),f'cell-{index}','exec')
    self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])
  first=next(c for c in nb['cells'] if c['cell_type']=='code')
  self.assertIn('FREE_RUNTIME_CONFIRMED = False',''.join(first['source']))
  self.assertIn('GOOGLE_PROCESSING_CONFIRMED = False',''.join(first['source']))

if __name__=='__main__':unittest.main()

"""Small deterministic checks; full media QA is validate_video.py."""
import json, tempfile, unittest
from pathlib import Path
import build_video as build
import timing

class RenderTests(unittest.TestCase):
 def test_clock_carry(self):
  self.assertEqual(timing.clock(59.9999),'00:01:00,000')
  self.assertEqual(timing.clock(61.12,True),'0:01:01.12')
 def test_chunks_preserve_script(self):
  rows=json.loads((build.HERE/'dialogue.fa.json').read_text())
  for row in rows:
   chunks=timing.text_chunks(row['text'])
   self.assertEqual(' '.join(c[0] for c in chunks).split(),row['text'].split())
   self.assertEqual(chunks[0][1],0)
   self.assertEqual(chunks[-1][2],len(row['text']))
 def test_wrapping_preserves_words(self):
  s='این یک متن فارسی برای بررسی حفظ دقیق کلمات در زیرنویس چندخطی ویدیو است.'
  self.assertEqual(timing.wrap(s).split(),s.split())
 def test_tracks_are_five_twelve_second_samples(self):
  tracks=json.loads((build.HERE/'tracks.json').read_text())
  self.assertEqual(len({t['id'] for t in tracks}),5)
  self.assertEqual([t['excerptDuration'] for t in tracks],[12]*5)
  self.assertEqual([t['excerptStart'] for t in tracks],[45,40,50,35,40])
 def test_old_male_voice_cannot_be_selected_implicitly(self):
  rows=json.loads((build.HERE/'dialogue.fa.json').read_text())
  self.assertEqual({r['id'] for r in rows if r['speaker']=='male'},{'02','10','11','06'})
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   with self.assertRaisesRegex(FileNotFoundError,'no silent fallback'):
    build.prepare_inputs(root,[],[next(r for r in rows if r['speaker']=='male')],root/'old',root/'new')
 def test_render_command_is_bounded_single_video_stream(self):
  with tempfile.TemporaryDirectory() as temp:
   command=build.render_command(Path(temp),280.3)
   self.assertEqual(command[command.index('-f')+1],'rawvideo')
   self.assertIn('pipe:0',command)
   self.assertNotIn('-filter_complex',command)
   self.assertIn('yuv420p',' '.join(command))
   self.assertNotIn('voice-01',' '.join(command))
if __name__=='__main__':unittest.main()

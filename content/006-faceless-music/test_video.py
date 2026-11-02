import json,tempfile,unittest,wave
from pathlib import Path
import numpy as np
import build_video as build

class FacelessVideoTests(unittest.TestCase):
 def test_full_episode_keeps_audio_timeline_and_all_speech(self):
  plan=build.make_plan('youtube');original=json.loads((build.OLD/'timeline.json').read_text())
  self.assertEqual(plan['duration'],original['duration']);self.assertEqual(plan['captions'],original['captions'])
  self.assertEqual(len([e for e in plan['events'] if e['type']=='speech']),11)
  self.assertEqual(len([e for e in plan['events'] if e['type']=='music']),5)
 def test_native_reel_contains_both_existing_hosts_and_five_tracks(self):
  plan=build.make_plan('reel')
  self.assertGreater(plan['duration'],30);self.assertLess(plan['duration'],40)
  speech=[e for e in plan['events'] if e['type']=='speech']
  self.assertEqual([e['speaker'] for e in speech],['male','female'])
  self.assertEqual(len(plan['captions']),2)
  self.assertEqual(len([e for e in plan['events'] if e['type']=='music']),5)
 def test_reel_extracts_only_authorized_existing_music_windows(self):
  original=build.make_plan('youtube');music={e['scene']:e for e in original['events'] if e['type']=='music'}
  for e in build.make_plan('reel')['events']:
   if e['type']=='music':
    source=music[e['scene']]
    self.assertGreaterEqual(e['sourceStart'],source['start'])
    self.assertLessEqual(e['sourceStart']+e['duration'],source['end'])
    self.assertEqual(e['duration'],5)
 def test_reel_segments_have_no_overlap(self):
  plan=build.make_plan('reel');previous=0
  for e in plan['events']:
   self.assertAlmostEqual(e['start'],previous);previous=e['end']
  self.assertAlmostEqual(plan['duration'],previous)
 def test_source_presenter_video_can_only_be_read_as_audio(self):
  for kind in ('youtube','reel'):
   command=build.command(Path('/tmp/check-command'),kind,20)
   maps=[command[i+1] for i,s in enumerate(command) if s=='-map']
   self.assertEqual(maps,['0:v:0','1:a:0'])
   self.assertIn('libx264',command)
   self.assertNotIn('HOSTS-VIEW',str(command))
  command=build.command(Path('/tmp/check-command'),'youtube',20)
  self.assertEqual(command[command.index('-c:a')+1],'copy')
 def test_caption_text_fits_vertical_safe_region(self):
  maximum=760
  for c in build.make_plan('reel')['captions']:
   size=48;wrapped=build.lines(c['text'],size,maximum)
   while len(wrapped)>2:size-=1;wrapped=build.lines(c['text'],size,maximum)
   self.assertLessEqual(len(wrapped),2)
   for line in wrapped:self.assertLessEqual(build.width(line,size,True),maximum+35)
   panel_width=maximum+60;x=round((88+920-panel_width)/2)
   self.assertGreaterEqual(x,88);self.assertLessEqual(x+panel_width,920)
 def test_spectrum_is_audio_driven_and_silence_is_zero(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'test.wav';rate=48000
   tone=(np.sin(np.arange(rate)*2*np.pi*440/rate)*.2*32767).astype('<i2')
   def write(signal):
    stereo=np.repeat(signal[:,None],2,axis=1)
    with wave.open(str(path),'wb') as w:w.setparams((2,2,rate,0,'NONE','not compressed'));w.writeframes(stereo.tobytes())
   write(tone);a=build.spectrum(path,30,1)
   self.assertEqual(a.shape,(30,48));self.assertGreater(float(a.max()),.5)
   write(np.zeros(rate,dtype='<i2'));b=build.spectrum(path,30,1)
   self.assertEqual(float(b.max()),0)
 def test_original_episode_source_is_unchanged(self):
  self.assertEqual(build.sha(build.SOURCE),build.SOURCE_SHA)
 def test_delivered_outputs_match_qa_and_native_geometry(self):
  manifest=json.loads((build.HERE/'delivery/manifest.json').read_text())
  for kind,output in manifest['outputs'].items():
   self.assertEqual(build.sha(build.REPO/output['video']),output['sha256'])
   self.assertEqual(tuple(output['resolution']),build.SIZES[kind])
   self.assertEqual(output['fps'],build.FPS[kind])
  for field in ('presenterImagesUsed','studioImagesUsed','newSpeechGenerated','youtubePublished','instagramPublished','copyrightCleared'):
   self.assertFalse(manifest[field],field)
 def test_face_pilot_is_not_the_active_production_direction(self):
  plan=json.loads((build.HERE/'production-plan.json').read_text())
  self.assertTrue(plan['userRejectedPresenterPilot'])
  self.assertTrue(plan['presenterLipSyncWorkStopped'])
  self.assertTrue(plan['youtubeComplete']);self.assertTrue(plan['reelComplete'])
  self.assertFalse(plan['subscriptionOrPaidServiceUsed'])
 def test_farsi_wrapping_preserves_all_words(self):
  for plan in (build.make_plan('youtube'),build.make_plan('reel')):
   for c in plan['captions']:
    self.assertEqual(' '.join(build.lines(c['text'],43,760)).split(),c['text'].split())

if __name__=='__main__':unittest.main()

import unittest
from build_camera_demo import SHOTS, DURATION, framing, crop_box

class CameraTests(unittest.TestCase):
    def test_shots_are_contiguous(self):
        self.assertEqual(SHOTS[0][0],0)
        self.assertEqual(SHOTS[-1][1],DURATION)
        for a,b in zip(SHOTS,SHOTS[1:]):self.assertEqual(a[1],b[0])
    def test_every_crop_stays_in_frame_and_keeps_aspect_ratio(self):
        for i in range(2801):
            _,state=framing(i/100)
            x,y,r,b=crop_box((3840,2160),state)
            self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
            self.assertLessEqual(r,3840);self.assertLessEqual(b,2160)
            self.assertAlmostEqual((r-x)/(b-y),16/9)
    def test_host_switch_uses_actual_speech_boundaries(self):
        self.assertIn('Sajad',framing(16.01)[0])
        self.assertIn('Sajad',framing(22.54)[0])
        self.assertIn('Ava',framing(22.543708333333335)[0])
    def test_smoothstep_reaches_both_endpoints(self):
        for start,end,_,a,b in SHOTS:
            self.assertEqual(framing(start)[1],a)
            for x,y in zip(framing(end-1e-7)[1],b):self.assertAlmostEqual(x,y,places=6)

if __name__=='__main__':unittest.main()

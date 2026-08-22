import unittest
import numpy as np
from audio_engine import RealtimeAutoTune


class AudioAlgorithmTests(unittest.TestCase):
    def setUp(self):
        self.e = RealtimeAutoTune(sample_rate=48000, block_size=2048)
        self.t = np.arange(2048, dtype=np.float32) / 48000

    def tone(self, hz):
        return (0.25 * np.sin(2 * np.pi * hz * self.t)).astype(np.float32)

    def test_doi_cao_do_a4(self):
        hz = self.e._detect_pitch(self.tone(440.0))
        self.assertTrue(abs(hz - 440.0) < 8.0, f"Dò được {hz} Hz")

    def test_doi_cao_do_a4_quoc_te(self):
        hz = self.e._detect_pitch(self.tone(220.0))
        self.assertTrue(abs(hz - 220.0) < 6.0, f"Dò được {hz} Hz")

    def test_quantize_ve_not_c(self):
        self.e.key = 0; self.e.scale_name = "Chromatic"
        target = self.e._nearest_scale_hz(260.0)
        self.assertTrue(abs(target - 261.63) < 3.0, f"Mục tiêu {target} Hz")

    def test_chong_be_co_tin_hieu(self):
        x = self.tone(440.0); self.e.harmony_mode = "Bè 3"; self.e.harmony_level = 0.35
        y = self.e._voice(x)
        self.assertGreater(float(np.sqrt(np.mean(y * y))), 0.02)
        self.assertFalse(np.allclose(x, y), "Chồng bè không tạo thay đổi")

    def test_delay_co_am_lap(self):
        x = np.zeros(2048, dtype=np.float32); x[0] = 1.0
        self.e.delay_enabled = True; self.e.delay_mix = 1.0; self.e.delay_ms = 5.0; self.e.delay_feedback = 0.4
        y1 = self.e._effects(x.copy())
        self.assertGreater(float(np.max(np.abs(y1))), 0.0)

    def test_noise_suppression_giam_nhieu(self):
        noise = (0.12 * np.sin(2 * np.pi * 900 * self.t) + 0.08 * np.sin(2 * np.pi * 1700 * self.t)).astype(np.float32)
        ns = self.e.noise_suppressor
        ns.enabled = True; ns.learning = True
        ns.learn(noise); ns.learning = False
        signal = self.tone(440.0) + noise
        cleaned = ns.process(signal)
        self.assertTrue(np.isfinite(cleaned).all())
        self.assertLess(float(np.std(cleaned)), float(np.std(signal)))

    def test_noise_suppression_tin_hieu_sach(self):
        ns = self.e.noise_suppressor; ns.enabled = True; ns.learn(np.zeros_like(self.t))
        cleaned = ns.process(self.tone(440.0))
        self.assertTrue(np.isfinite(cleaned).all())
        self.assertGreater(float(np.sqrt(np.mean(cleaned * cleaned))), 0.02)

    def test_reverb_khong_nan(self):
        self.e.reverb_enabled = True; self.e.reverb_mix = 0.6; y = self.e._effects(self.tone(440.0))
        self.assertTrue(np.isfinite(y).all())
        self.assertLessEqual(float(np.max(np.abs(y))), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

    def test_chong_be_doc_lap_khi_tat_autotune(self):
        x = self.tone(440.0); self.e.autotune_enabled = False; self.e.harmony_enabled = True; self.e.harmony_mode = "Bè 5"; self.e.harmony_level = .3
        y = self.e._voice(x)
        self.assertFalse(np.allclose(x, y))

    def test_effect_toggle_tat_khong_thay_doi(self):
        x = self.tone(440.0); self.e.delay_enabled = False; self.e.reverb_enabled = False; self.e.delay_mix = 1.0; self.e.reverb_mix = 1.0
        y = self.e._effects(x.copy())
        self.assertTrue(np.allclose(x, y))


class AutoKeyTests(unittest.TestCase):
    def test_auto_key_co_ket_qua_hop_le(self):
        from key_detector import AutoKeyDetector
        d = AutoKeyDetector(sample_rate=48000, fft_size=2048, history=4)
        t = np.arange(2048, dtype=np.float32) / 48000
        # Hợp âm C trưởng tổng hợp: C4-E4-G4.
        x = sum(0.2 * np.sin(2 * np.pi * hz * t) for hz in (261.63, 329.63, 392.00)).astype(np.float32)
        result = [d.analyze(x) for _ in range(4)]
        self.assertIn(result[-1][0], range(12))
        self.assertIn(result[-1][1], ("Trưởng", "Thứ"))
        self.assertTrue(np.isfinite(result[-1][2]))

"""
Smoke test — exercises the full audio pipeline with synthetic audio
to verify all DSP operations work correctly without needing internet/TTS.
"""
import os
import numpy as np
import soundfile as sf
from audio_processor import (
    SAMPLE_RATE, read_audio, write_wav, get_duration,
    generate_subliminal, generate_brown_noise, generate_binaural_beats,
    apply_tempo_change, apply_bandpass_filter, apply_dsb_am_modulation,
    preprocess_vocal, pad_to_length, _smooth_gain,
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_synthetic_speech(freq: float, duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a synthetic 'voice' as a sine wave at a given frequency."""
    t = np.arange(int(duration * sr), dtype=np.float32) / sr
    # Amplitude modulate to simulate speech envelope
    envelope = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * t))  # 0.5 Hz AM
    return (0.8 * np.sin(2 * np.pi * freq * t) * envelope).astype(np.float32)

def test_all():
    errors = []

    # --- Test 1: Synthetic voice generation ---
    print("1. Generating synthetic test tracks...")
    left = make_synthetic_speech(220, 3.0)   # A3 note — simulate "I AM" track
    right = make_synthetic_speech(261, 3.0)  # C4 note — simulate "YOU ARE" track
    center = make_synthetic_speech(330, 3.0) # E4 note — simulate "Bridge" track

    left_path = os.path.join(OUTPUT_DIR, "test_left.wav")
    right_path = os.path.join(OUTPUT_DIR, "test_right.wav")
    center_path = os.path.join(OUTPUT_DIR, "test_center.wav")

    sf.write(left_path, left, SAMPLE_RATE)
    sf.write(right_path, right, SAMPLE_RATE)
    sf.write(center_path, center, SAMPLE_RATE)

    print(f"   Left: {get_duration(left):.1f}s, {len(left)} samples")
    print(f"   Right: {get_duration(right):.1f}s, {len(right)} samples")
    print(f"   Center: {get_duration(center):.1f}s, {len(center)} samples")

    # --- Test 2: Tempo compression ---
    print("\n2. Testing tempo compression (1.35x)...")
    compressed = apply_tempo_change(left, SAMPLE_RATE, 1.35)
    orig_dur = get_duration(left)
    new_dur = get_duration(compressed)
    expected_dur = orig_dur / 1.35
    print(f"   Original: {orig_dur:.3f}s, Compressed: {new_dur:.3f}s, Expected: {expected_dur:.3f}s")
    if abs(new_dur - expected_dur) > 0.1:
        errors.append(f"Tempo duration mismatch: {new_dur:.3f} vs {expected_dur:.3f}")

    # --- Test 3: Brown noise ---
    print("\n3. Testing brown noise generation...")
    brown = generate_brown_noise(SAMPLE_RATE, SAMPLE_RATE, 0.3)
    assert brown.shape == (2, SAMPLE_RATE), f"Wrong shape: {brown.shape}"
    # Check there's no significant DC offset
    dc = np.mean(brown)
    print(f"   Shape: {brown.shape}, DC offset: {dc:.6f}, Max: {np.max(np.abs(brown)):.3f}")
    if abs(dc) > 0.01:
        errors.append(f"Brown noise DC offset too high: {dc:.6f}")

    # --- Test 4: Binaural beats ---
    print("\n4. Testing binaural beats (100/106 Hz)...")
    beats = generate_binaural_beats(SAMPLE_RATE, SAMPLE_RATE, 100, 106, 0.15)
    assert beats.shape == (2, SAMPLE_RATE), f"Wrong shape: {beats.shape}"
    print(f"   Shape: {beats.shape}, Left max: {np.max(np.abs(beats[0])):.3f}, Right max: {np.max(np.abs(beats[1])):.3f}")

    # --- Test 5: Bandpass filter ---
    print("\n5. Testing bandpass filter (150-4000 Hz)...")
    filtered = apply_bandpass_filter(left, SAMPLE_RATE, 150.0, 4000.0, order=4)
    print(f"   Input shape: {left.shape}, Output shape: {filtered.shape}")
    # The 220Hz tone should pass, but be somewhat attenuated
    rms_in = np.sqrt(np.mean(left**2))
    rms_out = np.sqrt(np.mean(filtered**2))
    print(f"   RMS in: {rms_in:.4f}, RMS out: {rms_out:.4f}")
    if rms_out < 0.01:
        errors.append("Bandpass filter killed the signal completely")

    # --- Test 6: DSB-AM modulation ---
    print("\n6. Testing DSB-AM modulation (17.5 kHz carrier)...")
    modulated = apply_dsb_am_modulation(filtered, SAMPLE_RATE, 17500.0)
    print(f"   Modulated shape: {modulated.shape}")
    # The modulated signal should have energy near 17.5kHz
    if len(modulated) > 1024:
        spectrum = np.abs(np.fft.rfft(modulated[:SAMPLE_RATE]))
        freqs = np.fft.rfftfreq(SAMPLE_RATE, 1.0 / SAMPLE_RATE)
        peak_idx = np.argmax(spectrum)
        peak_freq = freqs[peak_idx]
        print(f"   Peak frequency after modulation: {peak_freq:.0f} Hz")
        if peak_freq < 10000:
            errors.append(f"DSB-AM modulation didn't shift frequency high enough (peak at {peak_freq:.0f} Hz)")

    # --- Test 7: Full pipeline — masked method ---
    print("\n7. Testing full pipeline (Classic Masked)...")
    output_masked = os.path.join(OUTPUT_DIR, "test_subliminal_masked.wav")
    result = generate_subliminal(
        left_path, right_path, center_path,
        output_masked,
        method="masked",
        speed_factor=1.35,
        include_binaural=True,
    )
    assert os.path.exists(result), f"Output file not created: {result}"
    data, sr = sf.read(result)
    print(f"   Output: {result}")
    print(f"   Sample rate: {sr} Hz")
    print(f"   Shape: {data.shape} (samples, channels)")
    print(f"   Duration: {data.shape[0]/sr:.2f}s")
    print(f"   Peak amplitude: {np.max(np.abs(data)):.4f}")
    if sr != 48000:
        errors.append(f"Output sample rate is {sr}, expected 48000")
    if data.shape[1] != 2:
        errors.append(f"Output is not stereo (channels={data.shape[1]})")

    # --- Test 8: Full pipeline — silent method ---
    print("\n8. Testing full pipeline (Silent Ultrasonic)...")
    output_silent = os.path.join(OUTPUT_DIR, "test_subliminal_silent.wav")
    result2 = generate_subliminal(
        left_path, right_path, center_path,
        output_silent,
        method="silent",
        speed_factor=1.35,
        include_binaural=True,
    )
    assert os.path.exists(result2), f"Output file not created: {result2}"
    data2, sr2 = sf.read(result2)
    print(f"   Output: {result2}")
    print(f"   Sample rate: {sr2} Hz")
    print(f"   Shape: {data2.shape}")
    print(f"   Duration: {data2.shape[0]/sr2:.2f}s")
    print(f"   Peak amplitude: {np.max(np.abs(data2)):.4f}")

    # Verify ultrasonic content
    if len(data2) > 1024:
        spectrum = np.abs(np.fft.rfft(data2[:SAMPLE_RATE, 0]))
        freqs = np.fft.rfftfreq(SAMPLE_RATE, 1.0 / SAMPLE_RATE)
        peak_idx = np.argmax(spectrum)
        peak_freq = freqs[peak_idx]
        print(f"   Peak frequency: {peak_freq:.0f} Hz (should be above 15kHz)")
        if peak_freq < 15000:
            errors.append(f"Silent output peak at {peak_freq:.0f} Hz — below ultrasonic range")

    # --- Test 9: Preprocessing ---
    print("\n9. Testing preprocessing...")
    processed = preprocess_vocal(left)
    print(f"   Original peak: {np.max(np.abs(left)):.4f}")
    print(f"   Processed peak: {np.max(np.abs(processed)):.4f}")
    if np.max(np.abs(processed)) > 0.9:
        errors.append("Preprocessing didn't normalize to -1dB")

    # --- Test 10: _smooth_gain ---
    print("\n10. Testing gain smoothing...")
    gain_input = np.ones(SAMPLE_RATE) * 0.7
    gain_input[1000:2000] = 0.2  # Simulate a transient
    smoothed = _smooth_gain(gain_input, 240, 2400)  # 5ms attack, 50ms release
    # After the transient, the smoothed gain should recover slowly
    recovery_value = smoothed[3000]
    print(f"   Gain at transient: {smoothed[1500]:.3f}")
    print(f"   Gain at recovery (t+1s): {recovery_value:.3f}")
    if recovery_value > 0.65:
        errors.append("Gain smoothing release too fast")

    # --- Summary ---
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED -- {len(errors)} error(s):")
        for e in errors:
            print(f"   * {e}")
    else:
        print("ALL 10 TESTS PASSED")
        print(f"\nGenerated files in: {OUTPUT_DIR}")
        print(f"  • test_subliminal_masked.wav")
        print(f"  • test_subliminal_silent.wav")
    print("=" * 60)

    return len(errors) == 0

if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)

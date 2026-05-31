"""
Audio Processor - Digital Signal Processing for Subliminal Audio Generation.

Implements all audio transformations from the Optimal Subliminal Audio Creation Guide:
- Pitch-preserved tempo compression (1.35x)
- Dichotic panning with hemispheric routing
- 6 Hz Theta binaural beats
- Brown noise generation (masked subliminals)
- Bandpass filtering + DSB-AM modulation (silent/ultrasonic subliminals)
- Multi-track mixing and WAV export
- Energy layers: isochronic tones, Solfeggio frequencies, Schumann resonance
"""

import numpy as np
import soundfile as sf
from scipy import signal
import librosa
import os


SAMPLE_RATE = 48000
BIT_DEPTH = 24  # For WAV export


# =============================================================================
#  Core Audio Utilities
# =============================================================================

def read_audio(path: str, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Read an audio file and return mono float32 numpy array at target sample rate."""
    data, sr = sf.read(path, dtype='float32')
    if data.ndim > 1:
        data = data.mean(axis=1)  # Convert stereo to mono
    if sr != target_sr:
        data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
    return data


def write_wav(path: str, audio: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    """Write a stereo float32 numpy array to a WAV file."""
    # Clamp to avoid clipping
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(path, audio, sr, subtype=f'PCM_{BIT_DEPTH}')


def get_duration(audio: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    """Get the duration of audio in seconds."""
    if audio.ndim > 1:
        return audio.shape[1] / sr
    return len(audio) / sr


def pad_to_length(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Pad or truncate audio to exactly target_samples length."""
    if audio.ndim > 1:
        current = audio.shape[1]
        if current < target_samples:
            pad_width = target_samples - current
            return np.pad(audio, ((0, 0), (0, pad_width)), mode='constant')
        else:
            return audio[:, :target_samples]
    else:
        current = len(audio)
        if current < target_samples:
            return np.pad(audio, (0, target_samples - current), mode='constant')
        else:
            return audio[:target_samples]


# =============================================================================
#  Step 2: Pitch-Preserved Speed Compression
# =============================================================================

def apply_tempo_change(audio: np.ndarray, sr: int = SAMPLE_RATE, speed_factor: float = 1.35) -> np.ndarray:
    """
    Compress time while preserving pitch using a phase vocoder.

    Guide spec: 1.35x speed (35% faster), high-quality stretching.
    Equivalent to librosa rate = 1/speed_factor.
    """
    if speed_factor <= 0:
        raise ValueError("Speed factor must be positive")
    if abs(speed_factor - 1.0) < 0.001:
        return audio  # No change needed

    return librosa.effects.time_stretch(y=audio, rate=speed_factor)


# =============================================================================
#  Step 4: Binaural Beats (Theta 6 Hz)
# =============================================================================

# Brainwave entrainment presets: target beat frequency → (left Hz, right Hz)
BRAINWAVE_PRESETS = {
    "delta":    {"beat_hz": 2.0,  "left_hz": 100.0, "right_hz": 102.0, "label": "Delta (0.5-4 Hz) — Deep sleep, healing"},
    "theta":    {"beat_hz": 6.0,  "left_hz": 100.0, "right_hz": 106.0, "label": "Theta (4-8 Hz) — Meditation, creativity"},
    "alpha":    {"beat_hz": 10.0, "left_hz": 100.0, "right_hz": 110.0, "label": "Alpha (8-14 Hz) — Relaxation, calm focus"},
    "beta":     {"beat_hz": 20.0, "left_hz": 100.0, "right_hz": 120.0, "label": "Beta (14-30 Hz) — Alertness, concentration"},
    "gamma":    {"beat_hz": 40.0, "left_hz": 100.0, "right_hz": 140.0, "label": "Gamma (30-100 Hz) — Peak awareness, insight"},
}

# Solfeggio frequencies (Hz) — historic six-tone scale + extended frequencies
SOLFEGGIO_FREQUENCIES = {
    174:  "Pain relief, grounding",
    285:  "Tissue regeneration, vitality",
    396:  "Liberating guilt and fear",
    417:  "Undoing situations, change",
    528:  "Transformation, DNA repair",
    639:  "Connection, relationships",
    741:  "Awakening intuition, expression",
    852:  "Returning to spiritual order",
    963:  "Activating pineal gland, unity",
}

SCHUMANN_FREQUENCY = 7.83  # Hz — Earth's electromagnetic resonant frequency

# Energy layer presets — one-click configurations
ENERGY_PRESETS = {
    "deep_sleep": {
        "label": "Deep Sleep & Healing",
        "desc": "Delta entrainment + Schumann + grounding Solfeggio",
        "entrainment_method": "binaural",
        "entrainment_preset": "delta",
        "solfeggio_freqs": [174, 285],
        "schumann": True,
        "energy_amplitude": 0.15,
    },
    "meditation": {
        "label": "Deep Meditation",
        "desc": "Theta entrainment + Schumann + harmonious Solfeggio triad",
        "entrainment_method": "binaural",
        "entrainment_preset": "theta",
        "solfeggio_freqs": [396, 528, 639],
        "schumann": True,
        "energy_amplitude": 0.15,
    },
    "focus": {
        "label": "Focus & Concentration",
        "desc": "Beta isochronic tones + clarity Solfeggio (no headphones needed)",
        "entrainment_method": "isochronic",
        "entrainment_preset": "beta",
        "solfeggio_freqs": [528, 741],
        "schumann": False,
        "energy_amplitude": 0.12,
    },
    "creativity": {
        "label": "Creativity & Flow",
        "desc": "Theta binaural + creative Solfeggio frequencies",
        "entrainment_method": "binaural",
        "entrainment_preset": "theta",
        "solfeggio_freqs": [417, 528, 639],
        "schumann": False,
        "energy_amplitude": 0.15,
    },
    "manifestation": {
        "label": "Manifestation",
        "desc": "Theta + Schumann + full Solfeggio scale for abundance work",
        "entrainment_method": "binaural",
        "entrainment_preset": "theta",
        "solfeggio_freqs": [396, 417, 528, 639, 741],
        "schumann": True,
        "energy_amplitude": 0.18,
    },
    "energy_boost": {
        "label": "Energy Boost",
        "desc": "Gamma isochronic + high Solfeggio for peak activation",
        "entrainment_method": "isochronic",
        "entrainment_preset": "gamma",
        "solfeggio_freqs": [528, 963],
        "schumann": False,
        "energy_amplitude": 0.12,
    },
}


def generate_binaural_beats(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    freq_left: float = 100.0,
    freq_right: float = 106.0,
    amplitude: float = 0.15,
) -> np.ndarray:
    """
    Generate a stereo binaural beat signal.

    Left channel: freq_left Hz sine (routed 100% left)
    Right channel: freq_right Hz sine (routed 100% right)
    Brain perceives the difference frequency: freq_right - freq_left = 6 Hz (Theta).

    Returns stereo array shape (2, duration_samples).
    """
    t = np.arange(duration_samples, dtype=np.float32) / sr
    left_channel = amplitude * np.sin(2.0 * np.pi * freq_left * t, dtype=np.float32)
    right_channel = amplitude * np.sin(2.0 * np.pi * freq_right * t, dtype=np.float32)
    return np.stack([left_channel, right_channel])


# =============================================================================
#  Energy Layers: Isochronic Tones, Solfeggio, Schumann Resonance
# =============================================================================

def generate_isochronic_tones(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    beat_frequency: float = 6.0,
    carrier_frequency: float = 200.0,
    amplitude: float = 0.12,
    duty_cycle: float = 0.5,
) -> np.ndarray:
    """
    Generate isochronic tones — a single carrier frequency pulsed on/off
    at the target beat rate. Unlike binaural beats, isochronic tones are
    mono-compatible and don't require stereo headphones.

    The tone alternates between full amplitude and silence at the beat
    frequency, creating a strong rhythmic pulse that the brain can
    entrain to.

    Args:
        duration_samples: Number of samples.
        sr: Sample rate.
        beat_frequency: The pulse rate in Hz (brainwave target).
        carrier_frequency: The audible tone frequency to pulse.
        amplitude: Peak amplitude of the pulsed tone.
        duty_cycle: Fraction of each cycle the tone is "on" (0.0-1.0).

    Returns:
        Stereo numpy array shape (2, duration_samples) — both channels
        identical (mono-compatible).
    """
    t = np.arange(duration_samples, dtype=np.float32) / sr

    # Create the carrier sine wave
    carrier = np.sin(2.0 * np.pi * carrier_frequency * t, dtype=np.float32)

    # Create the pulsing envelope (square wave smoothed with raised cosine)
    # This is the key difference from binaural beats: amplitude modulation
    # at the beat frequency creates a consciously perceptible pulse.
    pulse_phase = 2.0 * np.pi * beat_frequency * t
    # Use a soft square: sin^2 gives smooth pulses, cos gives alternating
    envelope = 0.5 * (1.0 + np.cos(pulse_phase, dtype=np.float32))
    # Compress the duty cycle: raise to power so "on" periods are shorter
    if duty_cycle != 0.5:
        # Adjust: higher power → narrower peaks
        power = np.log(0.5) / np.log(duty_cycle) if duty_cycle > 0 else 1.0
        envelope = envelope ** power

    # Apply envelope to carrier
    pulsed = carrier * envelope * amplitude

    # Gentle highpass to remove any DC / subsonic artifacts from the pulsing
    nyquist = sr / 2.0
    b, a = signal.butter(2, 20.0 / nyquist, btype='high')
    pulsed = signal.filtfilt(b, a, pulsed).astype(np.float32)

    # Duplicate to stereo (both channels same — mono-compatible)
    return np.stack([pulsed, pulsed])


def generate_solfeggio_tones(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    frequencies: list = None,
    amplitude: float = 0.06,
) -> np.ndarray:
    """
    Generate a subtle mix of Solfeggio frequency sine waves.

    These are pure musical pitch frequencies (not beat frequencies),
    layered as a gentle harmonic bed. They operate in the pitch domain
    and do not conflict with brainwave entrainment.

    Args:
        duration_samples: Number of samples.
        sr: Sample rate.
        frequencies: List of Hz frequencies to include (e.g. [528, 396]).
                      If None, uses a default set [396, 528, 639].
        amplitude: Overall amplitude (divided among selected frequencies).

    Returns:
        Stereo numpy array shape (2, duration_samples).
    """
    if frequencies is None or len(frequencies) == 0:
        frequencies = [396, 528, 639]

    t = np.arange(duration_samples, dtype=np.float32) / sr
    mix = np.zeros(duration_samples, dtype=np.float32)

    # Each frequency gets equal share of the amplitude budget
    per_freq_amp = amplitude / max(len(frequencies), 1)

    for freq in frequencies:
        # Add a subtle phase offset to each frequency for a more natural sound
        phase_offset = (freq * 0.37) % (2.0 * np.pi)  # Arbitrary but deterministic
        sine = np.sin(2.0 * np.pi * freq * t + phase_offset, dtype=np.float32)
        mix += sine * per_freq_amp

    # Gentle peak normalization of the mix
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix * (amplitude / peak)

    # Duplicate to stereo
    return np.stack([mix, mix])


def generate_binaural_sweep(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    freq_start: float = 20.0,
    freq_end: float = 6.0,
    carrier_freq: float = 100.0,
    amplitude: float = 0.15,
) -> np.ndarray:
    """
    Generate binaural beats with a sweeping beat frequency.

    The left ear plays a constant carrier tone while the right ear sweeps
    from carrier_freq + freq_start to carrier_freq + freq_end using a
    linear chirp. The brain perceives a beat frequency that sweeps
    smoothly from freq_start to freq_end over the full audio duration.

    Uses scipy.signal.chirp for mathematically accurate linear frequency
    sweep (instantaneous frequency = integral of phase derivative).

    Args:
        duration_samples: Number of samples.
        sr: Sample rate.
        freq_start: Starting beat frequency in Hz (e.g., 20 Hz Beta).
        freq_end: Ending beat frequency in Hz (e.g., 6 Hz Theta).
        carrier_freq: Base frequency for the left ear (fixed).
        amplitude: Peak amplitude of each channel.

    Returns:
        Stereo numpy array shape (2, duration_samples).
    """
    t = np.arange(duration_samples, dtype=np.float64) / sr
    duration_sec = duration_samples / sr

    # Left channel: constant carrier tone
    left = amplitude * np.sin(2.0 * np.pi * carrier_freq * t, dtype=np.float32)

    # Right channel: sweeping from carrier+freq_start to carrier+freq_end
    right_sweep = signal.chirp(
        t, f0=carrier_freq + freq_start, f1=carrier_freq + freq_end,
        t1=duration_sec, method='linear'
    )
    right = amplitude * right_sweep.astype(np.float32)

    return np.stack([left, right])


def generate_isochronic_sweep(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    freq_start: float = 20.0,
    freq_end: float = 6.0,
    carrier_frequency: float = 200.0,
    amplitude: float = 0.12,
    duty_cycle: float = 0.5,
) -> np.ndarray:
    """
    Generate isochronic tones with a sweeping pulse rate.

    The carrier tone is pulsed on/off at a rate that sweeps from
    freq_start to freq_end using a linear chirp envelope. Mono-compatible
    and doesn't require stereo headphones.

    The envelope is a cosine at the instantaneous sweep frequency,
    creating smooth rhythmic pulses that the brain can entrain to as
    the frequency shifts.

    Args:
        duration_samples: Number of samples.
        sr: Sample rate.
        freq_start: Starting pulse rate in Hz (e.g., 20 Hz Beta).
        freq_end: Ending pulse rate in Hz (e.g., 6 Hz Theta).
        carrier_frequency: The audible tone frequency to pulse.
        amplitude: Peak amplitude.
        duty_cycle: Fraction of each cycle the tone is "on" (0.0-1.0).

    Returns:
        Stereo numpy array shape (2, duration_samples) — both channels
        identical (mono-compatible).
    """
    t = np.arange(duration_samples, dtype=np.float64) / sr
    duration_sec = duration_samples / sr

    # Create the carrier sine wave
    carrier = np.sin(2.0 * np.pi * carrier_frequency * t, dtype=np.float32)

    # Create envelope using the instantaneous phase of the sweep
    # φ(t) = 2π * (f_start * t + (f_end - f_start) * t² / (2 * T))
    phase = 2.0 * np.pi * (
        freq_start * t + (freq_end - freq_start) * t**2 / (2.0 * duration_sec)
    )
    envelope = 0.5 * (1.0 + np.cos(phase, dtype=np.float32))

    # Compress the duty cycle
    if duty_cycle != 0.5:
        power = np.log(0.5) / np.log(duty_cycle) if duty_cycle > 0 else 1.0
        envelope = envelope ** power

    # Apply envelope to carrier
    pulsed = carrier * envelope * amplitude

    # Gentle highpass to remove DC / subsonic artifacts
    nyquist = sr / 2.0
    b, a = signal.butter(2, 20.0 / nyquist, btype='high')
    pulsed = signal.filtfilt(b, a, pulsed).astype(np.float32)

    return np.stack([pulsed, pulsed])


def generate_schumann_resonance(
    duration_samples: int,
    sr: int = SAMPLE_RATE,
    amplitude: float = 0.04,
) -> np.ndarray:
    """
    Generate a Schumann resonance layer (7.83 Hz).

    At 7.83 Hz, the fundamental is below human hearing range (~20 Hz),
    but can be perceived through bone conduction, tactile sensation,
    and subtle amplitude modulation effects on the rest of the audio.

    We render it as a very low-frequency sine wave that creates a
    barely-perceptible rhythmic pressure modulation. For listeners with
    high-quality headphones or subwoofers, this adds a grounding,
    earth-frequency layer.

    Args:
        duration_samples: Number of samples.
        sr: Sample rate.
        amplitude: Peak amplitude (kept very low to avoid speaker damage).

    Returns:
        Stereo numpy array shape (2, duration_samples).
    """
    t = np.arange(duration_samples, dtype=np.float32) / sr

    # Pure 7.83 Hz sine wave
    schumann = amplitude * np.sin(2.0 * np.pi * SCHUMANN_FREQUENCY * t, dtype=np.float32)

    # Apply a gentle 10 Hz lowpass to remove any harmonic artifacts
    # from the sharp start/stop (filtfilt is zero-phase, no group delay)
    nyquist = sr / 2.0
    b, a = signal.butter(2, 10.0 / nyquist, btype='low')
    schumann = signal.filtfilt(b, a, schumann).astype(np.float32)

    # Duplicate to stereo
    return np.stack([schumann, schumann])


# =============================================================================
#  Step 5 Option A: Brown Noise Generator (Classic Masked Subliminal)
# =============================================================================

def generate_brown_noise(duration_samples: int, sr: int = SAMPLE_RATE, amplitude: float = 0.3) -> np.ndarray:
    """
    Generate stereo brown (brownian) noise.

    Brown noise has a -6 dB/octave spectral rolloff, naturally blanketing
    human vocal frequencies (100 Hz - 4 kHz) with a deep, soothing character.

    Uses cumulative-sum integration of white noise, then applies a 20 Hz
    highpass to remove DC wander that would otherwise build up over time.

    Returns stereo array shape (2, duration_samples).
    """
    # Generate white noise
    white = np.random.randn(duration_samples).astype(np.float32)

    # Integrate to get brown noise (cumulative sum gives -6 dB/octave)
    brown = np.cumsum(white, dtype=np.float64)
    brown = brown.astype(np.float32)

    # Remove DC offset and subsonic wander with a 20 Hz highpass
    nyquist = sr / 2.0
    b_hp, a_hp = signal.butter(2, 20.0 / nyquist, btype='high')
    brown = signal.filtfilt(b_hp, a_hp, brown).astype(np.float32)

    # Normalize to desired amplitude
    max_val = np.max(np.abs(brown))
    if max_val > 0:
        brown = brown * (amplitude / max_val)

    # Create stereo (both channels same noise for centered masking)
    return np.stack([brown, brown])


# =============================================================================
#  Step 5 Option B: Silent Subliminal (Lowery Method)
# =============================================================================

def apply_bandpass_filter(audio: np.ndarray, sr: int = SAMPLE_RATE,
                          low: float = 150.0, high: float = 4000.0,
                          order: int = 4) -> np.ndarray:
    """
    Bandpass filter audio to restrict to vocal intelligibility range.

    Guide spec: 150 Hz to 4000 Hz, capturing 99% of speech intelligibility.
    This prevents sibilant aliasing during DSB-AM modulation.
    """
    nyquist = sr / 2.0
    low_norm = low / nyquist
    high_norm = high / nyquist

    # Ensure normalized frequencies are in valid range
    low_norm = max(min(low_norm, 0.99), 0.001)
    high_norm = max(min(high_norm, 0.99), 0.001)

    if low_norm >= high_norm:
        raise ValueError(f"Invalid bandpass range: low={low}Hz, high={high}Hz")

    b, a = signal.butter(order, [low_norm, high_norm], btype='band')
    return signal.filtfilt(b, a, audio).astype(np.float32)


def apply_dsb_am_modulation(audio: np.ndarray, sr: int = SAMPLE_RATE,
                            carrier_freq: float = 17500.0) -> np.ndarray:
    """
    Apply Double-Sideband Amplitude Modulation to shift voice into ultrasonic range.

    Multiplies the bandpass-filtered voice signal by a high-frequency carrier sine wave.
    This shifts the voice spectrum to center around carrier_freq Hz, making it
    consciously inaudible while remaining neurally processable.

    Guide spec: 17,500 Hz carrier (or 15,500 Hz alternative).
    """
    t = np.arange(len(audio), dtype=np.float32) / sr
    carrier = np.sin(2.0 * np.pi * carrier_freq * t, dtype=np.float32)
    return (audio * carrier).astype(np.float32)


# =============================================================================
#  Step 1: Audio Preprocessing (Noise Reduction, EQ, Compression, Normalization)
# =============================================================================

def loop_vocals_to_duration(audio: np.ndarray, target_duration_seconds: float, output_path: str = None, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Loop a vocal track to match a target duration.

    Repeats the vocal track end-to-end until the target duration is reached.
    The final loop is trimmed so the total never exceeds the target.

    Args:
        audio: Mono float32 numpy array.
        target_duration_seconds: Desired total duration.
        output_path: If provided, saves the looped audio to this path.
        sr: Sample rate.

    Returns:
        Looped audio numpy array at exactly target_duration_seconds long.
    """
    vocal_duration = get_duration(audio, sr)
    target_samples = int(target_duration_seconds * sr)

    if vocal_duration <= 0 or len(audio) == 0:
        # Silence for empty tracks
        result = np.zeros(target_samples, dtype=np.float32)
        if output_path:
            sf.write(output_path, result, sr)
        return result

    if vocal_duration >= target_duration_seconds:
        # Already long enough — just trim
        result = pad_to_length(audio, target_samples)
        if output_path:
            sf.write(output_path, result, sr)
        return result

    # Calculate how many full loops + partial final loop
    num_full_loops = int(target_duration_seconds / vocal_duration)
    remainder_samples = target_samples - int(num_full_loops * len(audio))

    parts = [audio] * num_full_loops
    if remainder_samples > 0:
        parts.append(audio[:remainder_samples])

    result = np.concatenate(parts).astype(np.float32)
    result = pad_to_length(result, target_samples)

    if output_path:
        sf.write(output_path, result, sr)

    return result


def generate_preview(
    vocal_left_path: str,
    vocal_right_path: str,
    vocal_center_path: str,
    output_path: str,
    method: str = "masked",
    speed_factor: float = 1.35,
    include_binaural: bool = True,
    vocal_attenuation_db: float = -28.0,
    custom_mask_path: str = None,
    preview_duration: float = 10.0,
    energy_layers: dict = None,
) -> str:
    """
    Generate a short preview clip of the subliminal audio.

    Takes the first N seconds of each vocal track and generates a quick
    subliminal mix for preview purposes. Useful for the user to hear
    what the final output will sound like before committing to a full render.

    Args:
        vocal_left_path: Path to left ear vocal WAV.
        vocal_right_path: Path to right ear vocal WAV.
        vocal_center_path: Path to center vocal WAV.
        output_path: Where to save the preview WAV.
        method: "masked", "silent", or "both".
        speed_factor: Tempo compression factor.
        include_binaural: Whether to include binaural beats.
        vocal_attenuation_db: Vocal attenuation for masked method.
        custom_mask_path: Optional custom mask audio.
        preview_duration: Length of preview in seconds.
        energy_layers: Optional energy layer config (see generate_subliminal).

    Returns:
        Path to the preview WAV file.
    """
    # Load vocal tracks
    left_audio = read_audio(vocal_left_path)
    right_audio = read_audio(vocal_right_path)
    center_audio = read_audio(vocal_center_path)

    # Preprocess
    left_audio = preprocess_vocal(left_audio)
    right_audio = preprocess_vocal(right_audio)
    center_audio = preprocess_vocal(center_audio)

    # Tempo compress
    left_audio = apply_tempo_change(left_audio, SAMPLE_RATE, speed_factor)
    right_audio = apply_tempo_change(right_audio, SAMPLE_RATE, speed_factor)
    center_audio = apply_tempo_change(center_audio, SAMPLE_RATE, speed_factor)

    # Trim all tracks to preview duration
    preview_samples = int(preview_duration * SAMPLE_RATE)

    # Apply velocity to speed_factor: compress the preview to match
    # the effective duration after tempo change
    left_audio = pad_to_length(left_audio, preview_samples)
    right_audio = pad_to_length(right_audio, preview_samples)
    center_audio = pad_to_length(center_audio, preview_samples)

    total_samples = preview_samples

    # Apply subliminal method
    if method == "silent":
        left_audio = apply_bandpass_filter(left_audio, SAMPLE_RATE, 150.0, 4000.0)
        left_audio = apply_dsb_am_modulation(left_audio, SAMPLE_RATE, 17500.0)
        right_audio = apply_bandpass_filter(right_audio, SAMPLE_RATE, 150.0, 4000.0)
        right_audio = apply_dsb_am_modulation(right_audio, SAMPLE_RATE, 17500.0)
        center_audio = apply_bandpass_filter(center_audio, SAMPLE_RATE, 150.0, 4000.0)
        center_audio = apply_dsb_am_modulation(center_audio, SAMPLE_RATE, 17500.0)
    elif method == "both":
        attenuation_linear = 10.0 ** (vocal_attenuation_db / 20.0)
        left_silent = apply_bandpass_filter(left_audio.copy(), SAMPLE_RATE, 150.0, 4000.0)
        left_silent = apply_dsb_am_modulation(left_silent, SAMPLE_RATE, 17500.0)
        right_silent = apply_bandpass_filter(right_audio.copy(), SAMPLE_RATE, 150.0, 4000.0)
        right_silent = apply_dsb_am_modulation(right_silent, SAMPLE_RATE, 17500.0)
        center_silent = apply_bandpass_filter(center_audio.copy(), SAMPLE_RATE, 150.0, 4000.0)
        center_silent = apply_dsb_am_modulation(center_silent, SAMPLE_RATE, 17500.0)
        left_audio *= attenuation_linear
        right_audio *= attenuation_linear
        center_audio *= attenuation_linear
    else:
        attenuation_linear = 10.0 ** (vocal_attenuation_db / 20.0)
        left_audio *= attenuation_linear
        right_audio *= attenuation_linear
        center_audio *= attenuation_linear

    # Dichotic routing
    left_stereo = np.zeros((2, total_samples), dtype=np.float32)
    left_stereo[0, :] = left_audio

    offset_samples = int(0.050 * SAMPLE_RATE)
    right_stereo = np.zeros((2, total_samples), dtype=np.float32)
    if offset_samples < total_samples:
        right_stereo[1, offset_samples:] = right_audio[:total_samples - offset_samples]
    else:
        right_stereo[1, :] = right_audio[:total_samples]

    center_stereo = np.zeros((2, total_samples), dtype=np.float32)
    half_center = center_audio * 0.5
    center_stereo[0, :] = half_center
    center_stereo[1, :] = half_center

    # Brainwave entrainment (binaural beats or isochronic tones)
    binaural_stereo = None
    isochronic_stereo = None
    solfeggio_stereo = None
    schumann_stereo = None

    if energy_layers and energy_layers.get("entrainment_method"):
        ent_method = energy_layers["entrainment_method"]
        ent_preset = energy_layers.get("entrainment_preset", "theta")
        preset = BRAINWAVE_PRESETS.get(ent_preset, BRAINWAVE_PRESETS["theta"])
        energy_amp = float(energy_layers.get("energy_amplitude", 0.15))

        # Check for frequency sweep mode
        sweep_enabled = energy_layers.get("sweep_enabled", False)
        sweep_start_hz = float(energy_layers.get("sweep_start_hz", 20.0))
        sweep_end_hz = float(energy_layers.get("sweep_end_hz", 6.0))

        if sweep_enabled:
            if ent_method == "binaural":
                carrier = preset.get("left_hz", 100.0)
                binaural_stereo = generate_binaural_sweep(
                    total_samples, SAMPLE_RATE,
                    freq_start=sweep_start_hz,
                    freq_end=sweep_end_hz,
                    carrier_freq=carrier,
                    amplitude=0.15 * (energy_amp / 0.15),
                )
            elif ent_method == "isochronic":
                isochronic_stereo = generate_isochronic_sweep(
                    total_samples, SAMPLE_RATE,
                    freq_start=sweep_start_hz,
                    freq_end=sweep_end_hz,
                    carrier_frequency=200.0,
                    amplitude=0.12 * (energy_amp / 0.15),
                )
        else:
            if ent_method == "binaural":
                binaural_stereo = generate_binaural_beats(
                    total_samples, SAMPLE_RATE,
                    preset["left_hz"], preset["right_hz"],
                    0.15 * (energy_amp / 0.15)
                )
            elif ent_method == "isochronic":
                isochronic_stereo = generate_isochronic_tones(
                    total_samples, SAMPLE_RATE,
                    beat_frequency=preset["beat_hz"],
                    carrier_frequency=200.0,
                    amplitude=0.12 * (energy_amp / 0.15),
                )

        solf_freqs = energy_layers.get("solfeggio_freqs", [])
        if solf_freqs:
            valid_freqs = [f for f in solf_freqs if f in SOLFEGGIO_FREQUENCIES]
            if valid_freqs:
                solfeggio_stereo = generate_solfeggio_tones(
                    total_samples, SAMPLE_RATE,
                    frequencies=valid_freqs,
                    amplitude=0.06 * (energy_amp / 0.15),
                )

        if energy_layers.get("schumann", False):
            schumann_stereo = generate_schumann_resonance(
                total_samples, SAMPLE_RATE,
                amplitude=0.04 * (energy_amp / 0.15),
            )
    elif include_binaural:
        binaural_stereo = generate_binaural_beats(total_samples, SAMPLE_RATE, 100, 106, 0.15)

    # Mask
    mask_stereo = None
    if custom_mask_path and os.path.isfile(custom_mask_path):
        mask_audio = read_audio(custom_mask_path)
        mask_audio = pad_to_length(mask_audio, total_samples)
        if mask_audio.ndim == 1:
            mask_stereo = np.stack([mask_audio, mask_audio])
        else:
            mask_stereo = pad_to_length(mask_audio, total_samples)
        mask_peak = np.max(np.abs(mask_stereo))
        if mask_peak > 0:
            mask_stereo *= (0.8 / mask_peak)
    elif method in ("masked", "both"):
        mask_stereo = generate_brown_noise(total_samples, SAMPLE_RATE, 0.25)

    # Silent tracks for "both"
    silent_stereo = None
    if method == "both":
        silent_stereo = np.zeros((2, total_samples), dtype=np.float32)
        left_silent_pad = pad_to_length(left_silent * 0.25, total_samples)
        right_silent_pad = pad_to_length(right_silent * 0.25, total_samples)
        center_silent_pad = pad_to_length(center_silent * 0.25, total_samples)
        silent_stereo[0, :] += left_silent_pad
        if offset_samples < total_samples:
            silent_stereo[1, offset_samples:] += right_silent_pad[:total_samples - offset_samples]
        silent_stereo[0, :] += center_silent_pad[:total_samples] * 0.5
        silent_stereo[1, :] += center_silent_pad[:total_samples] * 0.5

    # Mix
    mixed = np.zeros((2, total_samples), dtype=np.float32)
    mixed += left_stereo
    mixed += right_stereo
    mixed += center_stereo
    if binaural_stereo is not None:
        mixed += binaural_stereo
    if isochronic_stereo is not None:
        mixed += isochronic_stereo
    if solfeggio_stereo is not None:
        mixed += solfeggio_stereo
    if schumann_stereo is not None:
        mixed += schumann_stereo
    if mask_stereo is not None:
        mixed += mask_stereo
    if silent_stereo is not None:
        mixed += silent_stereo

    peak = np.max(np.abs(mixed))
    if peak > 0.98:
        mixed *= (0.98 / peak)

    write_wav(output_path, mixed.T, SAMPLE_RATE)
    return output_path


def preprocess_vocal(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Apply basic vocal cleanup: highpass filter (remove sub-80Hz rumble),
    gentle compression, and peak normalization to -1 dB.

    This approximates the guide's: Noise Reduction → Vocal EQ → Compression → Normalization.
    """
    # Highpass at 80 Hz to remove subsonic rumble and mic handling noise
    nyquist = sr / 2.0
    b, a = signal.butter(4, 80.0 / nyquist, btype='high')
    audio = signal.filtfilt(b, a, audio).astype(np.float32)

    # Dynamic compression (guide spec: threshold -16 dB, noise floor -40 dB, ratio 3:1)
    # RMS-based detection with soft knee for natural-sounding compression
    threshold_linear = 10.0 ** (-16.0 / 20.0)  # -16 dB
    noise_floor_linear = 10.0 ** (-40.0 / 20.0)  # -40 dB
    ratio = 3.0

    # Compute RMS envelope (10ms window)
    rms_window = int(0.010 * sr)
    if rms_window > 0 and len(audio) > rms_window:
        squared = audio ** 2
        envelope = np.sqrt(np.convolve(squared, np.ones(rms_window) / rms_window, mode='same'))
    else:
        envelope = np.abs(audio)

    # Apply compression where envelope exceeds threshold
    above = envelope > threshold_linear
    if np.any(above):
        gain_reduction = np.ones_like(envelope)
        # Above threshold: reduce gain. Formula: gain = (threshold/env)^(1-1/R)
        gain_reduction[above] = (threshold_linear / envelope[above]) ** (1.0 - 1.0 / ratio)

        # Smooth gain changes to avoid clicks (attack ~5ms, release ~50ms)
        attack_samples = int(0.005 * sr)
        release_samples = int(0.050 * sr)
        gain_smoothed = _smooth_gain(gain_reduction, attack_samples, release_samples)
        audio = audio * gain_smoothed

        # Ensure we don't push below noise floor
        audio = np.clip(audio, -1.0, 1.0)

    # Peak normalize to -1 dB
    peak = np.max(np.abs(audio))
    if peak > 0:
        target_peak = 0.891  # -1 dB
        audio = audio * (target_peak / peak)

    return audio.astype(np.float32)


def _smooth_gain(gain: np.ndarray, attack_samples: int, release_samples: int) -> np.ndarray:
    """
    Smooth a gain reduction curve with asymmetric attack/release.

    Uses scipy.signal.lfilter for vectorized one-pole smoothing.
    We run two passes (attack direction + release direction) and take the
    minimum gain at each point, which effectively applies attack smoothing
    on downward gain changes and release smoothing on upward recovery.

    Args:
        gain: The per-sample gain array (should be <= 1.0).
        attack_samples: Number of samples for attack smoothing (~5ms).
        release_samples: Number of samples for release smoothing (~50ms).

    Returns:
        Smoothed gain array same shape as input, fully vectorized.
    """
    attack_coeff = np.exp(-1.0 / max(attack_samples, 1))
    release_coeff = np.exp(-1.0 / max(release_samples, 1))

    # One-pole lowpass: y[n] = coeff * y[n-1] + (1 - coeff) * x[n]
    # For lfilter: a = [1, -coeff], b = [1 - coeff]

    # Forward pass with release coefficient (smooth recovery)
    b_r = np.array([1.0 - release_coeff], dtype=np.float64)
    a_r = np.array([1.0, -release_coeff], dtype=np.float64)

    # Initialize filter to steady-state at the first gain value to avoid start-up artifact
    zi = signal.lfilter_zi(b_r, a_r) * float(gain[0])
    gain_release, _ = signal.lfilter(b_r, a_r, gain.astype(np.float64), zi=zi)

    # We also want fast attack response for downward gain changes.
    # Take the element-wise minimum of the original (fast-attack) and smoothed (slow-release).
    smoothed = np.minimum(gain.astype(np.float64), gain_release)

    return smoothed.astype(np.float32)


# =============================================================================
#  The Complete Pipeline
# =============================================================================

def generate_subliminal(
    vocal_left_path: str,
    vocal_right_path: str,
    vocal_center_path: str,
    output_path: str,
    method: str = "masked",  # "masked", "silent", or "both"
    speed_factor: float = 1.35,
    include_binaural: bool = True,
    binaural_freq_left: float = 100.0,
    binaural_freq_right: float = 106.0,
    binaural_amplitude: float = 0.15,
    mask_amplitude: float = 0.25,  # -12 dB approx (brown noise only)
    vocal_attenuation_db: float = -28.0,
    silent_carrier_freq: float = 17500.0,
    custom_mask_path: str = None,  # Optional path to custom masking audio
    energy_layers: dict = None,  # Energy layer configuration (see below)
    progress_callback=None,
) -> str:
    """
    The complete subliminal audio generation pipeline.

    Args:
        vocal_left_path: Path to mono WAV for Left ear (I AM statements).
        vocal_right_path: Path to mono WAV for Right ear (YOU ARE statements).
        vocal_center_path: Path to mono WAV for Center/Bridge.
        output_path: Where to save the final stereo WAV.
        method: "masked" (brown noise + attenuated vocals), "silent" (ultrasonic DSB-AM),
                or "both" (masked + silent combined in one file).
        speed_factor: Tempo compression factor (1.35 = 35% faster per guide).
        include_binaural: Whether to layer in Theta binaural beats.
        binaural_freq_left: Left binaural tone frequency (default 100 Hz).
        binaural_freq_right: Right binaural tone frequency (default 106 Hz).
        binaural_amplitude: Binaural tone amplitude (default 0.15).
        mask_amplitude: Brown noise amplitude for masked method (default 0.25).
        vocal_attenuation_db: How much to attenuate vocals in dB for masked method (default -28).
        silent_carrier_freq: Carrier frequency for silent method (default 17500 Hz).
        custom_mask_path: Optional path to a custom masking audio file (replaces brown noise).
        energy_layers: Optional dict with energy layer settings:
            {
                "entrainment_method": "binaural" | "isochronic" | None,
                "entrainment_preset": "theta" | "delta" | "alpha" | "beta" | "gamma",
                "solfeggio_freqs": [528, 396] or [],
                "schumann": True | False,
                "energy_amplitude": 0.15,  # overall multiplier (0.0-0.3)
            }
            If entrainment_method is provided, it OVERRIDES the legacy
            include_binaural/binaural_freq_* parameters.
            Only one entrainment method (binaural OR isochronic) is used.
            Solfeggio and Schumann can always be layered on top since they
            operate in the pitch domain, not the beat domain.
        progress_callback: Optional callback(description, percent_0_to_100).

    Returns:
        Path to the generated subliminal WAV file.
    """
    if progress_callback:
        progress_callback("Reading vocal tracks...", 0)

    # --- Load all vocal tracks ---
    left_audio = read_audio(vocal_left_path)
    right_audio = read_audio(vocal_right_path)
    center_audio = read_audio(vocal_center_path)

    if progress_callback:
        progress_callback("Preprocessing vocals...", 5)

    # --- Step 1: Preprocess vocals ---
    left_audio = preprocess_vocal(left_audio)
    right_audio = preprocess_vocal(right_audio)
    center_audio = preprocess_vocal(center_audio)

    if progress_callback:
        progress_callback("Applying tempo compression...", 15)

    # --- Step 2: Pitch-preserved speed compression ---
    left_audio = apply_tempo_change(left_audio, SAMPLE_RATE, speed_factor)
    right_audio = apply_tempo_change(right_audio, SAMPLE_RATE, speed_factor)
    center_audio = apply_tempo_change(center_audio, SAMPLE_RATE, speed_factor)

    if progress_callback:
        progress_callback("Applying subliminal method...", 30)

    # --- Step 5: Apply subliminal method ---
    # Initialize silent track variables (only used when method == "both")
    left_silent = right_silent = center_silent = None

    if method == "both":
        # Create masked copies (attenuated)
        attenuation_linear = 10.0 ** (vocal_attenuation_db / 20.0)
        left_masked = left_audio * attenuation_linear
        right_masked = right_audio * attenuation_linear
        center_masked = center_audio * attenuation_linear

        # Create silent copies (bandpass + DSB-AM modulated)
        left_silent = apply_bandpass_filter(left_audio, SAMPLE_RATE, 150.0, 4000.0)
        left_silent = apply_dsb_am_modulation(left_silent, SAMPLE_RATE, silent_carrier_freq)
        right_silent = apply_bandpass_filter(right_audio, SAMPLE_RATE, 150.0, 4000.0)
        right_silent = apply_dsb_am_modulation(right_silent, SAMPLE_RATE, silent_carrier_freq)
        center_silent = apply_bandpass_filter(center_audio, SAMPLE_RATE, 150.0, 4000.0)
        center_silent = apply_dsb_am_modulation(center_silent, SAMPLE_RATE, silent_carrier_freq)

        # Reassign: main vocal tracks = masked, we'll add silent tracks separately
        left_audio = left_masked
        right_audio = right_masked
        center_audio = center_masked

    elif method == "silent":
        # Bandpass filter vocals to 150-4000 Hz (prevents aliasing)
        left_audio = apply_bandpass_filter(left_audio, SAMPLE_RATE, 150.0, 4000.0)
        right_audio = apply_bandpass_filter(right_audio, SAMPLE_RATE, 150.0, 4000.0)
        center_audio = apply_bandpass_filter(center_audio, SAMPLE_RATE, 150.0, 4000.0)

        # DSB-AM modulate each track
        left_audio = apply_dsb_am_modulation(left_audio, SAMPLE_RATE, silent_carrier_freq)
        right_audio = apply_dsb_am_modulation(right_audio, SAMPLE_RATE, silent_carrier_freq)
        center_audio = apply_dsb_am_modulation(center_audio, SAMPLE_RATE, silent_carrier_freq)
    else:
        # Classic masked: attenuate vocals relative to mask
        attenuation_linear = 10.0 ** (vocal_attenuation_db / 20.0)
        left_audio = left_audio * attenuation_linear
        right_audio = right_audio * attenuation_linear
        center_audio = center_audio * attenuation_linear

    # --- Determine total duration ---
    durations = [
        get_duration(left_audio),
        get_duration(right_audio),
        get_duration(center_audio),
    ]
    max_duration = max(durations)
    total_samples = int(max_duration * SAMPLE_RATE)

    if progress_callback:
        progress_callback("Building stereo tracks...", 50)

    # --- Step 3: Stereophonic Hemispheric Routing ---
    # Pad all tracks to the same length
    left_padded = pad_to_length(left_audio, total_samples)
    right_padded = pad_to_length(right_audio, total_samples)
    center_padded = pad_to_length(center_audio, total_samples)

    # Left ear: hard left (channel 0 only) — I AM identity statements
    left_stereo = np.zeros((2, total_samples), dtype=np.float32)
    left_stereo[0, :] = left_padded

    # Right ear: hard right (channel 1 only) — YOU ARE authority statements
    # CRITICAL: 50ms offset to prevent phase cancellation (per guide Step 3, #2)
    offset_samples = int(0.050 * SAMPLE_RATE)
    right_stereo = np.zeros((2, total_samples), dtype=np.float32)
    if offset_samples < total_samples:
        right_stereo[1, offset_samples:] = right_padded[:total_samples - offset_samples]
    else:
        right_stereo[1, :] = right_padded[:total_samples]

    # Center/Bridge: centered stereo — progressive phrasing & afformations
    center_stereo = np.zeros((2, total_samples), dtype=np.float32)
    half_center = center_padded * 0.5  # Slightly lower to keep it as background
    center_stereo[0, :] = half_center
    center_stereo[1, :] = half_center

    if progress_callback:
        progress_callback("Generating additional layers...", 65)

    # --- Step 4: Binaural Beats OR Isochronic Tones (brainwave entrainment) ---
    # Energy layers override the legacy binaural parameters when provided.
    # Design rule: only ONE entrainment method at a time (binaural OR isochronic).
    binaural_stereo = None
    isochronic_stereo = None
    solfeggio_stereo = None
    schumann_stereo = None

    if energy_layers and energy_layers.get("entrainment_method"):
        ent_method = energy_layers["entrainment_method"]
        ent_preset = energy_layers.get("entrainment_preset", "theta")
        preset = BRAINWAVE_PRESETS.get(ent_preset, BRAINWAVE_PRESETS["theta"])
        energy_amp = float(energy_layers.get("energy_amplitude", 0.15))

        # Check for frequency sweep mode
        sweep_enabled = energy_layers.get("sweep_enabled", False)
        sweep_start_hz = float(energy_layers.get("sweep_start_hz", 20.0))
        sweep_end_hz = float(energy_layers.get("sweep_end_hz", 6.0))

        if sweep_enabled:
            # Frequency sweep mode — uses chirp generators
            if ent_method == "binaural":
                carrier = preset.get("left_hz", 100.0)
                binaural_stereo = generate_binaural_sweep(
                    total_samples, SAMPLE_RATE,
                    freq_start=sweep_start_hz,
                    freq_end=sweep_end_hz,
                    carrier_freq=carrier,
                    amplitude=binaural_amplitude * (energy_amp / 0.15),
                )
            elif ent_method == "isochronic":
                isochronic_stereo = generate_isochronic_sweep(
                    total_samples, SAMPLE_RATE,
                    freq_start=sweep_start_hz,
                    freq_end=sweep_end_hz,
                    carrier_frequency=200.0,
                    amplitude=0.12 * (energy_amp / 0.15),
                )
        else:
            # Standard fixed-frequency mode
            if ent_method == "binaural":
                binaural_stereo = generate_binaural_beats(
                    total_samples, SAMPLE_RATE,
                    preset["left_hz"], preset["right_hz"],
                    binaural_amplitude * (energy_amp / 0.15)  # scale relative to default
                )
            elif ent_method == "isochronic":
                isochronic_stereo = generate_isochronic_tones(
                    total_samples, SAMPLE_RATE,
                    beat_frequency=preset["beat_hz"],
                    carrier_frequency=200.0,
                    amplitude=0.12 * (energy_amp / 0.15),
                )

        # Solfeggio frequencies (pitch domain — always layerable)
        solf_freqs = energy_layers.get("solfeggio_freqs", [])
        if solf_freqs:
            # Validate frequencies against known Solfeggio set
            valid_freqs = [f for f in solf_freqs if f in SOLFEGGIO_FREQUENCIES]
            if valid_freqs:
                solfeggio_amp = 0.06 * (energy_amp / 0.15)
                solfeggio_stereo = generate_solfeggio_tones(
                    total_samples, SAMPLE_RATE,
                    frequencies=valid_freqs,
                    amplitude=solfeggio_amp,
                )

        # Schumann resonance (7.83 Hz — always layerable)
        if energy_layers.get("schumann", False):
            schumann_amp = 0.04 * (energy_amp / 0.15)
            schumann_stereo = generate_schumann_resonance(
                total_samples, SAMPLE_RATE,
                amplitude=schumann_amp,
            )
    elif include_binaural:
        # Legacy binaural mode (backward compatible)
        binaural_stereo = generate_binaural_beats(
            total_samples, SAMPLE_RATE,
            binaural_freq_left, binaural_freq_right, binaural_amplitude
        )

    # --- Masking Track ---
    # Use custom mask if provided, otherwise generate brown noise
    mask_stereo = None
    if method in ("masked", "both"):
        if custom_mask_path and os.path.isfile(custom_mask_path):
            # Load custom masking audio
            mask_audio = read_audio(custom_mask_path)
            mask_audio = pad_to_length(mask_audio, total_samples)
            if mask_audio.ndim == 1:
                mask_stereo = np.stack([mask_audio, mask_audio])
            else:
                mask_stereo = pad_to_length(mask_audio, total_samples)
            # Normalize custom mask to reasonable level
            mask_peak = np.max(np.abs(mask_stereo))
            if mask_peak > 0:
                mask_stereo = mask_stereo * (0.8 / mask_peak)
        else:
            mask_stereo = generate_brown_noise(total_samples, SAMPLE_RATE, mask_amplitude)

    # --- Silent tracks (for "both" method) ---
    silent_stereo = None
    if method == "both":
        # Scale silent layer to 25% so it doesn't dominate peak normalization
        # and bury the audible brown noise + whispers
        silent_scale = 0.25
        left_silent *= silent_scale
        right_silent *= silent_scale
        center_silent *= silent_scale

        # Pad silent tracks to total length and route to stereo
        left_silent_pad = pad_to_length(left_silent, total_samples)
        right_silent_pad = pad_to_length(right_silent, total_samples)
        center_silent_pad = pad_to_length(center_silent, total_samples)

        silent_stereo = np.zeros((2, total_samples), dtype=np.float32)
        # Left ear silent
        silent_stereo[0, :] += left_silent_pad
        # Right ear silent (with 50ms offset)
        offset_samples = int(0.050 * SAMPLE_RATE)
        if offset_samples < total_samples:
            silent_stereo[1, offset_samples:] += right_silent_pad[:total_samples - offset_samples]
        else:
            silent_stereo[1, :] += right_silent_pad[:total_samples]
        # Center silent (both ears)
        silent_stereo[0, :] += center_silent_pad * 0.5
        silent_stereo[1, :] += center_silent_pad * 0.5

    if progress_callback:
        progress_callback("Mixing final audio...", 85)

    # --- Mix all tracks ---
    mixed = np.zeros((2, total_samples), dtype=np.float32)

    # Layer vocal tracks
    mixed += left_stereo
    mixed += right_stereo
    mixed += center_stereo

    # Layer binaural beats (brainwave entrainment)
    if binaural_stereo is not None:
        mixed += binaural_stereo

    # Layer isochronic tones (brainwave entrainment — mutually exclusive with binaural)
    if isochronic_stereo is not None:
        mixed += isochronic_stereo

    # Layer Solfeggio frequencies (pitch domain — safe to layer with everything)
    if solfeggio_stereo is not None:
        mixed += solfeggio_stereo

    # Layer Schumann resonance (subtle earth frequency — safe to layer)
    if schumann_stereo is not None:
        mixed += schumann_stereo

    # Layer mask (on top or underneath — we add it; vocals are already attenuated)
    if mask_stereo is not None:
        mixed += mask_stereo

    # Layer silent/ultrasonic tracks (for "both" method)
    if silent_stereo is not None:
        mixed += silent_stereo

    # Final peak normalization to prevent clipping
    peak = np.max(np.abs(mixed))
    if peak > 0.98:
        mixed = mixed * (0.98 / peak)

    if progress_callback:
        progress_callback("Writing output file...", 95)

    # --- Export ---
    # Transpose for soundfile: (samples, channels)
    mixed_for_export = mixed.T
    write_wav(output_path, mixed_for_export, SAMPLE_RATE)

    if progress_callback:
        progress_callback("Done!", 100)

    return output_path

"""
Spectrogram Check — Verify ultrasonic energy in silent subliminal WAV output.

Loads the silent ultrasonic output WAV, generates:
1. A full spectrogram (time vs frequency, dB scale)
2. A frequency spectrum plot (average over time)
3. Highlights the >15kHz ultrasonic region

Save the plot as output/silent_spectrogram.png
"""

import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless rendering
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os

INPUT_WAV = "output/silent_test_output.wav"
OUTPUT_PNG = "output/silent_spectrogram.png"

def load_audio(path):
    """Load WAV and return stereo data, sample rate."""
    data, sr = sf.read(path, dtype='float32')
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    return data, sr

def compute_spectrogram(audio, sr, nperseg=4096, noverlap=3072):
    """Compute spectrogram using STFT. Returns freqs, times, dB spectrogram."""
    from scipy import signal
    f, t, Sxx = signal.spectrogram(
        audio, sr,
        nperseg=nperseg,
        noverlap=noverlap,
        window='hann',
        scaling='density'
    )
    # Convert to dB, floor at -120 dB
    Sxx_db = 10 * np.log10(np.maximum(Sxx, 1e-12))
    return f, t, Sxx_db

def compute_spectrum(audio, sr):
    """Compute average frequency spectrum (entire duration)."""
    n = len(audio)
    spec = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(n, 1/sr)
    # Convert to dB
    spec_db = 20 * np.log10(np.maximum(spec, 1e-12))
    return freqs, spec_db

def main():
    print(f"Loading: {INPUT_WAV}")
    data, sr = load_audio(INPUT_WAV)
    dur = data.shape[0] / sr
    ch = data.shape[1]
    print(f"  Sample rate: {sr} Hz")
    print(f"  Duration: {dur:.2f}s")
    print(f"  Channels: {ch}")
    print(f"  Peak: {np.max(np.abs(data)):.4f}")

    # Use left channel for analysis
    mono = data[:, 0]

    # Compute spectrogram and spectrum
    print("Computing spectrogram...")
    f_spec, t_spec, Sxx_db = compute_spectrogram(mono, sr)

    print("Computing frequency spectrum...")
    freqs, spec_db = compute_spectrum(mono, sr)

    # ---- PLOT ----
    print("Generating plot...")
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # --- Subplot 1: Spectrogram ---
    ax1 = axes[0]
    im = ax1.pcolormesh(t_spec, f_spec, Sxx_db, shading='gouraud', cmap='inferno', vmin=-120, vmax=0)
    ax1.set_yscale('symlog', linthresh=1000, linscale=0.5)
    ax1.set_ylim(0, sr / 2)

    # Highlight ultrasonic region (>15kHz)
    ax1.axhline(y=15000, color='#00ff88', linestyle='--', linewidth=2, alpha=0.8, label='15 kHz threshold')
    ax1.fill_between([t_spec[0], t_spec[-1]], 15000, sr/2, alpha=0.15, color='#00ff88')
    ax1.text(t_spec[-1] * 0.98, 16000, 'ULTRASONIC', color='#00ff88', fontsize=11,
             fontweight='bold', ha='right', va='bottom')

    # Annotate peak ultrasonic frequency
    ultrasonic_mask = f_spec > 15000
    if np.any(ultrasonic_mask):
        ultrasonic_Sxx = Sxx_db.copy()
        ultrasonic_Sxx[~ultrasonic_mask] = -999
        peak_ultra_idx = np.unravel_index(np.argmax(ultrasonic_Sxx), ultrasonic_Sxx.shape)
        peak_freq = f_spec[peak_ultra_idx[0]]
        peak_time = t_spec[peak_ultra_idx[1]]
        ax1.annotate(f'Peak: {peak_freq:.0f} Hz',
                     xy=(peak_time, peak_freq),
                     xytext=(peak_time + 0.5, peak_freq + 3000),
                     arrowprops=dict(arrowstyle='->', color='white', lw=1.5),
                     color='white', fontsize=10, fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))

    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Frequency (Hz)', fontsize=12)
    ax1.set_title('Silent Ultrasonic Subliminal — Spectrogram', fontsize=14, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax1, label='Power/Frequency (dB/Hz)')
    ax1.legend(loc='upper right')

    # --- Subplot 2: Average Frequency Spectrum ---
    ax2 = axes[1]
    ax2.semilogx(freqs, spec_db, color='#ff6b35', linewidth=1.2, alpha=0.9)
    ax2.set_xlim(20, sr / 2)
    ax2.set_ylim(-80, 80)
    ax2.set_xlabel('Frequency (Hz)', fontsize=12)
    ax2.set_ylabel('Magnitude (dB)', fontsize=12)
    ax2.set_title('Average Frequency Spectrum', fontsize=14, fontweight='bold')

    # Highlight ultrasonic region
    ax2.axvline(x=15000, color='#00ff88', linestyle='--', linewidth=2, alpha=0.8, label='15 kHz threshold')
    ax2.axvspan(15000, sr/2, alpha=0.12, color='#00ff88')
    ax2.text(16000, 70, 'ULTRASONIC', color='#00ff88', fontsize=11, fontweight='bold')

    # Annotate top ultrasonic peaks
    ultra_idx = freqs > 15000
    if np.any(ultra_idx):
        ultra_freqs = freqs[ultra_idx]
        ultra_spec = spec_db[ultra_idx]
        top_n = min(5, len(ultra_freqs))
        top_indices = np.argsort(ultra_spec)[-top_n:]
        for idx in reversed(top_indices):
            f = ultra_freqs[idx]
            v = ultra_spec[idx]
            ax2.annotate(f'{f:.0f} Hz',
                         xy=(f, v),
                         xytext=(f * 1.1, v + 3),
                         fontsize=8, color='#00ff88',
                         arrowprops=dict(arrowstyle='->', color='#00ff88', lw=0.8, alpha=0.6))

    # Annotate binaural beat peaks
    ax2.annotate('100 Hz\n(binaural left)',
                 xy=(100, spec_db[np.argmin(np.abs(freqs - 100))]),
                 xytext=(60, 50),
                 fontsize=9, color='#ffaa00',
                 arrowprops=dict(arrowstyle='->', color='#ffaa00', lw=1))
    ax2.annotate('106 Hz\n(binaural right)',
                 xy=(106, spec_db[np.argmin(np.abs(freqs - 106))]),
                 xytext=(150, 40),
                 fontsize=9, color='#ffaa00',
                 arrowprops=dict(arrowstyle='->', color='#ffaa00', lw=1))

    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    # --- Final energy stats ---
    n_total = len(mono)
    spec_total = np.abs(np.fft.rfft(mono))
    f_all = np.fft.rfftfreq(n_total, 1/sr)

    ultra_mask = f_all > 15000
    audible_mask = f_all <= 15000

    ultra_e = np.sum(spec_total[ultra_mask]**2)
    audible_e = np.sum(spec_total[audible_mask]**2)
    total_e = ultra_e + audible_e

    stats_text = (
        f"Ultrasonic (>15 kHz): {100*ultra_e/total_e:.1f}% energy\n"
        f"Audible (<15 kHz): {100*audible_e/total_e:.1f}% energy\n"
        f"Peak ultrasonic freq: {f_all[ultra_mask][np.argmax(spec_total[ultra_mask])]:.0f} Hz"
    )
    ax2.text(0.02, 0.97, stats_text, transform=ax2.transAxes,
             fontsize=10, fontfamily='monospace', verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='black', alpha=0.8, edgecolor='#00ff88'))

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()

    print(f"\n[DONE] Spectrogram saved to: {OUTPUT_PNG}")

    # Print final summary
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"  Ultrasonic energy: {100*ultra_e/total_e:.1f}%")
    print(f"  Audible energy:    {100*audible_e/total_e:.1f}%")
    peak_ultra_freq = f_all[ultra_mask][np.argmax(spec_total[ultra_mask])]
    print(f"  Peak ultrasonic:   {peak_ultra_freq:.0f} Hz")
    print(f"  Carrier target:    17,500 Hz")
    print(f"  Offset:            {abs(peak_ultra_freq - 17500):.0f} Hz")
    if peak_ultra_freq > 15000:
        print("  VERDICT:           PASS - Strong ultrasonic energy confirmed!")
    else:
        print("  VERDICT:           FAIL - No ultrasonic energy detected.")

if __name__ == '__main__':
    main()

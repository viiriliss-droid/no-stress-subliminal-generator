# No-Stress Subliminal Creator

A free, zero-cost desktop application that generates scientifically-optimized subliminal audio from your text affirmations. Built with AI assistance (Codebuff).

**No API keys. No subscriptions. No paid services. Free forever.**

## What It Does

You type in affirmations → the app generates a studio-quality WAV file with your words hidden beneath masking noise, ultrasonic carriers, and brainwave entrainment layers. Designed for subconscious reprogramming.

### Features

- **Dichotic listening** — separate affirmations for left ear, right ear, and center
- **Masked subliminals** — brown noise masking at configurable attenuation
- **Silent ultrasonic** — DSB-AM modulation at 17.5 kHz (inaudible to conscious hearing)
- **Binaural beats** — 5 presets (Delta 2 Hz through Gamma 40 Hz)
- **Isochronic tones** — pulsed single-frequency entrainment
- **Frequency sweep mode** — sweep brainwave frequency across the full audio duration
- **Solfeggio frequencies** — 9 sacred tones (174–963 Hz) as a harmonic bed
- **Schumann resonance** — 7.83 Hz Earth frequency grounding layer
- **6 one-click energy presets** — Deep Sleep, Meditation, Focus, Creativity, Manifestation, Energy Boost
- **Custom masking music** — upload your own audio instead of brown noise
- **Per-track voice selection** — different TTS voices for each ear
- **18 neural TTS voices** — Microsoft Edge text-to-speech (English)
- **Pitch-preserved tempo compression** — 1.0x–2.0x (phase vocoder)
- **48kHz / 24-bit stereo WAV** export
- **Live preview** — 10-second sample before full export
- **Modern dark UI** — glass morphism, animated progress bar, toast notifications

## Quick Start

### Option A: Download the .exe (Windows)

1. Go to the [Releases page](../../releases)
2. Download `Subliminal_Audio_Generator.exe` (180 MB)
3. Double-click to run — no installation needed

**Requirements:** Windows 10 or 11, internet connection (for TTS voices only)

### Option B: Run from source (any platform)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/subliminal-generator.git
cd subliminal-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get ffmpeg
# Download ffmpeg.exe (Windows) or install via package manager (Mac/Linux)
# Place ffmpeg.exe in the project folder

# 4. Run
python main.py              # Desktop mode (Windows, requires pywebview)
python main.py --browser    # Opens in your browser
python main.py --server     # Headless server mode
```

## How to Use

1. **Type affirmations** in the three text areas (Left Ear / Right Ear / Center)
2. **Configure settings** — choose masked, silent, or both; adjust tempo, volume, brainwave presets
3. **Optional:** Upload custom masking music, enable energy layers, set target duration
4. **Generate Speech Tracks** — converts your text to audio (requires internet)
5. **Preview** — listen to a 10-second sample
6. **Export** — save the full studio-quality WAV file

### Playback Requirements

- **Stereo headphones** required (for dichotic panning and binaural beats)
- Moderate volume (30–50%)
- Do NOT listen while driving or operating machinery

## Project Structure

```
├── main.py              # Entry point (Flask + pywebview)
├── server.py            # REST API backend
├── tts_engine.py        # Edge TTS integration
├── audio_processor.py   # Full DSP pipeline
├── gui.py               # Obsolete CustomTkinter GUI (kept for reference)
├── smoke_test.py        # 10-test verification suite
├── requirements.txt     # Python dependencies
├── Subliminal_Audio_Generator.spec  # PyInstaller build spec
├── HANDOVER.md          # Detailed handover document for developers
├── templates/           # HTML UI
├── static/              # CSS & JavaScript
└── ffmpeg.exe           # Portable ffmpeg (NOT included in repo — download separately)
```

## Building the .exe

```bash
# Install PyInstaller
pip install pyinstaller>=6.0

# Build (ffmpeg.exe must be in the project directory)
python -m PyInstaller Subliminal_Audio_Generator.spec --noconfirm

# Output: dist/Subliminal_Audio_Generator.exe (~180 MB)
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI | HTML5, CSS3, JavaScript (vanilla) |
| Desktop wrapper | pywebview (Windows WebView2) |
| Backend | Flask REST API |
| TTS | Microsoft Edge TTS (edge-tts) |
| Audio DSP | NumPy, SciPy, librosa, soundfile |
| Packaging | PyInstaller (single-file .exe) |

## Transparency & Security

This app is fully open-source. Every line of code is visible in this repository.

- **No data collection** — affirmations never leave your computer (except for TTS processing via Microsoft's Edge TTS API)
- **No network calls** beyond TTS and Google Fonts CDN
- **No background processes** — the app only runs while you're using it
- **Clean VirusTotal scan** — PyInstaller .exe files may trigger 1–3 false positives from obscure scanners; all major AV engines (Windows Defender, Kaspersky, Bitdefender, etc.) report clean

To verify yourself: read the source, run `python smoke_test.py`, or scan the .exe at [virustotal.com](https://www.virustotal.com).

## License

Free for personal use. Share with friends.

## Credits

- Audio techniques by vbizz
- Code by DeepSeek-V4-Pro (via Codebuff)
- Built with ❤️

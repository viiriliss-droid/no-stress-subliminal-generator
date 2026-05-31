# Subliminal Audio Generator — Handover Document

**Date:** May 31, 2026  
**Version:** 2.9 (Energy Layers + Frequency Sweep Mode)  
**Author:** Built with Codebuff (AI-assisted development)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [File Structure](#2-file-structure)
3. [Architecture & Data Flow](#3-architecture--data-flow)
4. [Key Features & Capabilities](#4-key-features--capabilities)
5. [Technology Stack & Dependencies](#5-technology-stack--dependencies)
6. [DSP Pipeline (Scientific Detail)](#6-dsp-pipeline-scientific-detail)
7. [Backend API Reference](#7-backend-api-reference)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Build & Packaging](#9-build--packaging)
10. [How to Run / Use](#10-how-to-run--use)
11. [Smoke Test Suite](#11-smoke-test-suite)
12. [Changelog](#12-changelog)
13. [Known Limitations & Future Improvements](#13-known-limitations--future-improvements)
14. [Scientific Reference](#14-scientific-reference)

---

## 1. Project Overview

The **Subliminal Audio Generator** is a zero-cost desktop application that autonomously generates scientifically-optimized subliminal audio from user-provided text affirmations. It implements every technique from the *Optimal Subliminal Audio Creation Guide* — dichotic listening, binaural beats, tempo compression, brown noise masking, custom mask support, and silent ultrasonic modulation — and outputs studio-quality 48kHz/24-bit stereo WAV files.

**v2.0** is a ground-up rewrite of the UI layer: the old CustomTkinter GUI has been replaced with a modern web-based interface (Flask backend + HTML/CSS/JS frontend), wrapped in a native desktop window via pywebview. The DSP engine (`audio_processor.py`) and TTS engine (`tts_engine.py`) remain battle-tested and unchanged at their core, with new features added.

**Core philosophy:** Free forever. No API keys, no paid services, no subscriptions.

**Status:** Fully functional, tested, and packaged as a Windows .exe (180 MB).

**v2.9** adds a full Energy Layers system: isochronic tones, Solfeggio frequencies, Schumann resonance, frequency sweep mode (chirp-based binaural/isochronic sweeps across the full audio duration), and 6 one-click energy presets. v2.8 added a native OS folder picker for export.

---

## 2. File Structure

```
nostress subliminal generator/
├── main.py                                  # Entry point — Flask + pywebview (100 lines)
├── server.py                                # Flask REST API backend (740 lines)
├── tts_engine.py                            # Edge TTS → MP3 → ffmpeg → WAV (676 lines)
├── audio_processor.py                       # Full DSP pipeline + energy layers + sweep (600+ lines)
├── gui.py                                   # ⚠️ OBSOLETE — CustomTkinter GUI, kept for reference
├── requirements.txt                         # Python dependencies (9 packages)
├── smoke_test.py                            # 10-test DSP verification suite (184 lines)
├── spectrogram_check.py                     # Spectrogram debugging utility
├── HANDOVER.md                              # This document
├── Subliminal_Audio_Generator.spec          # PyInstaller build spec (cleaned, no dead datas)
├── ffmpeg.exe                               # Portable ffmpeg 8.1.1 (217 MB)
├── Optimal_Subliminal_Audio_Creation_Guide.md  # The original scientific guide
│
├── templates/                               # Jinja2 HTML templates
│   └── index.html                        # Main app UI (420+ lines, energy layers card, sweep controls)
│
├── static/                               # Frontend assets
│   ├── css/
│   │   └── style.css                     # Black monochrome theme (850+ lines, energy layer + sweep styles)
│   └── js/
│       ├── api.js                        # REST API client (100 lines, energy presets endpoint)
│       └── app.js                        # Main app logic (1100+ lines, energy layers & sweep UI)
│
├── dist/
│   └── Subliminal_Audio_Generator.exe       # Packaged executable (180 MB)
│
├── build/                                   # PyInstaller intermediate files (~300 MB)
│
└── ~/Subliminal_Audio_Generator/output/     # Default output directory (user home)
    └── sessions/                            # Per-session temp files (auto-cleaned after 24h)
        └── <session_id>/
            ├── vocal_left.wav
            ├── vocal_right.wav
            ├── vocal_center.wav
            ├── binaural_beats.wav
            ├── custom_mask.wav              # If uploaded
            ├── looped/                      # Looped vocal tracks
            │   ├── vocal_left_looped.wav
            │   ├── vocal_right_looped.wav
            │   └── vocal_center_looped.wav
            ├── preview.wav                  # 10-second preview
            └── <user_filename>.wav          # Final export
```

### File Responsibilities

| File | Lines | Purpose |
|---|---|---|
| `main.py` | 100 | Entry point. Parses `--browser`/`--server`/`--port` args. Starts Flask in background thread, then launches pywebview desktop window (or browser). |
| `server.py` | 740 | Flask backend. 11 REST endpoints (added `/api/energy/presets` for energy layer presets). Preview endpoint generates FULL audio then clips (affirmations loop correctly, settings take effect). Wires `progress_callback` through `generate_subliminal()` for live percentage. Energy layers param extraction and passthrough. Diagnostic logging on TTS endpoint. Thread-safe with `gen_lock`. Session management with 24h auto-cleanup. PyInstaller-aware. |
| `tts_engine.py` | 676 | Edge TTS integration. 18 verified-valid English neural voices (4 invalid voices removed). **Tier 1:** In-process async with SSL monkey-patching (`ssl.create_default_context` patched to inject certifi CA bundle). **Tier 2:** edge-tts CLI via subprocess. **Tier 3:** Python subprocess with pre-check. `_ensure_ssl_certs()` checks frozen cert paths + monkey-patches ssl. `_is_audio_silent()` validates output. `_find_ffmpeg()` 3-tier search. Per-track voice support. Diagnostic print logging. |
| `audio_processor.py` | 600+ | DSP engine. All v1.x/v2.x functions plus: **Energy layers** (`generate_isochronic_tones()`, `generate_solfeggio_tones()`, `generate_schumann_resonance()`), **frequency sweep** (`generate_binaural_sweep()`, `generate_isochronic_sweep()` via chirp), **brainwave presets** (Delta/Theta/Alpha/Beta/Gamma), Solfeggio frequencies (174–963 Hz), **energy presets** (6 one-click configurations), `energy_layers` param on `generate_subliminal()` and `generate_preview()`. |
| `style.css` | 850+ | Black monochrome theme. CSS variables, glass morphism cards, gradient backgrounds, animated particles, custom sliders/checkboxes/selects, modal overlay/dialog, custom audio player, stale preview warning, animated progress bar, toast notifications, **energy layer styles** (panel, method selector, Solfeggio chip grid, Schumann toggle), **energy preset cards** (grid, hover, active states, tags), **sweep controls** (inputs, arrow, info panel, preset buttons), responsive breakpoints. |
| `index.html` | 420+ | Full layout. Header with branding, scrollable main content with 5 cards: Affirmations, Settings, **Energy Layers** (toggle, preset cards, entrainment method radio, frequency preset dropdown, sweep toggle + start/end Hz + sweep presets + info, Solfeggio chip grid, Schumann toggle, energy volume slider), Mask/Duration, Generate/Preview/Export. Preview choice modal, custom audio player, stale preview warning, animated progress bar. |
| `api.js` | 100 | `API` object with 8 methods wrapping `fetch()`. Handles JSON and FormData, normalizes error messages. Per-track voice params in `generateTTS()`. Includes `getProgress()` for polling. **`getEnergyPresets()`** for loading energy presets, brainwave presets, and Solfeggio frequencies. |
| `app.js` | 1100+ | Main controller. Session init, voice + **energy preset** loading, event listeners, settings hash (includes energy + sweep params), stale preview detection, TTS generation, preview choice modal, custom audio player, cache-busting, real progress polling, native Save As dialog, toast notifications. **Energy layer logic**: `buildSolfeggioGrid()`, `buildEnergyPresetCards()`, `applyEnergyPreset()`, `getSelectedSolfeggio()`, `getSweepParams()`, `getEffectiveDuration()`, `updateSweepInfo()`, `getEntrainmentMethod()`. Binaural toggle hidden when energy layers active. Sweep info panel updates dynamically when duration is known. |
| `smoke_test.py` | 184 | Headless DSP verification (10 tests). |
| `requirements.txt` | 13 lines | 9 pip-installable packages + ffmpeg + certifi note. |
| `.spec` | 110 | PyInstaller build spec. Bundles certifi SSL certs, aiohttp, multidict, yarl, frozenlist. Deduplicated hidden imports. |

---

## 3. Architecture & Data Flow

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DESKTOP WINDOW (pywebview)                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                  WEB UI (HTML/CSS/JS)                          │ │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │  Input   │  │  Settings    │  │  Preview/Export Panel    │ │ │
│  │  │  3 text  │  │  sliders etc │  │  Custom Audio Player     │ │ │
│  │  │  areas   │  │              │  │  Seek bar, play/pause    │ │ │
│  │  └────┬─────┘  └──────┬───────┘  │  ETA, stale warnings     │ │ │
│  │       │               │          └────────────┬─────────────┘ │ │
│  └───────┼───────────────┼───────────────────────┼───────────────┘ │
│          │   REST API    │                       │                  │
└──────────┼───────────────┼───────────────────────┼──────────────────┘
           │               │                       │
     ┌─────▼───────────────▼───────────────────────▼─────┐
     │               FLASK BACKEND (server.py)            │
     │                                                    │
     │  /api/session/create    /api/voices                │
     │  /api/tts/generate      /api/mask/upload           │
     │  /api/generate          /api/preview               │
     │  /api/progress/<id>     /api/download/<...>        │
     │  /api/audio/<...>       /api/waveform/<...>        │
     │                                                    │
     └──┬──────────────┬────────────────┬────────────────┘
        │              │                │
  ┌─────▼─────┐  ┌─────▼─────┐  ┌───────▼──────────┐
  │ tts_engine │  │  audio_   │  │  Sessions &      │
  │ edge_tts   │  │  processor│  │  File Management  │
  │ + ffmpeg   │  │  (DSP)    │  │  (24h cleanup)    │
  └────────────┘  └───────────┘  └──────────────────┘
```

### 3.2 Threading Model

- **Flask thread:** Runs the Werkzeug dev server on `127.0.0.1:5000` (daemon thread)
- **Flask request threads:** Werkzeug spawns one per request. DSP pipeline protected by `threading.Lock` (`gen_lock`) to prevent concurrent heavy processing
- **Main thread:** pywebview event loop (desktop mode) or `flask_thread.join()` (browser/server modes)
- **Frontend:** All JavaScript runs in the Chromium/Edge WebView2 runtime (async, single-threaded)

### 3.3 User Workflow

```
1. Open app → Session created (UUID) → Voices loaded from Edge TTS
2. Type affirmations into 3 text areas (Left/Right/Center)
3. Configure: method (masked/silent/both), speed, volume, binaural, voice
4. Optional: Upload custom masking music OR set target duration
5. Step 1: Click "Generate Speech Tracks" → TTS API called → tracks ready
6. Step 2: Click "Preview" → Modal asks "10s Sample" or "Full Audio"
   → Full audio generated, then clipped to 10s if chosen
   → Real-time progress shown as animated progress bar + percentage
   → Custom audio player shows seek bar, time, play/pause
7. Step 3: Click "Export Full Audio" → Full DSP pipeline runs with animated progress bar → native Save As dialog opens
8. If settings change → preview section turns orange with stale warning
```

---

## 4. Key Features & Capabilities

### 4.1 v2.x Features

| Feature | Description |
|---|---|
| **Energy Layers System** | Layer isochronic tones, Solfeggio frequencies, and Schumann resonance into the audio. Only one brainwave entrainment method at a time (binaural OR isochronic). Solfeggio and Schumann always layer safely in the pitch domain. |
| **Frequency Sweep Mode** | Sweep brainwave frequency linearly from start to end Hz over the full audio duration (chirp-based). Supports both binaural and isochronic entrainment. Live sweep info panel shows calculated sweep time once duration is known. |
| **One-Click Energy Presets** | 6 presets: Deep Sleep, Meditation, Focus, Creativity, Manifestation, Energy Boost. Each auto-fills entrainment method, frequency, Solfeggio selections, Schumann toggle, and energy volume. |
| **5 Brainwave Presets** | Delta (2 Hz), Theta (6 Hz), Alpha (10 Hz), Beta (20 Hz), Gamma (40 Hz) — selectable via dropdown for both binaural and isochronic modes. |
| **9 Solfeggio Frequencies** | 174–963 Hz sacred tonal frequencies, selectable as clickable chip grid. Mixed as a subtle harmonic bed at configurable amplitude. |
| **Schumann Resonance** | Optional 7.83 Hz Earth frequency grounding layer. Subtle, designed for quality headphones/subwoofer playback. |
| **Web-based UI** | Modern HTML/CSS/JS interface with black monochrome theme, glass morphism, drop shadows, animated particles, Google Fonts (Inter, Space Grotesk, JetBrains Mono) |
| **Preview Before Export** | 10-second preview generated via `/api/preview` — listen before committing to full render |
| **Three-Step Workflow** | Step 1: Generate Speech Tracks → Step 2: Preview (10s sample) → Step 3: Export Full Audio |
| **Per-Track Voice Selection** | Choose different TTS voices for Left Ear, Right Ear, and Center tracks (or use "Same as default") |
| **Custom Masking Music** | Upload your own audio (WAV, MP3, FLAC, OGG) as the masking layer instead of brown noise |
| **Auto-Looping to Duration** | Set target duration (seconds) — vocal tracks automatically loop to fill it (with tempo pre-compensation) |
| **Duration Presets** | One-click buttons: 1 min, 3 min, 5 min, 10 min, 30 min, 60 min |
| **Drag & Drop Upload** | Drag audio files directly onto the mask upload zone |
| **Keyboard Shortcuts** | Space bar triggers preview or toggles playback |
| **Toast Notifications** | Slide-in notifications for success/error/info messages |
| **Desktop + Browser Modes** | `python main.py` (desktop), `--browser` (web browser), `--server` (headless) |

### 4.2 Retained v1.x Features

- Three separate text areas for dichotic affirmation scripting
- Classic Masked, Silent Ultrasonic, and Both subliminal methods
- Pitch-preserved tempo compression (phase vocoder, 1.0x–2.0x)
- Vocal volume control (-40 to -10 dB)
- 5 brainwave entrainment presets (Delta through Gamma) with binaural or isochronic delivery
- Energy layers: isochronic tones, Solfeggio frequencies, Schumann resonance, frequency sweep
- 18 verified-valid Microsoft Edge neural TTS voices (English only)
- 48kHz/24-bit stereo WAV output
- All DSP processing is mathematically identical to v1.x

---

## 5. Technology Stack & Dependencies

### 5.1 Python Dependencies (pip-installable, all free)

| Package | Version | Purpose |
|---|---|---|
| `edge-tts` | ≥6.1.0 | Microsoft Edge neural TTS |
| `numpy` | ≥1.24.0 | Array math, FFT, signal generation |
| `scipy` | ≥1.10.0 | Butterworth filters, lfilter, signal processing |
| `soundfile` | ≥0.12.0 | WAV read/write (24-bit PCM) |
| `librosa` | ≥0.10.0 | Phase vocoder time-stretch |
| `flask` | ≥3.0.0 | REST API backend |
| `flask-cors` | ≥4.0.0 | CORS headers for dev mode |
| `pywebview` | ≥5.0.0 | Wrap web UI in native desktop window |
| `pyinstaller` | ≥6.0 | Build standalone .exe (dev dependency) |

### 5.2 Frontend Dependencies (CDN-loaded)

| Library | Version | Purpose |
|---|---|---|
| Google Fonts | — | Inter, Space Grotesk, JetBrains Mono |

> **Note:** WaveSurfer.js and Regions plugin were removed in v2.4. No audio visualization libraries are loaded. HTML5 `<audio>` element handles preview playback.

### 5.3 System Dependencies

| Component | Required? | Purpose |
|---|---|---|
| **ffmpeg** | Yes | MP3→WAV conversion. Bundled as `ffmpeg.exe` (217 MB). Also works from system PATH. |
| **Microsoft Edge WebView2** | Yes (desktop mode) | Runtime for pywebview's embedded browser. Pre-installed on Windows 10/11. |

### 5.4 Internet Requirements

- **TTS generation:** Required (Edge TTS API)
- **Google Fonts CDN:** Required on first load (browser-cached thereafter)
- **DSP processing:** 100% offline
- **Custom mask playback in editor:** 100% offline (local WAV files served by Flask)

---

## 6. DSP Pipeline (Scientific Detail)

Identical to v1.x with two additions:

### 6.1 New: Energy Layers & Frequency Sweep

**`generate_isochronic_tones()`** — Pulsed single-frequency beat at configurable rate and carrier frequency. Cosine-smoothed envelope with adjustable duty cycle. Mono-compatible, no headphones required.

**`generate_solfeggio_tones()`** — Layer of Solfeggio frequency sine waves (174–963 Hz) mixed at low amplitude as a harmonic bed. Each frequency gets a deterministic phase offset for natural sound. Operates in the pitch domain — always safe to layer with any other technique.

**`generate_schumann_resonance()`** — 7.83 Hz sine wave with 10 Hz lowpass filtering. Very low amplitude (0.04 default). Adds a subtle grounding layer at the Earth's electromagnetic resonant frequency.

**`generate_binaural_sweep()`** — Chirp-based binaural beats using `scipy.signal.chirp` for mathematically accurate linear frequency sweep. Left ear plays constant carrier; right ear sweeps from `carrier + freq_start` to `carrier + freq_end`.

**`generate_isochronic_sweep()`** — Sweeping isochronic tones via instantaneous phase integration. The cosine pulse envelope frequency sweeps linearly from start to end Hz over the full audio duration.

**Design rule:** Only ONE brainwave entrainment source at a time (binaural OR isochronic). Solfeggio and Schumann operate in different perceptual domains (pitch and sub-audible respectively) and can always layer on top without conflict. Different frequencies cannot destructively interfere — they simply sum additively.

### 6.2 New: Energy Presets

- **`ENERGY_PRESETS`** dict with 6 one-click configurations: Deep Sleep, Meditation, Focus, Creativity, Manifestation, Energy Boost
- Each preset specifies: entrainment method, frequency preset, Solfeggio frequencies, Schumann toggle, and energy amplitude
- Exposed via `/api/energy/presets` endpoint

### 6.3 New: `loop_vocals_to_duration()`
- Takes a mono vocal array and a target duration in seconds
- Repeats end-to-end until target reached, trims final loop
- Tempo pre-compensation in server.py: loops to `target_duration × speed_factor` so after phase vocoder compression, final duration equals `target_duration`

### 6.4 New: `generate_preview()`
- Lightweight version of `generate_subliminal()` for 10-second clips
- Applies the same preprocessing → tempo → method → routing → mix pipeline
- Used by the Preview API endpoint for quick auditioning before full export

### 6.5 New: `custom_mask_path` on `generate_subliminal()`
- When a custom mask path is provided and the file exists, loads that audio as the masking layer instead of generating brown noise
- Normalizes custom mask to 0.8 peak amplitude for consistent mix levels

### 6.6 Full Pipeline (updated for v2.9)
1. **Preprocess:** 80 Hz HPF → RMS compressor (threshold -16 dB, ratio 3:1, attack 5ms, release 50ms) → peak normalize to -1 dB
2. **Tempo Compress:** Phase vocoder via `librosa.effects.time_stretch` (pitch-preserved)
3. **Subliminal Method:**
   - *Masked:* Attenuate vocals by `vocal_attenuation_db`, layer brown noise (cumulative-sum integration + 20 Hz HPF)
   - *Silent:* Bandpass 150–4000 Hz → DSB-AM modulate at 17,500 Hz carrier
   - *Both:* Attenuated masked + 25%-scaled silent layer
4. **Dichotic Routing:** Left hard-panned (Right hemisphere), Right hard-panned with 50ms offset (Left hemisphere), Center at 50% both channels
5. **Brainwave Entrainment (one of):**
   - *Binaural Beats:* Preset-based (Delta 2 Hz through Gamma 40 Hz) or frequency sweep (chirp-based)
   - *Isochronic Tones:* Pulsed carrier at preset beat frequency or frequency sweep
6. **Energy Layers (optional, always layerable):**
   - *Solfeggio Frequencies:* Multi-frequency harmonic bed (174–963 Hz)
   - *Schumann Resonance:* 7.83 Hz subtle grounding layer
7. **Mix & Normalize:** Sum all layers, peak normalize to 0.98, export 48kHz/24-bit stereo WAV

---

## 7. Backend API Reference

All endpoints are prefixed with `/api/`. Session-scoped audio files are served from `/api/audio/<session_id>/<filename>`.

### `POST /api/session/create`
Create a new session. Returns `{"session_id": "abc123..."}`.

### `GET /api/voices`
Returns `{"voices": {"Aria (US Female - Warm)": "en-US-AriaNeural", ...}, "default": "en-US-AriaNeural"}`.

### `POST /api/tts/generate`
**Body:** `{"session_id", "left_text", "right_text", "center_text", "voice"}`
**Returns:** `{"tracks": {"left": "vocal_left.wav", ...}, "durations": {"left": 3.5, ...}}`
Also generates `binaural_beats.wav` for editor visualization.

### `POST /api/mask/upload`
**Body:** Multipart form with `file` and `session_id`.
Converts uploaded audio to 48kHz mono WAV. Returns `{"filename", "duration", "waveform": {"peaks": [...], "duration": ...}}`.

### `GET /api/progress/<session_id>`
Poll for real-time generation progress (polled by frontend every 500ms during preview and export).
Returns `{"percent": 27, "message": "Mixing tracks...", "done": false}`.  
`percent` ranges 0–100, `done` is `true` when the operation completes. If session doesn't exist, returns `{"percent": 0, "message": "No active session", "done": true}`.

### `POST /api/generate`
**Body:** `{"session_id", "method", "speed_factor", "vocal_volume_db", "include_binaural", "use_custom_mask", "target_duration", "output_filename", "energy_layers"}`  
Runs full DSP pipeline. Protected by `gen_lock`. Reports progress via `sessions[session_id]["progress"]`.  
**`energy_layers` object (optional):** `{"entrainment_method": "binaural"|"isochronic"|null, "entrainment_preset": "theta", "solfeggio_freqs": [528, 396], "schumann": true, "energy_amplitude": 0.15, "sweep_enabled": false, "sweep_start_hz": 20.0, "sweep_end_hz": 6.0}`  
Returns `{"output_file", "output_path", "duration", "waveform": {...}}`.

### `POST /api/preview`
**Body:** `{"session_id", "method", "speed_factor", "vocal_volume_db", "include_binaural", "use_custom_mask", "target_duration", "preview_duration", "energy_layers"}`  
Generates the FULL subliminal audio first (loops vocals, runs complete DSP pipeline), then clips the first `preview_duration` seconds using ffmpeg. Reports real progress via the progress endpoint. **`energy_layers` object (optional):** same structure as `/api/generate`. Returns `{"preview_file": "preview.wav", "duration", "full_duration", "gen_time_seconds"}`.

### `GET /api/waveform/<session_id>/<filename>`
Returns `{"peaks": [0.1, 0.5, ...], "duration": 3.5, "sample_rate": 48000}` for waveform visualization.

### `GET /api/energy/presets`
Returns `{"brainwave_presets": {...}, "solfeggio_frequencies": [{hz, label}, ...], "schumann_hz": 7.83, "energy_presets": {...}}`.  
Provides all available brainwave entrainment presets (Delta through Gamma), Solfeggio frequency definitions, and 6 one-click energy presets (Deep Sleep, Meditation, Focus, Creativity, Manifestation, Energy Boost). Used by the frontend to populate the Energy Layers UI card.

### `GET /api/download/<session_id>/<filename>`
Serves WAV file with `Content-Disposition: attachment` header, triggering the browser's native Save As dialog. Same as `/api/audio` but forces download instead of inline playback.

---

## 8. Frontend Architecture

### 8.1 Module Dependency Graph

```
index.html
  ├── Google Fonts (Inter, Space Grotesk, JetBrains Mono)
  ├── style.css
  ├── api.js          → defines global API object
  └── app.js          → uses API
```

### 8.2 `API` Object (`api.js`)
- `API.createSession()` → `POST /api/session/create`
- `API.getVoices()` → `GET /api/voices`
- `API.generateTTS(sid, left, right, center, voice, leftVoice, rightVoice, centerVoice)` → `POST /api/tts/generate`
- `API.uploadMask(sid, file)` → `POST /api/mask/upload` (FormData)
- `API.generateSubliminal(sid, settings)` → `POST /api/generate`
- `API.generatePreview(sid, settings)` → `POST /api/preview`
- `API.getAudioUrl(sid, filename)` → returns URL string
- `API.getProgress(sid)` → `GET /api/progress/<sid>` (returns `{percent, message, done}`)

> **Note:** `getWaveform()` was removed in v2.4 along with WaveSurfer.js. The `/api/waveform` endpoint still exists server-side but is unused. `getProgress()` was added in v2.6 for real-time percentage polling.

### 8.3 Main App Logic (`app.js`)
- **Init:** Creates background particles, session, loads voices, loads energy presets
- **Energy layers UI:** `buildSolfeggioGrid()` populates the Solfeggio frequency chip grid; `buildEnergyPresetCards()` renders the 6 one-click preset cards; `applyEnergyPreset()` auto-fills all energy fields when a preset is clicked
- **Sweep mode:** `getSweepParams()` reads start/end Hz; `getEffectiveDuration()` determines total audio length from mask upload, TTS vocal durations, or manual duration input; `updateSweepInfo()` shows live sweep info (e.g. "20.0 Hz → 6.0 Hz over 5m 0s" or "Sweep time will be calculated when the audio duration is known")
- **Event wiring:** Character counters, slider live labels, mask drag-drop, duration presets, keyboard shortcuts, energy layer events (toggle, method radio, sweep toggle + inputs, Solfeggio chips, Schumann toggle, energy volume slider, sweep preset buttons)
- **Settings hash:** `computeSettingsHash()` joins all settings + text + energy layer params into `|`-separated string; compared on every change
- **Stale detection:** If hash changes after a preview was generated, preview section turns orange with "⚠ Current Preview is not up-to-date. Generate a new one!"
- **Preview choice modal:** Two buttons — "10 Second Sample" (clips 10s from full audio) or "Full Audio Preview" (plays complete subliminal). Both generate full audio first, then clip.
- **Custom audio player:** Play/pause button, seek bar (`<input type="range">` synced to `audio.currentTime`), current time / total time display. Clicking the play button when audio is loaded toggles play/pause; when no audio is loaded, opens the preview choice modal
- **Cache-busting:** Preview URL gets `?t=<timestamp>` appended so volume/voice changes always load fresh audio
- **Progress polling:** `startProgressPolling(onProgress, onDone)` polls `API.getProgress()` every 500ms. Used by both preview and export for real percentage display
- **ETA:** Preview and export show live percentage from the server (e.g. "27% — Mixing tracks..."). When done, export shows elapsed time ("Completed in 45.2s")
- **TTS flow:** Validates text → `API.generateTTS()` → shows TTS status + preview section → enables export
- **Preview flow:** Modal → `API.generatePreview()` with `preview_duration` → plays via custom player → cache-busted URL → real progress shown
- **Export flow:** Calls `API.generateSubliminal()` → progress bar animates with live percentage → on success, uses File System Access API (`showSaveFilePicker`) or fallback `<a download>` to save
- **State:** `{sessionId, voice, leftVoice, rightVoice, centerVoice, tracksGenerated, maskUploaded, maskDuration, vocalMaxDuration, isGenerating, audioLoaded, lastSettingsHash, previewDuration, energyPresets}`
- **Keyboard:** Space bar toggles custom player play/pause, or opens preview modal if no audio loaded

---

## 9. Build & Packaging

### 9.1 PyInstaller Configuration

- **Tool:** PyInstaller 6.20
- **Spec file:** `Subliminal_Audio_Generator.spec`
- **Mode:** Single-file (`EXE()`, no `COLLECT`), no console window (`console=False`)
- **Name:** `Subliminal_Audio_Generator.exe`
- **Size:** 180 MB (~165 MB ffmpeg + ~15 MB Python/DSP/Flask/web files)
- **Output:** `dist/Subliminal_Audio_Generator.exe`

### 9.2 Bundle Details

| Category | Items |
|---|---|
| **Bundled binaries** | `ffmpeg.exe` (portable ffmpeg 8.1.1) |
| **Bundled data** | `templates/`, `static/` directories |
| **Collected packages** | edge_tts, soundfile, librosa, scipy, flask, flask_cors, jinja2 |
| **Hidden imports** | Flask ecosystem (flask.*), pywebview and platform backends, werkzeug, jinja2, markupsafe, itsdangerous, click, blinker, scipy/numba/sklearn internals |

### 9.3 PyInstaller Frozen Mode Support

`server.py` detects PyInstaller bundled mode via `sys.frozen` and uses `sys._MEIPASS` for template/static resolution. Output files are saved to `~/Subliminal_Audio_Generator/output/` (user home directory) instead of the temp `_MEIPASS` directory.

### 9.4 To Rebuild

```bash
cd "C:\Users\niala\OneDrive\Documents\nostress subliminal generator"
python -m PyInstaller Subliminal_Audio_Generator.spec --noconfirm
```

### 9.5 Build Warnings (non-critical)

PyInstaller produces warnings about missing optional sub-modules:
- `pkg_resources.py2_warn` (legacy setuptools, not needed)
- `flask.scaffold` (renamed in Flask 3.x)
- `pycparser.lextab/yacctab` (optional cffi parsing tables)
- `scipy.special._cdflib` (optional scipy extension)
- `tbb12.dll` not resolved for numba (not used in our pipeline)

These do not affect functionality.

---

## 10. How to Run / Use

### 10.1 From Source (Python)

```bash
cd "C:\Users\niala\OneDrive\Documents\nostress subliminal generator"
pip install -r requirements.txt
# Ensure ffmpeg.exe is in the project directory or installed system-wide

# Desktop mode (requires pywebview)
python main.py

# Browser mode (opens in Chrome/Edge)
python main.py --browser

# Server only (headless)
python main.py --server --port 5000
```

### 10.2 From Packaged .exe

Double-click `dist/Subliminal_Audio_Generator.exe`

### 10.3 Usage Steps

1. Enter affirmations in the three text areas (one per line)
2. Choose subliminal method (Masked, Silent, or both)
3. Adjust tempo, vocal volume, binaural beats, and TTS voice
4. Optional: Upload custom masking music (or set target duration)
5. Click **Generate Speech Tracks** — wait ~10–20 seconds (internet required)
6. Click **Preview** — choose "10 Second Sample" or "Full Audio Preview" from the modal
7. Use the custom audio player (seek bar, play/pause, time display) to audition your audio
8. Click **Export Full Audio** — full DSP pipeline runs with animated progress bar, then browser Save As dialog opens
9. Choose where to save the WAV file in the native file dialog

### 10.4 Playback Requirements

- **Stereo headphones required** (for dichotic panning and binaural beats)
- **Moderate volume** (30–50%) — especially for silent/ultrasonic files
- **Do NOT listen while driving or operating machinery**

---

## 11. Smoke Test Suite

### 11.1 Running Tests

```bash
cd "C:\Users\niala\OneDrive\Documents\nostress subliminal generator"
python smoke_test.py
```

### 11.2 Test Coverage (10 Tests)

| # | Test | What It Verifies |
|---|---|---|
| 1 | Synthetic track generation | Audio file creation and duration |
| 2 | Tempo compression (1.35x) | Duration correctly shortened by 35% |
| 3 | Brown noise (with DC filter) | DC offset ≈ 0, stereo shape, amplitude |
| 4 | Binaural beats (100/106 Hz) | Stereo separation, amplitude |
| 5 | Bandpass filter (150–4000 Hz) | Signal passes through, correct attenuation |
| 6 | DSB-AM modulation (17.5 kHz) | Peak frequency shifted to ultrasonic (>15 kHz) |
| 7 | Full masked pipeline | Stereo WAV, 48kHz, proper duration, peak amplitude |
| 8 | Full silent pipeline | Ultrasonic peak >15 kHz, proper format |
| 9 | Vocal preprocessing | Peak normalized to -1 dB |
| 10 | Gain smoothing | Asymmetric attack/release |

**Last result:** ALL 10 TESTS PASSED (verified v2.9).

---

## 12. Changelog

### v2.9 (May 31, 2026) — Energy Layers System + Frequency Sweep Mode

**Energy Layers System:**
- New `generate_isochronic_tones()` — Pulsed single-frequency beats at configurable rate/carrier/duty cycle. Mono-compatible, no headphones needed
- New `generate_solfeggio_tones()` — Multi-frequency harmonic bed using sacred Solfeggio frequencies (174–963 Hz). Operates in the pitch domain, always safe to layer
- New `generate_schumann_resonance()` — 7.83 Hz Earth frequency subtle grounding layer with lowpass filtering
- 5 brainwave entrainment presets (Delta 2 Hz, Theta 6 Hz, Alpha 10 Hz, Beta 20 Hz, Gamma 40 Hz) for both binaural and isochronic modes
- 9 Solfeggio frequencies selectable as a clickable chip grid in the UI
- Design rule: only ONE brainwave entrainment source at a time (binaural OR isochronic). Solfeggio and Schumann always layer safely

**Frequency Sweep Mode:**
- New `generate_binaural_sweep()` — Chirp-based binaural beats using `scipy.signal.chirp` for mathematically accurate linear frequency sweep over the full audio duration
- New `generate_isochronic_sweep()` — Sweeping isochronic pulse rate via instantaneous phase integration
- UI: Toggle + start/end Hz inputs + quick sweep preset buttons (Beta→Theta, Alpha→Delta, Theta→Delta, Gamma→Alpha)
- Live sweep info panel displays calculated sweep range and time once duration is known (e.g. "20.0 Hz → 6.0 Hz over 5m 0s")

**Energy Presets:**
- 6 one-click presets: Deep Sleep, Meditation, Focus, Creativity, Manifestation, Energy Boost
- New `ENERGY_PRESETS` dict in `audio_processor.py`, exposed via `/api/energy/presets` endpoint
- Frontend: Visual preset cards that auto-fill entrainment method, frequency, Solfeggio selections, Schumann toggle, and energy volume

**Backend:**
- New `GET /api/energy/presets` endpoint returns brainwave presets, Solfeggio frequencies, and energy presets
- Both `/api/generate` and `/api/preview` accept `energy_layers` object with full energy/sweep configuration
- Backward compatible — existing API calls without `energy_layers` work identically

**Build:** .exe size 180 MB

### v2.8 (May 30, 2026) — Native OS Folder Picker for Export

**Native folder picker before export:**
- Export now prompts the user to choose where to save BEFORE generation starts, using the `window.showSaveFilePicker()` API (File System Access API)
- Opens the native OS file picker — same UX as the drag-and-drop import for masking music, but for saving
- User navigates to a folder, picks a filename, and confirms — then generation begins with full progress bar
- After generation, the audio file is written directly to the user-chosen location via the File System Access API
- Falls back to `<a download>` (browser Save As dialog) if `showSaveFilePicker` is not supported
- If user cancels the file picker, export aborts cleanly with no UI state changes

**Build:** .exe size 180 MB

### v2.7 (May 30, 2026) — Animated Progress Bar, Native Save Dialog

**Animated progress bar:**
- Redesigned progress bar with 10px height, gradient fill (dark → light shimmer), and glow effect
- Added percentage badge (`#progressPct`) alongside the status message for dual feedback (e.g. "27%" badge + "Mixing tracks..." text)
- Added shimmer animation — a light sweep moves across the bar while processing
- Smooth slide-in animation when the bar appears, smooth width transitions
- Moved progress bar INSIDE the Generate & Preview card (was at the bottom of the page, easy to miss)
- `setProgress()` updated to drive both `#progressFill` width and `#progressPct` text

**Native save dialog (replaces output directory text field):**
- Added `GET /api/download/<session_id>/<filename>` endpoint — serves WAV with `Content-Disposition: attachment`, triggering the browser's native Save As dialog
- `app.js` `handleExport()`: After successful export, creates a temporary `<a>` element pointing to `/api/download`, clicks it to trigger save dialog, then removes it
- Removed `outputDirInput` text field from `index.html` — no more typing paths
- Removed all `output_dir` handling from `server.py` (extraction, validation, copy block, docstring)
- User now picks save location via their OS file dialog instead of typing a directory path

**Build:** .exe size 180 MB

### v2.6 (May 30, 2026) — Folder Restructure, Real Progress Polling, Output Directory

**Folder restructuring:**
- All program files moved from `subliminal_generator/` subdirectory to project root
- Removed dead directories: `build/`, `__pycache__/`, `staticcss/`, `staticjs/`, `output/`, `subliminal affirmations/`
- PyInstaller spec cleaned up — removed dead `('output', 'output')` datas entry
- Build instructions and run commands updated to reflect flat project structure

**Real progress polling (replaces simulated ETA):**
- Added `GET /api/progress/<session_id>` polling endpoint — returns `{percent, message, done}`
- Server wires `progress_callback` through `generate_subliminal()` for live percentage (e.g. "27% — Mixing tracks...")
- `preview()` endpoint also reports real progress (not simulated) since it now runs the full pipeline
- `app.js`: `startProgressPolling(onProgress, onDone)` polls every 500ms, replaces `setInterval` countdown
- Both preview and export show live percentage from the server; export shows elapsed time on completion

**Export to custom directory:**
- `index.html`: Added `outputDirInput` text field — user can specify where to save the final WAV
- `server.py` `generate()` endpoint: validates `output_dir` before DSP work (fast-fail if directory doesn't exist), copies final file to user-chosen directory via `shutil.copy2()`
- Returns HTTP 400 with clear error if output directory doesn't exist or can't be written to
- If no `output_dir` provided, saves to default session directory as before

**Build:** .exe size 180 MB

### v2.5 (May 30, 2026) — Preview Fixes, Stale Detection, Custom Player, Valid Voices, Modal, ETA

**Voices fixed:**
- Removed 4 invalid voices causing "No audio was received" errors: `en-US-DavisNeural`, `en-US-RogerNeural`, `en-US-MichelleNeural`, `en-US-JaneNeural` (not real Microsoft Edge TTS voices)
- Replaced with 18 verified-valid English neural voices from Azure Voice Gallery 2025

**Preview now generates full audio then clips:**
- `server.py` preview endpoint rewritten: generates the COMPLETE subliminal first (loops vocals, runs full DSP pipeline via `generate_subliminal()`), then uses ffmpeg to clip the first N seconds
- Fixes the "preview sounds the same" bug — was only processing raw first N seconds of vocals instead of running full pipeline
- Fixes the "volume doesn't change in preview" bug — full pipeline ensures volume/voice settings take effect
- Cleans up intermediate looped files and full temp file after clipping
- Uses explicit ffmpeg codec `-acodec pcm_s24le` instead of fragile `-c copy`

**Preview choice modal:**
- When clicking Preview, a modal overlay appears with two options:
  - **"10 Second Sample"** — generates full audio, clips first 10s (~ETA same as full)
  - **"Full Audio Preview"** — generates complete subliminal for auditioning before export
- Both options call the same server endpoint with different `preview_duration` values
- Modal has close button, click-outside-to-close, and smooth slide-in animation

**Custom audio player:**
- Replaced hidden `<audio>` element with a custom player: play/pause button, seek bar (`<input type="range">` on `timeupdate`), current time / total time display
- Play button toggles between play triangle and pause rectangles
- Clicking play when audio is loaded → toggles playback; when no audio → opens preview modal
- Keyboard Space bar uses same logic

**Stale preview detection:**
- `computeSettingsHash()` joins all settings + text into a hash string on every change
- When hash differs from `lastSettingsHash` (saved after successful preview), preview section turns orange-red with: "⚠ Current Preview is not up-to-date. Generate a new one!"
- Any setting change triggers `onSettingChanged()` — text input, sliders, voice selects, method checkboxes, binaural toggle, mask upload, duration
- Mask upload success now triggers stale detection (was missing)

**ETA (Estimated Time):**
- Preview: Shows "ETA: ~Xs" based on target duration × 0.4 heuristic, displayed next to preview label during generation
- Export: Shows "Estimated export time: ~Xm" before generation, then elapsed time counter during generation
- `server.py` returns `gen_time_seconds` and `full_duration` for future ETA refinement

**Cache-busting:**
- Preview URL gets `?t=<Date.now()>` appended so volume/voice/affirmation changes always fetch fresh audio from the server
- Fixes stale browser caching causing "same preview" when settings changed

**Bug fixes from code review:**
- `previewPlayBtn` click handler now gates on `state.audioLoaded` (was always opening modal)
- `state.audioLoaded` reset to `false` on preview failure
- 10s preview ETA now matches full audio ETA since both generate full audio first
- Server no longer duplicates `import subprocess` inside preview function
- Looped preview intermediates cleaned up after clipping

**Build:** .exe size 181 MB

### v2.4 (May 30, 2026) — Simplified UI: WaveSurfer Removed, Black Monochrome, Preview+Export Flow

**Major simplification — removed all waveform editing complexity:**
- Removed WaveSurfer.js and Regions plugin CDN imports from `index.html` (no more audio visualization libraries)
- Deleted `static/js/waveform.js` (338 lines of WaveformEditor class) — no longer needed
- All waveform toolbar buttons removed (Play, Stop, Zoom In/Out, Fit)
- Per-track solo/mute/volume/speed controls removed (unnecessary complexity)

**New black monochrome colour scheme:**
- Complete `style.css` rewrite (~540 lines): CSS variables in black/white/grey palette
- Gradient backgrounds, glass morphism cards, animated floating particles
- Drop shadows, smooth transitions, modern custom form controls
- All purple/accent colours replaced with monochrome equivalents

**New header branding:**
- App title: "No-Stress Subliminal Creator"
- Subtitle: "Made with love by vbizz (Audio Techniques) and DeepSeek-V4-Pro (Coding)"

**Simplified three-step workflow:**
- Step 1: "Generate Speech Tracks" — TTS API called, status shows track durations
- Step 2: "Preview" — 10-second sample mixed and played via HTML5 `<audio>` element
- Step 3: "Export Full Audio" — Full DSP pipeline runs, WAV saved
- Preview and Export are now separate buttons (previously export auto-generated preview)

**`app.js` rewrite (~340 lines):**
- Removed ALL WaveSurfer/editor references (no `window.waveformEditor`, `editor.addTrack`, etc.)
- Preview handler uses HTML5 Audio element with `readyState` check for instant playback on cached reloads
- Keyboard Space bar now triggers preview or toggles playback (instead of waveform transport)
- TTS handler shows track durations in status text after generation

**`api.js` cleanup:**
- Removed `getWaveform()` method (no longer needed without waveform visualization)

**Known limitation:** The `/api/waveform/...` endpoint still exists in `server.py` but is unused by the frontend. Could be removed in a future cleanup.

**Build:** .exe size 181 MB

### v2.3 (May 30, 2026) — TTS Fix v2: SSL Certs in Frozen Env + System Python Fallback

**Root Cause (confirmed):** Two bugs in the PyInstaller-frozen .exe prevented TTS from working:
1. **Subprocess:** `sys.executable` is the `.exe` itself (with argparse from main.py), not a Python interpreter — it rejected `-c "python code"` as unrecognized arguments
2. **Async/In-process:** `certifi.where()` returned a path in a non-existent site-packages directory. SSL/TLS handshake to Microsoft Edge TTS failed silently, producing empty audio

**Fixes:**
- **`_ensure_ssl_certs()` rewritten:** When frozen, checks `sys._MEIPASS/certifi/cacert.pem` first (where the .spec bundles it), then `sys._MEIPASS/certifi/certifi/cacert.pem`, then falls back to `certifi.where()`. Uses `os.environ[]` assignment (not `setdefault`) to force-override. Added diagnostic print logging.
- **`_find_system_python()` added:** In dev mode returns `sys.executable`. In frozen mode: searches PATH for `python`/`python3`/`py` (excluding our own .exe), then checks `%LOCALAPPDATA%\Programs\Python`, `%PROGRAMFILES%\Python`, `C:\Python` for `python.exe`.
- **`_generate_mp3_subprocess()` updated:** Uses `_find_system_python()` instead of `sys.executable`. Clear error if no system Python found.
- **Priority swapped:** Async (TIER 1, primary) → Subprocess (TIER 2, fallback). Only tries subprocess if system Python found. Better combined error messages.
- **Dead variables removed:** `tried_async` and `tried_subprocess` were assigned but never read.

**Build:** .exe size 181 MB

### v2.2 (May 30, 2026) — Subprocess-Based TTS + SSL Fix for PyInstaller

**Root Cause Fix — TTS silently produced empty audio in bundled .exe:**
- `edge_tts` Python API fails silently in PyInstaller-frozen environments due to missing SSL certificates (`certifi` not bundled) and asyncio event-loop fragility in nested-thread contexts
- Symptom: vocal WAV files created but containing only silence (0.0 peak amplitude)

**Subprocess-Based TTS (PRIMARY):**
- `_generate_mp3_subprocess()`: Runs `edge_tts` in a completely independent subprocess via `sys.executable -c`
- Subprocess has its own event loop, SSL stack, and no threading complications — works reliably in frozen environments
- Passes text/voice/output as JSON via command-line argument (safe, no shell injection)
- Generates clean MP3 files in the subprocess, validated by parent before ffmpeg conversion

**In-Process Async API (FALLBACK):**
- `_generate_mp3_async()`: Kept as fallback for environments where subprocess fails
- `generate_speech_sync()`: Tries subprocess first, falls back to async, reports both errors if all fail

**Audio Silence Detection:**
- `_is_audio_silent()`: Validates generated WAV has actual audio content (>0.001 peak amplitude)
- Catches silently-failed TTS requests that return empty audio

**SSL Certificate Fix:**
- `_ensure_ssl_certs()`: Sets `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` from certifi at module load
- Enables HTTPS in both in-process and subprocess TTS methods

**PyInstaller Spec Updates:**
- Bundles certifi's certificate file as a binary dependency
- Added `certifi` and `aiohttp` to `collect_all()` loop
- Extensive hidden imports: aiohttp (all submodules), multidict, yarl, frozenlist, aiosignal, async_timeout, attrs, idna, charset_normalizer
- Removed duplicate SSL hidden import block; deduplication via `list(set(...))`

**Diagnostic Logging:**
- `server.py` TTS endpoint now logs: frozen status, SSL cert availability, per-track file sizes, audio durations, and peak amplitudes
- Uses `traceback.format_exc()` for visible error output in console

**Build:** .exe size reduced from 263 MB → 181 MB (leaner bundling)

### v2.1 (May 30, 2026) — TTS Robustness Fix + Per-Track Voice Selection

**TTS Robustness Fix:**
- Replaced `asyncio.run()` with `_run_async()`: spawns a dedicated non-daemon thread with its own event loop, avoiding event-loop conflicts when called from Flask's daemon threads inside pywebview
- Set `WindowsSelectorEventLoopPolicy` at module level for Windows compatibility
- Added explicit voice validation (`if not voice or not voice.strip()`)
- Better error messages: includes MP3 file size in failure messages, expanded connection-error detection keywords
- Added 60-second timeout to TTS async calls

**Per-Track Voice Selection:**
- `tts_engine.py`: `generate_all_tracks()` accepts `left_voice`, `right_voice`, `center_voice` parameters (fall back to default `voice` if not set)
- `server.py`: TTS endpoint accepts `left_voice`, `right_voice`, `center_voice` in JSON body
- `api.js`: `generateTTS()` passes per-track voice params
- `app.js`: Four voice selects (main default + one per track), "Same as default" option on per-track selects
- `index.html`: Added per-track voice `<select>` dropdowns in each affirmation text area
- `style.css`: Added `.track-voice-select` styling

**Build:** .exe size remains 263 MB

### v2.0 (May 30, 2026) — Massive GUI Upgrade

**Architecture:**
- Replaced CustomTkinter GUI with web-based UI (Flask + HTML/CSS/JS)
- Added pywebview for native desktop window wrapping
- Server/client architecture: Flask REST API backend, JavaScript frontend

**New Backend (`server.py` — 340 lines):**
- 8 REST endpoints: session CRUD, voices, TTS generation, mask upload, full generate, preview, waveform data, audio serving
- Session management with UUID keys and 24-hour auto-cleanup
- `gen_lock` mutex for thread-safe DSP pipeline
- PyInstaller frozen mode support via `sys._MEIPASS`
- Output routed to `~/Subliminal_Audio_Generator/output/` in bundled mode

**New Frontend:**
- `templates/index.html` — Semantic HTML5 with left panel (inputs/settings) + right panel (waveform editor)
- `static/css/style.css` — 755-line dark theme with CSS variables, glass morphism, gradient backgrounds, animated particles, custom form controls, toast notifications
- `static/js/api.js` — REST API client with error normalization
- `static/js/waveform.js` — Multi-track WaveSurfer.js v7 editor with Regions plugin (trim handles), per-track solo/mute/volume/speed, synced zoom/scroll/playback, timeline
- `static/js/app.js` — Main controller handling all user interactions, drag-drop mask upload, duration presets, keyboard shortcuts

**New Features:**
- Multi-track waveform editor (Left Ear, Right Ear, Center, Mask, Binaural)
- Per-track volume and speed controls
- Trim region editing on waveforms
- Preview generation (10-second clip) before full export
- Custom masking music upload (WAV, MP3, FLAC, OGG, M4A, AIFF)
- Auto-looping vocal tracks to target duration with tempo pre-compensation
- Duration presets (1/3/5/10/30/60 min)
- Drag-and-drop file upload
- Space bar keyboard shortcut for play/pause
- `--browser` and `--server` CLI flags for dev/debug modes

**DSP Additions (`audio_processor.py`):**
- `loop_vocals_to_duration()` — Loop vocal track to target duration
- `generate_preview()` — 10-second quick mix for auditioning
- `custom_mask_path` parameter on `generate_subliminal()` — Replaces brown noise with user-provided audio

**`main.py` Updates:**
- Rewritten for 3 launch modes: desktop (pywebview), browser (webbrowser), server-only (headless)
- Argument parser: `--browser`, `--server`, `--port`
- Graceful fallback to browser mode if pywebview not installed

**Dependencies:**
- Added: `flask>=3.0.0`, `flask-cors>=4.0.0`, `pywebview>=5.0.0`
- Removed: `customtkinter` (no longer used)

**Build:**
- Updated `.spec` file: bundles templates/, static/, output/; collects Flask/jinja2/pywebview; deduplication logic
- .exe size: 263 MB (was 260 MB)

**Obsoleted:**
- `gui.py` — The old CustomTkinter GUI is no longer loaded by `main.py`. Kept for reference.

### v1.1 (May 26, 2026) — TTS Bug Fix

- Fixed critical TTS bug: switched from `Communicate.stream()` (WebM/Opus) to `edge_tts.save()` (proper MP3) + ffmpeg subprocess for MP3→WAV conversion
- Added `ffmpeg.exe` (217 MB portable ffmpeg 8.1.1)
- Added `_find_ffmpeg()` with 3-tier search
- .exe size increased from 177 MB → 260 MB

### v1.0 (May 26, 2026) — Initial Release

- CustomTkinter GUI with 3 text areas, dual method checkboxes, vocal volume slider
- Edge TTS neural voices (10 English options)
- Full DSP pipeline: preprocessing, tempo compression, brown noise, DSB-AM, binaural beats, dichotic panning
- PyInstaller packaging into standalone .exe

---

## 13. Known Limitations & Future Improvements

### 13.1 Known Limitations

1. **TTS requires internet:** Edge TTS must reach Microsoft servers. No offline fallback. Some voices may be temporarily unavailable ("No audio was received").
2. **English only:** Edge TTS voices are English only (18 verified-valid voices as of v2.5).
3. **No waveform visualization:** WaveSurfer.js editor removed in v2.4 for simplicity. Custom audio player with seek bar provides navigation.
4. **Large .exe (180 MB):** ~165 MB is ffmpeg alone. Minimal ffmpeg build would reduce this significantly.
5. **No settings persistence:** Session resets on app restart. No save/load of settings.
6. **`gui.py` is dead code:** The old CustomTkinter GUI is obsoleted but not deleted.
7. **Flask dev server in production:** Uses Werkzeug's built-in server. For true production, should use Waitress.
8. **No offline Google Fonts fallback:** If CDN unreachable, fonts fall back to system defaults (still usable).
9. **Full audio preview takes as long as export:** Since preview generates full audio before clipping, the 10s sample takes roughly the same time as a full export.

### 13.2 Future Improvement Ideas

1. **Offline TTS fallback:** Integrate Windows SAPI or Piper TTS
2. **Multi-voice support:** Different TTS voices for left vs. right ear (implemented in v2.1)
3. **Settings persistence:** Save/load GUI settings to JSON config
4. **Batch processing:** Process multiple .txt files in sequence
5. **Additional mask types:** Pink noise, white noise, nature sounds
6. **LUFS normalization:** Replace peak normalization with proper loudness normalization
7. **Slimmer ffmpeg:** Build minimal ffmpeg (MP3 decode + WAV encode only) — could save ~200 MB
8. **Export format options:** FLAC, OGG support
9. **Session import/export:** Save and reload full session state
10. **Reintroduce waveform visualization:** Optional WaveSurfer.js editor as an advanced toggle
11. **Spectrogram view:** Toggle between waveform and spectrogram display

---

## 14. Scientific Reference

This application faithfully implements techniques described in:

**"The Science of Subliminal Programming: Optimal Audio Architecture for Subconscious Priming & Manifestation"**  
*(`Optimal_Subliminal_Audio_Creation_Guide.md` in the parent directory)*

### Techniques Implemented

| Guide Section | Implementation |
|---|---|
| Dichotic Listening & Hemispheric Specialization | Hard-left pan for "I AM", hard-right pan for "YOU ARE", 50ms offset |
| Time-Compressed Speech (1.35x) | Pitch-preserved phase vocoder via `librosa.effects.time_stretch` |
| Spectral Masking (Brown Noise) | Cumulative-sum integration + 20Hz HPF DC filter |
| The Subliminal Window (-20 to -35 dB) | User-controllable vocal attenuation (-40 to -10 dB, default -28 dB) |
| Silent Subliminal (Lowery Method, DSB-AM) | Bandpass 150–4000 Hz → 17,500 Hz carrier |
| Binaural Beats (Theta 6 Hz) | 100 Hz left + 106 Hz right, amplitude 0.15 |
| Multi-Perspective Syntax | Three text areas for I/YOU/Progressive phrasing |
| WAV 24-bit / 48 kHz Export | Lossless format preserves ultrasonic carriers and phase-locked signals |

### Key Scientific Principles

- **ACC bypass:** Progressive phrasing avoids triggering the anterior cingulate cortex
- **Instinctive Elaboration:** "Why" questions trigger automatic search-for-proof
- **Self-Distancing Theory:** Second-person phrasing replicates external validation
- **Contralateral auditory pathways:** Left ear → right hemisphere, Right ear → left hemisphere
- **Cochlear mechanics:** Ultrasonic vibrations processed by inner ear and temporal lobes
- **Neural entrainment:** Olivary nuclei sync EEG to binaural beat differences

---

## Appendix: Quick Reference Commands

```bash
# Install dependencies
cd "C:\Users\niala\OneDrive\Documents\nostress subliminal generator"
pip install -r requirements.txt

# Run the app
python main.py                    # Desktop (pywebview)
python main.py --browser          # Browser
python main.py --server --port 5000  # Headless server

# Run smoke tests (no internet needed)
python smoke_test.py

# Syntax check all Python files
python -c "import ast; files=['main.py','server.py','tts_engine.py','audio_processor.py','smoke_test.py']; [print(f+': OK') for f in files if not ast.parse(open(f,encoding='utf-8').read()) and True]; print('All OK')"

# Import test
python -c "from tts_engine import AVAILABLE_VOICES, generate_all_tracks; from audio_processor import generate_subliminal, generate_preview, loop_vocals_to_duration, generate_isochronic_tones, generate_solfeggio_tones, generate_schumann_resonance, generate_binaural_sweep, generate_isochronic_sweep, BRAINWAVE_PRESETS, SOLFEGGIO_FREQUENCIES, ENERGY_PRESETS; print('Imports OK')"

# Rebuild the .exe
cd "C:\Users\niala\OneDrive\Documents\nostress subliminal generator"
python -m PyInstaller Subliminal_Audio_Generator.spec --noconfirm

# Clean build artifacts
rm -rf build/ dist/
```

---

**End of Handover Document**

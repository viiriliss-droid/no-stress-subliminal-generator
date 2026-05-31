"""
Flask Backend Server - REST API for the Subliminal Audio Generator.

Serves the web-based GUI and exposes endpoints for:
- TTS generation (text → speech WAV)
- Custom masking audio upload
- Subliminal audio generation (full pipeline)
- Preview generation (short sample)
- Waveform peak data for visualization
- Audio file serving
"""

import os
import sys
import json
import uuid
import threading
import time
import subprocess
import shutil
import traceback
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Setup paths — handle both dev and PyInstaller bundled modes
def _get_base_dir():
    """Get the base directory, works in dev and PyInstaller bundled mode."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle — files are extracted to _MEIPASS
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_dir()
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Subliminal_Audio_Generator", "output")
SESSIONS_DIR = os.path.join(OUTPUT_DIR, "sessions")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Import project modules
from tts_engine import AVAILABLE_VOICES, DEFAULT_VOICE, generate_speech_sync, generate_all_tracks
from audio_processor import (
    SAMPLE_RATE, read_audio, get_duration,
    generate_subliminal, generate_preview,
    loop_vocals_to_duration,
    generate_binaural_beats, write_wav,
    BRAINWAVE_PRESETS, SOLFEGGIO_FREQUENCIES, ENERGY_PRESETS,
)

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
CORS(app)

# In-memory session store (keyed by session_id)
sessions = {}

# Thread lock for generation to prevent concurrent DSP runs
gen_lock = threading.Lock()


# =============================================================================
#  Utility Functions
# =============================================================================

def _get_session_dir(session_id: str) -> str:
    """Get or create a session directory for temporary files."""
    d = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(d, exist_ok=True)
    return d


def _cleanup_old_sessions(max_age_hours: float = 24.0):
    """Remove session directories older than max_age_hours."""
    try:
        now = time.time()
        for name in os.listdir(SESSIONS_DIR):
            path = os.path.join(SESSIONS_DIR, name)
            if os.path.isdir(path):
                age = now - os.path.getmtime(path)
                if age > max_age_hours * 3600:
                    shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _compute_waveform_peaks(audio_path: str, num_peaks: int = 2000) -> dict:
    """
    Compute waveform peak data for visualization.

    Returns a dict with 'peaks' (array of normalized values -1 to 1)
    and 'duration' (seconds), 'sample_rate'.
    """
    try:
        data, sr = sf.read(audio_path, dtype='float32')
        if data.ndim > 1:
            data = data.mean(axis=1)  # Mono for display

        duration = len(data) / sr
        n = len(data)
        peaks_per_bin = max(1, n // num_peaks)

        peaks = []
        for i in range(0, n, peaks_per_bin):
            chunk = data[i:i + peaks_per_bin]
            if len(chunk) > 0:
                peaks.append(max(float(np.max(chunk)), abs(float(np.min(chunk)))))
            if len(peaks) >= num_peaks:
                break

        # Normalize
        max_peak = max(peaks) if peaks and max(peaks) > 0 else 1.0
        peaks = [p / max_peak for p in peaks]

        return {
            "peaks": peaks,
            "duration": round(duration, 3),
            "sample_rate": sr,
        }
    except Exception as e:
        return {"error": str(e), "peaks": [], "duration": 0, "sample_rate": 48000}


# =============================================================================
#  Static File Serving
# =============================================================================

@app.route("/")
def index():
    """Serve the main UI."""
    return send_from_directory(TEMPLATES_DIR, "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files (CSS, JS)."""
    return send_from_directory(STATIC_DIR, filename)


@app.route("/api/audio/<session_id>/<filename>")
def serve_audio(session_id, filename):
    """Serve generated audio files from a session directory."""
    session_dir = _get_session_dir(session_id)
    return send_from_directory(session_dir, filename, mimetype="audio/wav")


@app.route("/api/download/<session_id>/<filename>")
def download_audio(session_id, filename):
    """Serve an audio file as a forced download (triggers native Save As dialog)."""
    session_dir = _get_session_dir(session_id)
    return send_from_directory(
        session_dir, filename,
        mimetype="audio/wav",
        as_attachment=True,
        download_name=filename,
    )


# =============================================================================
#  API: Session Management
# =============================================================================

@app.route("/api/session/create", methods=["POST"])
def create_session():
    """Create a new generation session."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = _get_session_dir(session_id)
    sessions[session_id] = {
        "id": session_id,
        "dir": session_dir,
        "status": "idle",
        "files": {},
        "created_at": time.time(),
    }
    _cleanup_old_sessions()
    return jsonify({"session_id": session_id})


# =============================================================================
#  API: Voice List
# =============================================================================

@app.route("/api/voices", methods=["GET"])
def get_voices():
    """Return available TTS voices."""
    return jsonify({"voices": AVAILABLE_VOICES, "default": DEFAULT_VOICE})


# =============================================================================
#  API: TTS Generation
# =============================================================================

@app.route("/api/tts/generate", methods=["POST"])
def generate_tts():
    """
    Generate speech WAV files from text.

    Expects JSON:
    {
        "session_id": "...",
        "left_text": "I am safe...",
        "right_text": "You are strong...",
        "center_text": "Why does this work...",
        "voice": "en-US-AriaNeural",
        "left_voice": "en-US-GuyNeural",     // optional per-track override
        "right_voice": "en-US-JennyNeural",  // optional per-track override
        "center_voice": "en-US-AriaNeural"   // optional per-track override
    }

    Returns:
    {
        "tracks": {"left": "vocal_left.wav", "right": "vocal_right.wav", "center": "vocal_center.wav"},
        "durations": {"left": 3.5, "right": 3.8, "center": 4.1}
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    session_dir = _get_session_dir(session_id)
    voice = data.get("voice", DEFAULT_VOICE)
    left_voice = data.get("left_voice") or voice
    right_voice = data.get("right_voice") or voice
    center_voice = data.get("center_voice") or voice
    left_text = data.get("left_text", "").strip()
    right_text = data.get("right_text", "").strip()
    center_text = data.get("center_text", "").strip()

    if not left_text and not right_text and not center_text:
        return jsonify({"error": "At least one text field must be non-empty"}), 400

    try:
        _frozen = getattr(sys, 'frozen', False)
        _ssl_ok = False
        try:
            import certifi
            cert_path = certifi.where()
            _ssl_ok = os.path.isfile(cert_path)
        except ImportError:
            cert_path = 'certifi not installed'

        print(f"[TTS] Generating tracks | frozen={_frozen} | ssl_cert={cert_path} | ssl_ok={_ssl_ok}", flush=True)
        print(f"[TTS] Voices: L={left_voice} R={right_voice} C={center_voice}", flush=True)
        print(f"[TTS] Text lengths: L={len(left_text)} R={len(right_text)} C={len(center_text)}", flush=True)

        tracks = generate_all_tracks(
            left_text, right_text, center_text,
            session_dir,
            voice=voice,
            left_voice=left_voice,
            right_voice=right_voice,
            center_voice=center_voice,
        )

        # Verify generated files have actual audio content
        for key, path in tracks.items():
            if os.path.isfile(path):
                size_kb = os.path.getsize(path) / 1024
                try:
                    import soundfile as _sf
                    data = _sf.read(path, dtype='float32')[0]
                    peak = float(np.max(np.abs(data))) if len(data) > 0 else 0
                    dur = len(data) / SAMPLE_RATE
                    print(f"[TTS] {key}: {size_kb:.1f}KB | {dur:.1f}s | peak={peak:.4f}", flush=True)
                except Exception:
                    print(f"[TTS] {key}: {size_kb:.1f}KB (unable to read)", flush=True)
            else:
                print(f"[TTS] {key}: FILE NOT CREATED", flush=True)

    except ConnectionError as e:
        print(f"[TTS] CONNECTION ERROR: {e}", flush=True)
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        print(f"[TTS] FAILED: {type(e).__name__}: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

    durations = {}
    for key, path in tracks.items():
        try:
            durations[key] = round(get_duration(read_audio(path)), 3)
        except Exception:
            durations[key] = 0

    # Generate a binaural beat WAV for visualization in the editor
    max_dur = max(durations.values()) if durations else 3.0
    binaural_samples = int(max_dur * SAMPLE_RATE)
    binaural_stereo = generate_binaural_beats(binaural_samples, SAMPLE_RATE, 100, 106, 0.15)
    binaural_path = os.path.join(session_dir, "binaural_beats.wav")
    write_wav(binaural_path, binaural_stereo.T, SAMPLE_RATE)

    return jsonify({
        "tracks": {**{k: os.path.basename(v) for k, v in tracks.items()}, "binaural": "binaural_beats.wav"},
        "durations": {**durations, "binaural": round(max_dur, 3)},
    })


# =============================================================================
#  API: Custom Mask Upload
# =============================================================================

@app.route("/api/mask/upload", methods=["POST"])
def upload_mask():
    """
    Upload a custom masking audio file.

    Expects multipart form data with 'file' field and 'session_id'.

    Returns:
    {
        "filename": "custom_mask.wav",
        "duration": 60.0,
        "waveform": { "peaks": [...], "duration": 60.0, "sample_rate": 48000 }
    }
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    session_id = request.form.get("session_id", "")

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    session_dir = _get_session_dir(session_id)

    # Save the uploaded file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff"):
        ext = ".wav"

    safe_name = f"custom_mask{ext}"
    mask_path = os.path.join(session_dir, safe_name)
    file.save(mask_path)

    # Convert to 48kHz mono WAV if needed using audio_processor
    try:
        audio = read_audio(mask_path)
        # Save as proper WAV
        converted_path = os.path.join(session_dir, "custom_mask.wav")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        sf.write(converted_path, audio, SAMPLE_RATE)
        duration = round(get_duration(audio), 3)

        # Clean up original if different format
        if mask_path != converted_path:
            try:
                os.remove(mask_path)
            except OSError:
                pass
    except Exception as e:
        return jsonify({"error": f"Failed to process uploaded audio: {str(e)}"}), 400

    # Compute waveform data
    waveform = _compute_waveform_peaks(converted_path)

    return jsonify({
        "filename": "custom_mask.wav",
        "duration": duration,
        "waveform": waveform,
    })


# =============================================================================
#  API: Progress Polling
# =============================================================================

@app.route("/api/progress/<session_id>", methods=["GET"])
def get_progress(session_id):
    """Poll for real-time generation progress (used by frontend progress bar)."""
    session = sessions.get(session_id)
    if not session:
        return jsonify({"percent": 0, "message": "No active session", "done": True})
    prog = session.get("progress", {"percent": 0, "message": "Idle", "done": False})
    return jsonify({
        "percent": prog.get("percent", 0),
        "message": prog.get("message", ""),
        "done": prog.get("done", False),
    })


# =============================================================================
#  API: Generate Subliminal Audio
# =============================================================================

@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Run the full subliminal audio generation pipeline.

    Expects JSON:
    {
        "session_id": "...",
        "method": "masked" | "silent" | "both",
        "speed_factor": 1.35,
        "vocal_volume_db": -28.0,
        "include_binaural": true,
        "use_custom_mask": false,
        "target_duration": 300.0,
        "output_filename": "my_subliminal",
        "energy_layers": { ... }  // optional energy layer config
    }

    Returns:
    {
        "output_file": "my_subliminal.wav",
        "output_path": "/full/path/to/my_subliminal.wav",
        "duration": 120.5,
        "waveform": { ... }
    }
    """
    with gen_lock:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        session_dir = _get_session_dir(session_id)
        method = data.get("method", "masked")
        speed_factor = float(data.get("speed_factor", 1.35))
        vocal_volume_db = float(data.get("vocal_volume_db", -28.0))
        include_binaural = data.get("include_binaural", True)
        use_custom_mask = data.get("use_custom_mask", False)
        target_duration = data.get("target_duration", None)
        output_filename = data.get("output_filename", "my_subliminal")
        energy_layers = data.get("energy_layers", None)

        # Sanitize filename
        output_filename = "".join(c for c in output_filename if c.isalnum() or c in " _-").strip()
        if not output_filename:
            output_filename = "my_subliminal"

        # Init progress state
        sessions[session_id]["progress"] = {"percent": 0, "message": "Starting...", "done": False}

        def _update_progress(msg, pct):
            sessions[session_id]["progress"] = {"percent": round(pct), "message": msg, "done": False}

        # Find vocal tracks
        vocal_left_path = os.path.join(session_dir, "vocal_left.wav")
        vocal_right_path = os.path.join(session_dir, "vocal_right.wav")
        vocal_center_path = os.path.join(session_dir, "vocal_center.wav")

        missing = []
        for p, label in [(vocal_left_path, "left"), (vocal_right_path, "right"), (vocal_center_path, "center")]:
            if not os.path.isfile(p):
                missing.append(label)

        # Create silent tracks for missing ones
        for label in missing:
            silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
            path = os.path.join(session_dir, f"vocal_{label}.wav")
            sf.write(path, silence, SAMPLE_RATE)

        # Determine target duration and handle looping
        if use_custom_mask:
            mask_path = os.path.join(session_dir, "custom_mask.wav")
            if not os.path.isfile(mask_path):
                return jsonify({"error": "Custom mask not found. Please upload a mask first."}), 400
            mask_duration = get_duration(read_audio(mask_path))
            target_duration = mask_duration
        elif target_duration is not None and target_duration > 0:
            target_duration = float(target_duration)
        else:
            # Use longest vocal track as duration
            durations = []
            for p in [vocal_left_path, vocal_right_path, vocal_center_path]:
                if os.path.isfile(p):
                    durations.append(get_duration(read_audio(p)))
            target_duration = max(durations) if durations else 60.0

        # Loop vocal tracks to match target duration
        looped_dir = os.path.join(session_dir, "looped")
        os.makedirs(looped_dir, exist_ok=True)

        vocal_left_looped = os.path.join(looped_dir, "vocal_left_looped.wav")
        vocal_right_looped = os.path.join(looped_dir, "vocal_right_looped.wav")
        vocal_center_looped = os.path.join(looped_dir, "vocal_center_looped.wav")

        _update_progress("Reading vocal tracks...", 1)
        left_audio = read_audio(vocal_left_path)
        right_audio = read_audio(vocal_right_path)
        center_audio = read_audio(vocal_center_path)

        # Pre-compensate: loop to target * speed_factor so after compression it fills target
        _update_progress("Looping vocals to target duration...", 3)
        loop_target = target_duration * speed_factor
        loop_vocals_to_duration(left_audio, loop_target, vocal_left_looped)
        loop_vocals_to_duration(right_audio, loop_target, vocal_right_looped)
        loop_vocals_to_duration(center_audio, loop_target, vocal_center_looped)

        # Determine output path
        output_path = os.path.join(session_dir, f"{output_filename}.wav")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(session_dir, f"{output_filename}_{counter}.wav")
            counter += 1

        # Run the DSP pipeline with real progress
        try:
            generate_subliminal(
                vocal_left_looped, vocal_right_looped, vocal_center_looped,
                output_path,
                method=method,
                speed_factor=speed_factor,
                include_binaural=include_binaural,
                vocal_attenuation_db=vocal_volume_db,
                custom_mask_path=os.path.join(session_dir, "custom_mask.wav") if use_custom_mask else None,
                energy_layers=energy_layers,
                progress_callback=_update_progress,
            )
        except Exception as e:
            _update_progress("DSP pipeline failed", 0)
            sessions[session_id]["progress"]["done"] = True
            return jsonify({"error": f"DSP pipeline failed: {str(e)}"}), 500

        _update_progress("Writing output file...", 97)
        duration = get_duration(read_audio(output_path))
        waveform = _compute_waveform_peaks(output_path)

        _update_progress("Complete!", 100)
        sessions[session_id]["progress"]["done"] = True
        sessions[session_id]["status"] = "generated"
        sessions[session_id]["files"]["output"] = os.path.basename(output_path)

        return jsonify({
            "output_file": os.path.basename(output_path),
            "output_path": output_path,
            "duration": round(duration, 3),
            "waveform": waveform,
        })


# =============================================================================
#  API: Generate Preview
# =============================================================================

@app.route("/api/preview", methods=["POST"])
def preview():
    """
    Generate a preview of the subliminal audio.

    Generates the FULL audio first (ensures affirmations loop correctly,
    volume/voice changes actually take effect), then clips to the requested
    preview_duration. Real progress is reported via the progress polling endpoint.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    session_dir = _get_session_dir(session_id)
    method = data.get("method", "masked")
    speed_factor = float(data.get("speed_factor", 1.35))
    vocal_volume_db = float(data.get("vocal_volume_db", -28.0))
    include_binaural = data.get("include_binaural", True)
    use_custom_mask = data.get("use_custom_mask", False)
    target_duration = data.get("target_duration", None)
    preview_clip_duration = float(data.get("preview_duration", 10.0))
    energy_layers = data.get("energy_layers", None)

    t_start = time.time()

    # Init progress state
    sessions[session_id]["progress"] = {"percent": 0, "message": "Starting preview...", "done": False}

    def _update_progress(msg, pct):
        sessions[session_id]["progress"] = {"percent": round(pct), "message": msg, "done": False}

    # Find vocal tracks (ensure they exist)
    vocal_left_path = os.path.join(session_dir, "vocal_left.wav")
    vocal_right_path = os.path.join(session_dir, "vocal_right.wav")
    vocal_center_path = os.path.join(session_dir, "vocal_center.wav")

    for label, path in [("left", vocal_left_path), ("right", vocal_right_path), ("center", vocal_center_path)]:
        if not os.path.isfile(path):
            silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
            sf.write(path, silence, SAMPLE_RATE)

    custom_mask_path = None
    if use_custom_mask:
        custom_mask_path = os.path.join(session_dir, "custom_mask.wav")
        if not os.path.isfile(custom_mask_path):
            return jsonify({"error": "Custom mask not found"}), 400

    # Determine effective total duration
    if use_custom_mask:
        effective_duration = get_duration(read_audio(custom_mask_path))
    elif target_duration is not None and target_duration > 0:
        effective_duration = float(target_duration)
    else:
        durations = []
        for p in [vocal_left_path, vocal_right_path, vocal_center_path]:
            if os.path.isfile(p):
                try:
                    durations.append(get_duration(read_audio(p)))
                except Exception:
                    pass
        effective_duration = max(durations) if durations else 60.0

    full_path = os.path.join(session_dir, "preview_full.wav")
    preview_path = os.path.join(session_dir, "preview.wav")

    try:
        # Loop vocals to full duration first
        _update_progress("Looping vocals...", 5)
        left_audio = loop_vocals_to_duration(read_audio(vocal_left_path), effective_duration * speed_factor)
        right_audio = loop_vocals_to_duration(read_audio(vocal_right_path), effective_duration * speed_factor)
        center_audio = loop_vocals_to_duration(read_audio(vocal_center_path), effective_duration * speed_factor)

        looped_dir = os.path.join(session_dir, "looped")
        os.makedirs(looped_dir, exist_ok=True)
        left_looped = os.path.join(looped_dir, "vocal_left_preview.wav")
        right_looped = os.path.join(looped_dir, "vocal_right_preview.wav")
        center_looped = os.path.join(looped_dir, "vocal_center_preview.wav")
        sf.write(left_looped, left_audio, SAMPLE_RATE)
        sf.write(right_looped, right_audio, SAMPLE_RATE)
        sf.write(center_looped, center_audio, SAMPLE_RATE)

        # Generate full subliminal with real progress
        _update_progress("Generating full audio...", 10)
        generate_subliminal(
            left_looped, right_looped, center_looped,
            full_path,
            method=method,
            speed_factor=speed_factor,
            include_binaural=include_binaural,
            vocal_attenuation_db=vocal_volume_db,
            custom_mask_path=custom_mask_path,
            energy_layers=energy_layers,
            progress_callback=_update_progress,
        )

        # Clip the first N seconds
        _update_progress("Clipping preview...", 92)
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        clip_cmd = [
            ffmpeg, "-i", full_path,
            "-t", str(preview_clip_duration),
            "-acodec", "pcm_s24le",
            "-ar", str(SAMPLE_RATE),
            "-ac", "2",
            "-y", preview_path,
        ]
        clip_result = subprocess.run(clip_cmd, capture_output=True, timeout=30)

        if clip_result.returncode != 0 or not os.path.isfile(preview_path):
            shutil.copy(full_path, preview_path)

        # Clean up full temp file and looped preview intermediates
        try:
            os.remove(full_path)
        except OSError:
            pass
        try:
            for f in [left_looped, right_looped, center_looped]:
                if os.path.isfile(f):
                    os.remove(f)
        except OSError:
            pass

        _update_progress("Complete!", 100)

    except Exception as e:
        _update_progress("Preview failed", 0)
        sessions[session_id]["progress"]["done"] = True
        return jsonify({"error": f"Preview generation failed: {str(e)}"}), 500

    sessions[session_id]["progress"]["done"] = True
    duration = get_duration(read_audio(preview_path))
    gen_time = round(time.time() - t_start, 2)

    return jsonify({
        "preview_file": "preview.wav",
        "duration": round(duration, 3),
        "full_duration": round(effective_duration, 1),
        "gen_time_seconds": gen_time,
    })


# =============================================================================
#  API: Energy Layer Presets
# =============================================================================

@app.route("/api/energy/presets", methods=["GET"])
def get_energy_presets():
    """Return available brainwave entrainment presets, Solfeggio frequencies, and energy presets."""
    return jsonify({
        "brainwave_presets": BRAINWAVE_PRESETS,
        "solfeggio_frequencies": [
            {"hz": hz, "label": label}
            for hz, label in SOLFEGGIO_FREQUENCIES.items()
        ],
        "schumann_hz": 7.83,
        "energy_presets": ENERGY_PRESETS,
    })


# =============================================================================
#  API: Waveform Data
# =============================================================================

@app.route("/api/waveform/<session_id>/<filename>", methods=["GET"])
def get_waveform(session_id, filename):
    """Get waveform peak data for an audio file."""
    session_dir = _get_session_dir(session_id)
    filepath = os.path.join(session_dir, filename)
    if not os.path.isfile(filepath):
        # Also check looped dir and output dir
        for subdir in ["looped", ""]:
            alt = os.path.join(session_dir, subdir, filename)
            if os.path.isfile(alt):
                filepath = alt
                break
        else:
            return jsonify({"error": "File not found"}), 404

    waveform = _compute_waveform_peaks(filepath)
    return jsonify(waveform)


# =============================================================================
#  Main
# =============================================================================

def run_server(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Run the Flask development server."""
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    run_server()

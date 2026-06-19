"""
TTS Engine - Microsoft Edge Neural Text-to-Speech (free, high quality).

Generates speech using Microsoft Edge's free TTS API. Uses a two-tier approach:
  1. PRIMARY: In-process async API — works when SSL certs are properly set up.
  2. FALLBACK: Subprocess-based — spawns a system Python process to run edge_tts.
     This is used when the async API fails (e.g. missing certs, threading issues).

Both methods produce an MP3 which is then converted to 48kHz 24-bit mono WAV
via ffmpeg. Audio silence detection verifies the output has real content.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import threading
import numpy as np
import soundfile as sf

# ---------------------------------------------------------------------------
# SSL Certificate Fix for PyInstaller-frozen environments
# ---------------------------------------------------------------------------
# When packaged with PyInstaller, certifi.where() may return a path in a
# non-existent site-packages directory. We check sys._MEIPASS for the
# bundled copy of cacert.pem first, then fall back to certifi.where().
def _ensure_ssl_certs():
    """Ensure SSL certificates are available, even in PyInstaller bundles.

    Uses multiple strategies:
    1. Find cacert.pem (frozen bundle or certifi.where())
    2. Set env vars (SSL_CERT_FILE, REQUESTS_CA_BUNDLE)
    3. Monkey-patch ssl.create_default_context to inject certifi's CA bundle
       (this is the most reliable method for aiohttp-based edge_tts)
    """
    try:
        import ssl
        import certifi
        cert_path = None

        # In PyInstaller frozen mode, certifi.where() may point to a
        # non-existent site-packages path. The .spec bundles cacert.pem
        # into <MEIPASS>/certifi/ — check there first.
        if getattr(sys, 'frozen', False):
            meipass = sys._MEIPASS
            for candidate in [
                os.path.join(meipass, 'certifi', 'cacert.pem'),
                os.path.join(meipass, 'certifi', 'certifi', 'cacert.pem'),
            ]:
                if os.path.isfile(candidate):
                    cert_path = candidate
                    break

        # Fall back to certifi's own resolution (works in dev mode)
        if not cert_path or not os.path.isfile(cert_path):
            try:
                cert_path = certifi.where()
            except Exception:
                pass

        if cert_path and os.path.isfile(cert_path):
            # Strategy 1: Env vars (works for requests, partial for aiohttp)
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            os.environ.setdefault('AIOHTTP_NO_EXTENSIONS', '1')

            # Strategy 2: Monkey-patch ssl.create_default_context to always
            # inject certifi's CA bundle. This is the most reliable fix for
            # aiohttp (used by edge_tts), which creates its own SSL contexts.
            _orig_create_default_context = ssl.create_default_context
            def _patched_create_default_context(*args, **kwargs):
                if 'cafile' not in kwargs and 'cadata' not in kwargs and 'capath' not in kwargs:
                    kwargs['cafile'] = cert_path
                return _orig_create_default_context(*args, **kwargs)
            ssl.create_default_context = _patched_create_default_context

            print(f"[tts_engine] SSL cert: {cert_path} (exists={os.path.isfile(cert_path)}, monkey-patched ssl)", flush=True)
            return True
        else:
            print(f"[tts_engine] SSL cert NOT FOUND (tried frozen paths + certifi.where())", flush=True)
    except ImportError:
        print("[tts_engine] certifi not installed — SSL may fail", flush=True)
    except Exception as e:
        print(f"[tts_engine] SSL setup error: {e}", flush=True)
    return False

_has_ssl_certs = _ensure_ssl_certs()

# Fix asyncio on Windows when running from daemon threads (e.g. Flask inside pywebview).
# The default ProactorEventLoop can fail in daemon-thread contexts.
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass  # Best-effort; Proactor might still work in newer Python versions


# Available Edge neural voices (English only, verified against Azure Voice Gallery 2025)
AVAILABLE_VOICES = {
    "Aria (US Female - Warm)": "en-US-AriaNeural",
    "Jenny (US Female - Friendly)": "en-US-JennyNeural",
    "Guy (US Male - Confident)": "en-US-GuyNeural",
    "Ana (US Female - Clear)": "en-US-AnaNeural",
    "Christopher (US Male - Natural)": "en-US-ChristopherNeural",
    "Eric (US Male - Warm)": "en-US-EricNeural",
    "Emma (US Female - Pleasant)": "en-US-EmmaNeural",
    "Nancy (US Female - Gentle)": "en-US-NancyNeural",
    "Steffan (US Male - Steady)": "en-US-SteffanNeural",
    "Tony (US Male - Strong)": "en-US-TonyNeural",
    "Brian (US Male - Deep)": "en-US-BrianNeural",
    "Sara (US Female - Soft)": "en-US-SaraNeural",
    "Andrew (US Male - Warm)": "en-US-AndrewNeural",
    "Sonia (UK Female - Warm)": "en-GB-SoniaNeural",
    "Ryan (UK Male - Friendly)": "en-GB-RyanNeural",
    "Libby (UK Female - Gentle)": "en-GB-LibbyNeural",
    "Maisie (UK Female - Bright)": "en-GB-MaisieNeural",
    "Thomas (UK Male - Deep)": "en-GB-ThomasNeural",
}

DEFAULT_VOICE = "en-US-AriaNeural"
TARGET_SAMPLE_RATE = 48000


def _mp3_to_wav(mp3_path: str, wav_path: str) -> str:
    """
    Convert MP3 to 48kHz 24-bit mono WAV using pure-Python audio libs.

    Uses soundfile (libsndfile >= 1.1.0 decodes MP3 natively) for decode
    and write, and librosa for resampling. This avoids any dependency on
    an external ffmpeg.exe being present on the machine or bundled with
    the PyInstaller build, so the app works when shipped as a bare .exe.

    Args:
        mp3_path: Path to the input MP3 file.
        wav_path: Path for the output WAV file.

    Returns:
        The wav_path on success.

    Raises:
        RuntimeError: If decode/resample/write fails or output is empty.
    """
    try:
        # librosa is heavy to import; load it lazily so module import stays fast.
        import librosa

        # Decode the MP3 via libsndfile (native MP3 support in >= 1.1.0).
        data, sr = sf.read(mp3_path, dtype='float32', always_2d=False)

        # Flatten to mono (Edge TTS is already mono, but be defensive).
        if data.ndim > 1:
            data = data.mean(axis=1)

        if len(data) == 0:
            raise RuntimeError("MP3 decoded to an empty audio buffer")

        # Resample to the target sample rate if needed.
        if sr != TARGET_SAMPLE_RATE:
            data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)

        # Write 48kHz / 24-bit / mono WAV. Float32 in [-1, 1] maps cleanly.
        sf.write(wav_path, data, TARGET_SAMPLE_RATE, subtype='PCM_24')

    except (RuntimeError, sf.LibsndfileError, OSError, ValueError) as e:
        raise RuntimeError(f"MP3→WAV conversion failed: {e}") from e

    # Verify the output is a valid, non-empty WAV.
    try:
        verify, _ = sf.read(wav_path)
        if len(verify) == 0:
            raise RuntimeError("produced an empty WAV file")
    except (RuntimeError, sf.LibsndfileError, OSError) as e:
        raise RuntimeError(f"WAV output validation failed: {e}")

    return wav_path


# ---------------------------------------------------------------------------
#  FALLBACK: Subprocess-based TTS (sidesteps asyncio/SSL issues)
# ---------------------------------------------------------------------------

def _find_system_python():
    """
    Find a real Python interpreter.

    In dev mode, sys.executable IS the Python interpreter.
    In PyInstaller frozen mode, sys.executable is the .exe itself (which has
    its own argparse and doesn't support -c). We must find a system Python.

    Returns:
        Path to a Python interpreter, or None if none found.
    """
    if not getattr(sys, 'frozen', False):
        return sys.executable  # Dev mode: sys.executable IS python

    # Frozen mode: look for a system Python installation
    exe_path = os.path.normpath(sys.executable).lower()
    for name in ['python', 'python3', 'py']:
        found = shutil.which(name)
        if found:
            found_norm = os.path.normpath(found).lower()
            if found_norm != exe_path:
                # Verify it's actually a different executable
                return found

    # Also check common Windows Python install locations
    if sys.platform == 'win32':
        for base in [
            os.path.expandvars(r'%LOCALAPPDATA%\Programs\Python'),
            os.path.expandvars(r'%PROGRAMFILES%\Python'),
            r'C:\Python',
        ]:
            if os.path.isdir(base):
                for entry in sorted(os.listdir(base), reverse=True):
                    candidate = os.path.join(base, entry, 'python.exe')
                    if os.path.isfile(candidate):
                        return candidate

    return None


def _generate_mp3_cli(text: str, voice: str, mp3_path: str, timeout: int = 60) -> str:
    """
    Generate MP3 using the `edge-tts` CLI command via subprocess.

    This is the preferred fallback — it avoids all Python asyncio/SSL/import
    issues by using the standalone CLI tool that comes with the edge_tts pip
    package.

    Args:
        text: The text to convert to speech.
        voice: The Edge TTS voice short name.
        mp3_path: Path for the output MP3 file.
        timeout: Maximum time in seconds.

    Returns:
        The mp3_path on success.

    Raises:
        RuntimeError: If the CLI fails or isn't found.
        TimeoutError: If the subprocess times out.
    """
    # On Windows, the CLI is edge-tts.exe (shim installed by pip)
    cli_name = 'edge-tts.exe' if sys.platform == 'win32' else 'edge-tts'
    cli_path = shutil.which(cli_name)

    if not cli_path:
        # Also try with python -m edge_tts (works in some setups)
        python_exe = _find_system_python()
        if python_exe:
            cmd = [python_exe, '-m', 'edge_tts', '--text', text, '--voice', voice, '--write-media', mp3_path]
        else:
            raise RuntimeError(
                "edge-tts CLI not found on PATH. "
                "Install it with: pip install edge-tts"
            )
    else:
        cmd = [cli_path, '--text', text, '--voice', voice, '--write-media', mp3_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"edge-tts CLI timed out after {timeout}s."
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()[:800] if result.stderr else "(no output)"
        raise RuntimeError(
            f"edge-tts CLI failed (exit {result.returncode}): {stderr}"
        )

    if not os.path.isfile(mp3_path):
        raise RuntimeError(
            "edge-tts CLI completed but produced no output file."
        )

    mp3_size = os.path.getsize(mp3_path)
    if mp3_size < 200:
        raise RuntimeError(
            f"edge-tts produced a near-empty MP3 ({mp3_size} bytes). "
            f"Voice '{voice}' may be unavailable, or the text may be too short."
        )

    return mp3_path


def _generate_mp3_subprocess(text: str, voice: str, mp3_path: str, timeout: int = 60) -> str:
    """
    Generate MP3 via edge_tts Python API in a clean subprocess.

    This is a LAST-RESORT fallback. It runs edge_tts in a separate Python
    process with proper SSL config. Only tried if the CLI fallback fails.

    NOTE: Requires a system Python installation with edge_tts installed.
    """
    python_exe = _find_system_python()
    if python_exe is None:
        raise RuntimeError(
            "No system Python interpreter found. "
            "The subprocess TTS fallback requires a system Python installation "
            "with edge_tts installed (pip install edge-tts)."
        )

    # Check if edge_tts is importable in the system Python before trying
    check_cmd = [python_exe, '-c', 'import edge_tts; print("ok")']
    check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=15)
    if check_result.returncode != 0:
        raise RuntimeError(
            f"System Python at '{python_exe}' does not have edge_tts installed.\n"
            f"Run: {python_exe} -m pip install edge_tts\n"
            f"(or install Python from python.org and then pip install edge_tts)"
        )

    # Inline script with proper SSL + error handling
    script = '''
import asyncio, json, os, sys, ssl
try:
    import certifi
    cf = certifi.where()
    os.environ["SSL_CERT_FILE"] = cf
    os.environ["REQUESTS_CA_BUNDLE"] = cf
    _orig = ssl.create_default_context
    def _patched(*a, **kw):
        if "cafile" not in kw and "cadata" not in kw and "capath" not in kw:
            kw["cafile"] = cf
        return _orig(*a, **kw)
    ssl.create_default_context = _patched
except Exception:
    pass

async def _go():
    import edge_tts
    args = json.loads(sys.argv[1])
    c = edge_tts.Communicate(args["text"], args["voice"])
    await c.save(args["output"])

try:
    asyncio.run(_go())
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
'''

    args_json = json.dumps({"text": text, "voice": voice, "output": mp3_path})

    try:
        result = subprocess.run(
            [python_exe, '-c', script, args_json],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"TTS subprocess timed out after {timeout}s."
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500] if result.stderr else "(no output)"
        raise RuntimeError(
            f"Edge TTS subprocess failed (exit {result.returncode}): {stderr}"
        )

    if not os.path.isfile(mp3_path):
        raise RuntimeError(
            "Edge TTS subprocess completed but produced no output file."
        )

    mp3_size = os.path.getsize(mp3_path)
    if mp3_size < 200:
        raise RuntimeError(
            f"Edge TTS produced a near-empty MP3 ({mp3_size} bytes)."
        )

    return mp3_path


# ---------------------------------------------------------------------------
#  PRIMARY: In-process async TTS (with SSL monkey-patching)
# ---------------------------------------------------------------------------

async def _generate_mp3_async(text: str, voice: str, output_path: str) -> str:
    """
    Generate speech using edge_tts Python API inline (fallback only).
    """
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def _run_async(coro, timeout_seconds: int = 60):
    """
    Run an async coroutine in a dedicated thread with its own event loop.
    """
    result_container = {"value": None, "error": None}

    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_container["value"] = loop.run_until_complete(coro)
        except Exception as exc:
            result_container["error"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=_target, daemon=False)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(f"TTS generation timed out after {timeout_seconds}s")

    if result_container["error"]:
        raise result_container["error"]

    return result_container["value"]


# ---------------------------------------------------------------------------
#  Audio silence detection
# ---------------------------------------------------------------------------

def _is_audio_silent(wav_path: str, threshold: float = 0.001) -> bool:
    """
    Check if a WAV file contains only silence (or near-silence).

    Args:
        wav_path: Path to the WAV file.
        threshold: Maximum absolute amplitude considered "silent".

    Returns:
        True if the audio is effectively silent.
    """
    try:
        data, _ = sf.read(wav_path, dtype='float32')
        if len(data) == 0:
            return True
        max_amplitude = float(np.max(np.abs(data)))
        return max_amplitude < threshold
    except Exception:
        return True  # Can't read = treat as silent


def generate_speech_sync(text: str, output_wav_path: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Generate speech from text and save as 48kHz 24-bit WAV.

    Uses a three-tier approach:
      1. PRIMARY: In-process async edge_tts API (with SSL monkey-patching)
      2. FALLBACK: edge-tts CLI via subprocess (most reliable cross-platform)
      3. LAST-RESORT: edge_tts Python API via subprocess (needs system Python)

    After generation, validates the audio to ensure it contains real speech.

    Args:
        text: The text to convert to speech.
        output_wav_path: Path to save the output WAV file.
        voice: The Edge TTS voice short name.

    Returns:
        The path to the generated WAV file.

    Raises:
        ValueError: If text or voice is invalid.
        ConnectionError: If Edge TTS cannot be reached.
        RuntimeError: If audio generation fails or produces silence.
    """
    if not text or not text.strip():
        raise ValueError("Text must not be empty")

    if not voice or not voice.strip():
        raise ValueError(f"Invalid voice name: '{voice}'")

    mp3_path = os.path.splitext(output_wav_path)[0] + ".mp3"
    errors = []

    def _clean_mp3():
        if os.path.isfile(mp3_path):
            try:
                os.remove(mp3_path)
            except OSError:
                pass

    # ---- TIER 1: In-process async (primary — monkey-patched SSL) ----
    try:
        print(f"[tts_engine] TIER 1: async TTS (voice={voice}, frozen={getattr(sys, 'frozen', False)})...", flush=True)
        _run_async(_generate_mp3_async(text, voice, mp3_path), timeout_seconds=60)
        if os.path.isfile(mp3_path) and os.path.getsize(mp3_path) >= 200:
            print(f"[tts_engine] TIER 1 SUCCESS: {os.path.getsize(mp3_path)} bytes", flush=True)
        else:
            raise RuntimeError("Async produced no valid MP3")
    except Exception as e:
        print(f"[tts_engine] TIER 1 failed: {type(e).__name__}", flush=True)
        errors.append(f"Async error: {e}")
        _clean_mp3()

        # Check for connection errors to fail fast
        msg = str(e).lower()
        if any(kw in msg for kw in ["connect", "resolve", "name or service", "network", "unreachable"]):
            raise ConnectionError(
                "Cannot reach Microsoft Edge TTS. Please check your internet connection."
            ) from e

        # ---- TIER 2: edge-tts CLI (most reliable fallback) ----
        try:
            print(f"[tts_engine] TIER 2: edge-tts CLI...", flush=True)
            _generate_mp3_cli(text, voice, mp3_path, timeout=60)
            print(f"[tts_engine] TIER 2 SUCCESS: {os.path.getsize(mp3_path)} bytes", flush=True)
        except Exception as e2:
            print(f"[tts_engine] TIER 2 failed: {type(e2).__name__}", flush=True)
            errors.append(f"CLI error: {e2}")
            _clean_mp3()

            msg2 = str(e2).lower()
            if any(kw in msg2 for kw in ["connect", "resolve", "name or service", "network", "unreachable"]):
                raise ConnectionError(
                    "Cannot reach Microsoft Edge TTS. Please check your internet connection."
                ) from e2

            # ---- TIER 3: Python subprocess (last resort) ----
            system_python = _find_system_python()
            if system_python:
                try:
                    print(f"[tts_engine] TIER 3: Python subprocess via {system_python}...", flush=True)
                    _generate_mp3_subprocess(text, voice, mp3_path, timeout=60)
                    print(f"[tts_engine] TIER 3 SUCCESS: {os.path.getsize(mp3_path)} bytes", flush=True)
                except Exception as e3:
                    print(f"[tts_engine] TIER 3 failed: {type(e3).__name__}", flush=True)
                    errors.append(f"Subprocess error: {e3}")
                    _clean_mp3()
                    raise RuntimeError(
                        f"TTS generation failed using all methods.\n"
                        + "\n".join(errors)
                        + f"\n\nTroubleshooting:\n"
                        f"  1. Ensure you have an internet connection\n"
                        f"  2. Try a different voice (e.g. en-US-JennyNeural)\n"
                        f"  3. Install edge-tts CLI: pip install edge-tts"
                    ) from e3
            else:
                raise RuntimeError(
                    f"TTS generation failed using both methods.\n"
                    + "\n".join(errors)
                    + f"\n\nNo system Python found for subprocess fallback.\n"
                    f"Install edge-tts CLI: pip install edge-tts"
                )

    # ---- Verify MP3 ----
    if not os.path.isfile(mp3_path):
        raise RuntimeError("TTS did not produce an output file.")

    mp3_size = os.path.getsize(mp3_path)
    if mp3_size < 200:
        _clean_mp3()
        raise RuntimeError(
            f"TTS produced a near-empty MP3 ({mp3_size} bytes). "
            f"Voice '{voice}' may be unavailable. Try a different voice."
        )

    # ---- Convert MP3 → WAV ----
    try:
        _mp3_to_wav(mp3_path, output_wav_path)
    finally:
        _clean_mp3()

    # ---- Validate: check for silent audio ----
    if _is_audio_silent(output_wav_path):
        raise RuntimeError(
            f"Generated audio is silent. Voice '{voice}' may be temporarily "
            f"unavailable. Try a different voice (e.g., 'en-US-JennyNeural')."
        )

    return output_wav_path


def generate_all_tracks(
    left_text: str,
    right_text: str,
    center_text: str,
    output_dir: str,
    voice: str = DEFAULT_VOICE,
    left_voice: str = None,
    right_voice: str = None,
    center_voice: str = None,
    progress_callback=None,
) -> dict:
    """
    Generate all three vocal tracks using TTS.

    Args:
        left_text: Affirmations for the Left ear (first-person "I AM").
        right_text: Affirmations for the Right ear (second-person "YOU ARE").
        center_text: Affirmations for the Center/Bridge (progressive/afformations).
        output_dir: Directory to save the generated WAV files.
        voice: The default Edge TTS voice short name (used if per-track voices not set).
        left_voice: Optional per-track voice for left ear (overrides 'voice').
        right_voice: Optional per-track voice for right ear (overrides 'voice').
        center_voice: Optional per-track voice for center (overrides 'voice').
        progress_callback: Optional callback(label, percent_0_to_100).

    Returns:
        Dictionary mapping track names to their WAV file paths.
    """
    tracks = {
        "left": os.path.join(output_dir, "vocal_left.wav"),
        "right": os.path.join(output_dir, "vocal_right.wav"),
        "center": os.path.join(output_dir, "vocal_center.wav"),
    }

    # Use per-track voice if provided, otherwise fall back to default voice
    voices = {
        "left": left_voice if left_voice else voice,
        "right": right_voice if right_voice else voice,
        "center": center_voice if center_voice else voice,
    }

    texts = [
        ("Left ear (I AM)", left_text, tracks["left"], voices["left"]),
        ("Right ear (YOU ARE)", right_text, tracks["right"], voices["right"]),
        ("Center (Bridge)", center_text, tracks["center"], voices["center"]),
    ]

    for i, (label, text, path, track_voice) in enumerate(texts):
        if progress_callback:
            progress_callback(f"Generating speech: {label} ({track_voice})...", (i / len(texts)) * 100)

        if text and text.strip():
            generate_speech_sync(text, path, track_voice)
        else:
            # If no text for this track, create a silent WAV of minimal length
            silence = np.zeros(TARGET_SAMPLE_RATE, dtype=np.float32)  # 1 second
            sf.write(path, silence, TARGET_SAMPLE_RATE)

    return tracks

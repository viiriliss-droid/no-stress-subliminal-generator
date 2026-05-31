# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# --- FFmpeg binary ---
binaries = [('ffmpeg.exe', '.')] if __import__('os').path.isfile('ffmpeg.exe') else []

# --- SSL Certificate bundle (critical for edge_tts HTTPS in frozen env) ---
try:
    import certifi
    cert_path = certifi.where()
    if __import__('os').path.isfile(cert_path):
        binaries.append((cert_path, 'certifi'))
        print(f"Bundling certifi certificates: {cert_path}")
except ImportError:
    print("WARNING: certifi not found — HTTPS may fail in frozen app")

# --- Flask templates & static files ---
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

# --- Collect all package data ---
hiddenimports = [
    'pkg_resources.py2_warn',
    'sklearn',
    'numba',
    # Flask ecosystem
    'flask', 'flask_cors', 'flask.json',
    'jinja2', 'jinja2.ext',
    'werkzeug', 'werkzeug.middleware',
    'markupsafe',
    'itsdangerous',
    'click',
    'blinker',
    # PyWebView
    'webview', 'webview.platforms',
    'webview.platforms.winforms',
    'webview.platforms.cocoa',
    'webview.platforms.gtk',
    'webview.js',
    'webview.guilib',
    # Additional Jinja2/Flask internals
    'flask.helpers',
    'flask.signals',
    'flask.sessions',
    'flask.templating',
    'flask.views',
    'flask.wrappers',
    'flask.blueprints',
    'flask.config',
    'flask.ctx',
    'flask.globals',
    'flask.logging',
    'flask.scaffold',
    'flask.testing',
    'flask.cli',
    # SSL / Networking dependencies for edge_tts
    'certifi', 'certifi.core',
    'aiohttp', 'aiohttp.client', 'aiohttp.client_ws',
    'aiohttp.connector', 'aiohttp.cookiejar', 'aiohttp.formdata',
    'aiohttp.hdrs', 'aiohttp.helpers', 'aiohttp.http',
    'aiohttp.multipart', 'aiohttp.payload', 'aiohttp.resolver',
    'aiohttp.streams', 'aiohttp.tracing', 'aiohttp.web',
    'aiohttp.web_request', 'aiohttp.web_response',
    'aiohttp.worker', 'aiohttp.wsgi',
    'multidict', 'multidict._multidict',
    'yarl', 'yarl._quoting',
    'frozenlist', 'frozenlist._frozenlist',
    'aiosignal',
    'async_timeout',
    'attrs',
]

# --- Collect all dependencies ---
for pkg in ['edge_tts', 'soundfile', 'librosa', 'scipy', 'flask', 'flask_cors', 'jinja2', 'certifi', 'aiohttp']:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# Deduplicate
datas = list(set(datas))
binaries = list(set(binaries))
hiddenimports = list(set(hiddenimports))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Subliminal_Audio_Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

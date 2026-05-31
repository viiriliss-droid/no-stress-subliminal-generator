"""
Subliminal Audio Generator - Main Entry Point

A free, offline(ish) tool that takes your affirmations and generates
scientifically-optimized subliminal audio following the principles of
dichotic listening, binaural beats, and psychoacoustic masking.

Launches as a modern web-based desktop application using Flask + pywebview,
or as a browser-based app when running in dev mode.

Usage:
    python main.py              # Desktop app (requires pywebview)
    python main.py --browser    # Opens in default web browser
    python main.py --server     # Flask server only (no GUI window)
"""

import sys
import os
import threading
import argparse
import webbrowser

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Subliminal Audio Generator")
    parser.add_argument("--browser", action="store_true", help="Open in browser instead of desktop window")
    parser.add_argument("--server", action="store_true", help="Run Flask server only (no window)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    args = parser.parse_args()

    from server import app, run_server

    host = "127.0.0.1"
    port = args.port
    url = f"http://{host}:{port}"

    # Start Flask in a background thread
    flask_thread = threading.Thread(
        target=run_server,
        args=(host, port),
        daemon=True,
    )
    flask_thread.start()

    if args.server:
        # Server-only mode: keep the main thread alive
        print(f"\n  Subliminal Audio Generator server running at: {url}\n")
        print("  Press Ctrl+C to stop.\n")
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")

    elif args.browser:
        # Browser mode: open in default web browser
        print(f"\n  Opening in browser: {url}\n")
        webbrowser.open(url)
        print("  Press Ctrl+C to stop.\n")
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")

    else:
        # Desktop mode: use pywebview
        try:
            import webview
        except ImportError:
            print("\n  pywebview is not installed. Install with: pip install pywebview")
            print("  Falling back to browser mode...\n")
            webbrowser.open(url)
            print(f"  Opening in browser: {url}")
            print("  Press Ctrl+C to stop.\n")
            try:
                flask_thread.join()
            except KeyboardInterrupt:
                print("\nShutting down...")
            return

        print(f"\n  Launching Subliminal Audio Generator...\n")

        # Create the desktop window
        window = webview.create_window(
            title="Subliminal Audio Generator",
            url=url,
            width=1280,
            height=860,
            min_size=(900, 600),
            resizable=True,
            fullscreen=False,
        )

        webview.start()


if __name__ == "__main__":
    main()

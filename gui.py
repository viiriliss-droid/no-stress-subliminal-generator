"""
GUI - Modern tkinter interface for the Subliminal Audio Generator.

Three text areas for the three ear-specific affirmation scripts,
plus settings for subliminal method, speed, binaural beats, voice,
vocal volume, and output filename.
"""

import os
import threading
import customtkinter as ctk
from tkinter import messagebox

from tts_engine import AVAILABLE_VOICES, DEFAULT_VOICE, generate_all_tracks
from audio_processor import generate_subliminal


# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constants
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
DEFAULT_SPEED = 1.35
DEFAULT_VOLUME_DB = -28.0  # Guide-recommended vocal attenuation for masked


class SubliminalGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Subliminal Audio Generator")
        self.geometry("900x920")
        self.minsize(750, 750)

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # State
        self.is_generating = False
        self.destroyed = False
        self.voice_map = AVAILABLE_VOICES
        self.voice_names = list(self.voice_map.keys())

        self._build_ui()

        # Handle window close during generation
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =========================================================================
    #  UI Construction
    # =========================================================================

    def _build_ui(self):
        """Construct all UI elements."""
        # --- Title ---
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 5))

        ctk.CTkLabel(
            title_frame,
            text="Subliminal Audio Generator",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Craft scientifically-optimized subliminal audio from your affirmations.",
            font=ctk.CTkFont(size=13),
            text_color="gray70",
        ).pack(anchor="w", pady=(2, 0))

        # --- Scrollable main area ---
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Input Section ---
        self._build_input_section(scroll_frame)

        # --- Settings Section ---
        self._build_settings_section(scroll_frame)

        # --- Filename Section ---
        self._build_filename_section(scroll_frame)

        # --- Generate Section ---
        self._build_generate_section(scroll_frame)

    def _build_input_section(self, parent):
        """Build the three text input areas for affirmations."""
        ctk.CTkLabel(
            parent,
            text="Affirmation Scripts",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            parent,
            text="Enter one affirmation per line. Each track is spoken separately and routed to the optimal ear.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        ).pack(anchor="w", pady=(0, 12))

        # Three text boxes side by side
        text_cols = ctk.CTkFrame(parent, fg_color="transparent")
        text_cols.pack(fill="x")

        text_cols.grid_columnconfigure(0, weight=1)
        text_cols.grid_columnconfigure(1, weight=1)
        text_cols.grid_columnconfigure(2, weight=1)

        self._make_text_area(
            text_cols, 0,
            title="LEFT EAR  (Right Hemisphere)",
            subtitle='First-person "I AM" statements',
        )

        self._make_text_area(
            text_cols, 1,
            title="RIGHT EAR  (Left Hemisphere)",
            subtitle='Second-person "YOU ARE" statements',
        )

        self._make_text_area(
            text_cols, 2,
            title="CENTER BRIDGE  (Both Ears)",
            subtitle="Progressive phrasing & Afformations",
        )

    def _make_text_area(self, parent, col, title, subtitle):
        """Create a labeled text area in the given grid column."""
        frame = ctk.CTkFrame(parent, fg_color="gray15")
        frame.grid(row=0, column=col, padx=4, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            frame,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).pack(anchor="w", padx=10, pady=(0, 8))

        textbox = ctk.CTkTextbox(frame, height=180, wrap="word", font=ctk.CTkFont(size=12))
        textbox.pack(fill="both", expand=True, padx=8, pady=(0, 0))
        textbox.insert("1.0", "")

        if col == 0:
            self.left_text = textbox
        elif col == 1:
            self.right_text = textbox
        else:
            self.center_text = textbox

    def _build_settings_section(self, parent):
        """Build the settings panel."""
        ctk.CTkLabel(
            parent,
            text="Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(20, 8))

        settings_frame = ctk.CTkFrame(parent, fg_color="gray15")
        settings_frame.pack(fill="x")

        # --- Row 1: Method checkboxes + Binaural toggle ---
        row1 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 6))

        # Method checkboxes (allow selecting both)
        method_frame = ctk.CTkFrame(row1, fg_color="transparent")
        method_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            method_frame,
            text="Subliminal Method",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")

        method_cb_frame = ctk.CTkFrame(method_frame, fg_color="transparent")
        method_cb_frame.pack(anchor="w", pady=(4, 0))

        self.masked_var = ctk.BooleanVar(value=True)
        self.silent_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            method_cb_frame,
            text="Classic Masked  (brown noise + whispers)",
            variable=self.masked_var,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 15))

        ctk.CTkCheckBox(
            method_cb_frame,
            text="Silent Ultrasonic  (17.5 kHz carrier)",
            variable=self.silent_var,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        # Binaural toggle
        binaural_frame = ctk.CTkFrame(row1, fg_color="transparent")
        binaural_frame.pack(side="right")

        self.binaural_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            binaural_frame,
            text="Include 6 Hz Theta Binaural Beats",
            variable=self.binaural_var,
            font=ctk.CTkFont(size=12),
        ).pack()

        # --- Row 2: Speed slider + Vocal volume slider ---
        row2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(6, 4))

        # Speed slider
        speed_frame = ctk.CTkFrame(row2, fg_color="transparent")
        speed_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        speed_label_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_label_frame.pack(fill="x")

        ctk.CTkLabel(
            speed_label_frame,
            text="Tempo Compression",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        self.speed_value_label = ctk.CTkLabel(
            speed_label_frame,
            text=f"{DEFAULT_SPEED:.2f}x",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4da6ff",
        )
        self.speed_value_label.pack(side="right")

        self.speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=1.0,
            to=2.0,
            number_of_steps=20,
            command=self._on_speed_change,
        )
        self.speed_slider.pack(fill="x", pady=(4, 0))
        self.speed_slider.set(DEFAULT_SPEED)

        ctk.CTkLabel(
            speed_frame,
            text="1.0x = natural  |  1.35x = recommended  |  2.0x = maximum",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        ).pack(anchor="w", pady=(2, 0))

        # Vocal volume slider
        volume_frame = ctk.CTkFrame(row2, fg_color="transparent")
        volume_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))

        vol_label_frame = ctk.CTkFrame(volume_frame, fg_color="transparent")
        vol_label_frame.pack(fill="x")

        ctk.CTkLabel(
            vol_label_frame,
            text="Vocal Volume (Masked)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        self.volume_value_label = ctk.CTkLabel(
            vol_label_frame,
            text=f"{DEFAULT_VOLUME_DB:.0f} dB",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4da6ff",
        )
        self.volume_value_label.pack(side="right")

        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=-40.0,
            to=-10.0,
            number_of_steps=30,
            command=self._on_volume_change,
        )
        self.volume_slider.pack(fill="x", pady=(4, 0))
        self.volume_slider.set(DEFAULT_VOLUME_DB)

        ctk.CTkLabel(
            volume_frame,
            text="-40 dB = faintest  |  -28 dB = recommended  |  -10 dB = loudest",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        ).pack(anchor="w", pady=(2, 0))

        # --- Row 3: Voice selector ---
        row3 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row3.pack(fill="x", padx=15, pady=(6, 12))

        voice_frame = ctk.CTkFrame(row3, fg_color="transparent")
        voice_frame.pack(side="left")

        ctk.CTkLabel(
            voice_frame,
            text="TTS Voice",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")

        self.voice_var = ctk.StringVar(value=self.voice_names[0])
        voice_menu = ctk.CTkOptionMenu(
            voice_frame,
            values=self.voice_names,
            variable=self.voice_var,
            font=ctk.CTkFont(size=12),
            width=220,
        )
        voice_menu.pack(pady=(4, 0))

    def _build_filename_section(self, parent):
        """Build the output filename entry."""
        ctk.CTkLabel(
            parent,
            text="Output File",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(20, 8))

        fn_frame = ctk.CTkFrame(parent, fg_color="gray15")
        fn_frame.pack(fill="x")

        fn_inner = ctk.CTkFrame(fn_frame, fg_color="transparent")
        fn_inner.pack(fill="x", padx=15, pady=(12, 12))

        ctk.CTkLabel(
            fn_inner,
            text="Filename:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self.filename_entry = ctk.CTkEntry(
            fn_inner,
            font=ctk.CTkFont(size=13),
            height=36,
        )
        self.filename_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.filename_entry.insert(0, "my_subliminal")

        ctk.CTkLabel(
            fn_inner,
            text=".wav",
            font=ctk.CTkFont(size=13),
            text_color="gray50",
        ).pack(side="left")

    def _build_generate_section(self, parent):
        """Build the generate button, progress bar, and status area."""
        gen_frame = ctk.CTkFrame(parent, fg_color="transparent")
        gen_frame.pack(fill="x", pady=(20, 10))

        self.generate_btn = ctk.CTkButton(
            gen_frame,
            text="GENERATE SUBLIMINAL AUDIO",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self._on_generate,
        )
        self.generate_btn.pack(fill="x")

        self.progress_bar = ctk.CTkProgressBar(gen_frame)
        self.progress_bar.pack(fill="x", pady=(10, 8))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            gen_frame,
            text="Ready. Fill in your affirmations and click Generate.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self.status_label.pack(anchor="w")

        # Safety notice
        safety_frame = ctk.CTkFrame(parent, fg_color="#1a1a2e", border_color="#333355")
        safety_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            safety_frame,
            text="SAFETY: Use stereo headphones. Do not max your volume. "
                 "Never listen while driving or operating machinery.",
            font=ctk.CTkFont(size=11),
            text_color="#ffaa33",
            wraplength=800,
        ).pack(padx=12, pady=8)

    # =========================================================================
    #  Callbacks
    # =========================================================================

    def _on_speed_change(self, value):
        self.speed_value_label.configure(text=f"{value:.2f}x")

    def _on_volume_change(self, value):
        self.volume_value_label.configure(text=f"{value:.0f} dB")

    def _on_close(self):
        """Handle window close - clean shutdown even during generation."""
        self.destroyed = True
        self.destroy()

    def _set_status(self, message: str, percent: float = None):
        """Thread-safe status update."""
        if not self.destroyed:
            try:
                self.after(0, lambda: self._update_status_ui(message, percent))
            except Exception:
                pass

    def _update_status_ui(self, message: str, percent: float = None):
        """Update status label and progress bar on main thread."""
        if self.destroyed:
            return
        try:
            self.status_label.configure(text=message)
            if percent is not None:
                self.progress_bar.set(percent / 100.0)
        except Exception:
            pass

    def _on_generate(self):
        """Handle the Generate button click."""
        if self.is_generating:
            return

        # Get text content
        left_text = self.left_text.get("1.0", "end-1c").strip()
        right_text = self.right_text.get("1.0", "end-1c").strip()
        center_text = self.center_text.get("1.0", "end-1c").strip()

        # Validation
        if not left_text and not right_text and not center_text:
            messagebox.showwarning(
                "No Text",
                "Please enter affirmations in at least one of the text areas."
            )
            return

        # Warn if left ear is empty
        if not left_text and (right_text or center_text):
            result = messagebox.askyesno(
                "Missing Left Ear Content",
                "The Left Ear (first-person 'I AM') text area is empty. "
                "For optimal hemispheric routing, you should include left-ear affirmations.\n\n"
                "Continue anyway?"
            )
            if not result:
                return

        # Determine method from checkboxes
        use_masked = self.masked_var.get()
        use_silent = self.silent_var.get()

        if not use_masked and not use_silent:
            messagebox.showwarning(
                "No Method Selected",
                "Please select at least one subliminal method (Classic Masked or Silent Ultrasonic)."
            )
            return

        if use_masked and use_silent:
            method = "both"
        elif use_masked:
            method = "masked"
        else:
            method = "silent"

        # Get settings
        include_binaural = self.binaural_var.get()
        speed_factor = self.speed_slider.get()
        vocal_volume_db = self.volume_slider.get()
        voice_name = self.voice_var.get()
        voice_code = self.voice_map.get(voice_name, DEFAULT_VOICE)

        # Get custom filename
        filename = self.filename_entry.get().strip()
        if not filename:
            filename = "my_subliminal"
        # Remove any .wav extension the user might have typed
        if filename.lower().endswith(".wav"):
            filename = filename[:-4]
        # Sanitize: remove path separators and other dangerous chars
        filename = "".join(c for c in filename if c.isalnum() or c in " _-").strip()
        if not filename:
            filename = "my_subliminal"

        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="Generating...")

        thread = threading.Thread(
            target=self._run_generation,
            args=(left_text, right_text, center_text, method, include_binaural,
                  speed_factor, vocal_volume_db, voice_code, filename),
            daemon=True,
        )
        thread.start()

    def _run_generation(self, left_text, right_text, center_text, method,
                        include_binaural, speed_factor, vocal_volume_db,
                        voice_code, output_filename):
        """Run the full generation pipeline in a background thread."""
        try:
            # Phase 1: TTS Generation
            self._set_status("Generating speech from text...", 5)

            vocal_paths = generate_all_tracks(
                left_text, right_text, center_text,
                OUTPUT_DIR, voice_code,
                progress_callback=lambda msg, pct: self._set_status(msg, 5 + pct * 0.35),
            )

            # Phase 2: Audio Processing
            self._set_status("Processing audio pipeline...", 45)

            # Ensure filename is unique
            base_name = output_filename
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}.wav")
            counter = 1
            while os.path.exists(output_path):
                output_path = os.path.join(OUTPUT_DIR, f"{base_name}_{counter}.wav")
                counter += 1

            generate_subliminal(
                vocal_left_path=vocal_paths["left"],
                vocal_right_path=vocal_paths["right"],
                vocal_center_path=vocal_paths["center"],
                output_path=output_path,
                method=method,
                speed_factor=speed_factor,
                include_binaural=include_binaural,
                vocal_attenuation_db=vocal_volume_db,
                progress_callback=lambda msg, pct: self._set_status(msg, 45 + pct * 0.55),
            )

            # Success
            output_file = os.path.basename(output_path)
            self._set_status(f"Saved: {output_file}", 100)

            if not self.destroyed:
                self.after(0, lambda: self._on_generation_done(output_path))

        except Exception as e:
            error_str = str(e)
            if "connect" in error_str.lower() or "resolve" in error_str.lower():
                error_str = (
                    "Cannot reach Microsoft Edge TTS servers.\n\n"
                    "Please check your internet connection and try again."
                )
            self._set_status(f"Error: {error_str}", 0)
            if not self.destroyed:
                self.after(0, lambda: self._on_generation_error(error_str))

    def _on_generation_done(self, output_path: str):
        """Re-enable UI after successful generation."""
        if self.destroyed:
            return
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="GENERATE SUBLIMINAL AUDIO")

        result = messagebox.askyesno(
            "Generation Complete",
            f"Subliminal audio saved to:\n{output_path}\n\n"
            f"Remember:\n"
            f"Use stereo headphones\n"
            f"Play at moderate volume (30-50%)\n"
            f"Best before sleep or during meditation\n\n"
            f"Open output folder?"
        )
        if result:
            os.startfile(OUTPUT_DIR)

    def _on_generation_error(self, error_msg: str):
        """Re-enable UI after error."""
        if self.destroyed:
            return
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="GENERATE SUBLIMINAL AUDIO")
        messagebox.showerror("Generation Failed", f"An error occurred:\n\n{error_msg}")

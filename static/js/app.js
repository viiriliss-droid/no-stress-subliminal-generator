/**
 * No-Stress Subliminal Creator — Main App Logic
 *
 * Handles:
 * - Session management & voice loading
 * - Affirmation text input & character counting
 * - Settings (method, speed, volume, voice) with stale-preview detection
 * - TTS speech generation with ETA
 * - Custom mask upload with drag & drop
 * - Preview choice modal (10s sample vs full audio)
 * - Custom audio player with seek bar, play/pause, time display
 * - Cache-busting for preview URLs
 * - Final subliminal export with ETA
 */

(function () {
    'use strict';

    // =========================================================================
    //  DOM Elements
    // =========================================================================
    var $ = function (sel) { return document.querySelector(sel); };
    var $$ = function (sel) { return document.querySelectorAll(sel); };

    // Inputs
    var leftText = $('#leftText');
    var rightText = $('#rightText');
    var centerText = $('#centerText');
    var leftCharCount = $('#leftCharCount');
    var rightCharCount = $('#rightCharCount');
    var centerCharCount = $('#centerCharCount');

    // Settings
    var methodMasked = $('#methodMasked');
    var methodSilent = $('#methodSilent');
    var binauralToggle = $('#binauralToggle');
    var speedSlider = $('#speedSlider');
    var speedValue = $('#speedValue');
    var volumeSlider = $('#volumeSlider');
    var volumeValue = $('#volumeValue');
    var voiceSelect = $('#voiceSelect');
    var leftVoiceSelect = $('#leftVoiceSelect');
    var rightVoiceSelect = $('#rightVoiceSelect');
    var centerVoiceSelect = $('#centerVoiceSelect');

    // Mask & Duration
    var useCustomMask = $('#useCustomMask');
    var maskUploadArea = $('#maskUploadArea');
    var uploadZone = $('#uploadZone');
    var maskFileInput = $('#maskFileInput');
    var maskInfo = $('#maskInfo');
    var maskFilename = $('#maskFilename');
    var maskDuration = $('#maskDuration');
    var removeMaskBtn = $('#removeMaskBtn');
    var durationSection = $('#durationSection');
    var durationInput = $('#durationInput');
    var durationHint = $('#durationHint');

    // Energy Layers
    var energyToggle = $('#energyToggle');
    var energyPanel = $('#energyPanel');
    var entrainmentPreset = $('#entrainmentPreset');
    var schumannToggle = $('#schumannToggle');
    var energyAmpSlider = $('#energyAmpSlider');
    var energyAmpValue = $('#energyAmpValue');
    var solfeggioGrid = $('#solfeggioGrid');
    var energyPresetsGrid = $('#energyPresetsGrid');
    var sweepToggle = $('#sweepToggle');
    var sweepControls = $('#sweepControls');
    var sweepStartHz = $('#sweepStartHz');
    var sweepEndHz = $('#sweepEndHz');
    var sweepInfo = $('#sweepInfo');

    // Buttons
    var generateTTSBtn = $('#generateTTSBtn');
    var previewPlayBtn = $('#previewPlayBtn');
    var previewAudio = $('#previewAudio');
    var previewLabel = $('#previewLabel');
    var previewSection = $('#previewSection');
    var previewEta = $('#previewEta');
    var exportBtn = $('#exportBtn');
    var exportEta = $('#exportEta');
    var filenameInput = $('#filenameInput');

    // Custom player
    var previewSeekBar = $('#previewSeekBar');
    var previewCurrentTime = $('#previewCurrentTime');
    var previewTotalTime = $('#previewTotalTime');

    // TTS Status
    var ttsStatus = $('#ttsStatus');
    var ttsStatusText = $('#ttsStatusText');

    // Progress
    var progressContainer = $('#progressContainer');
    var progressFill = $('#progressFill');
    var progressText = $('#progressText');
    var progressPct = $('#progressPct');

    // Connection Status
    var statusDot = $('.status-dot');
    var statusText = $('.status-text');

    // Modal
    var previewChoiceModal = $('#previewChoiceModal');
    var modalCloseBtn = $('#modalCloseBtn');
    var preview10sBtn = $('#preview10sBtn');
    var previewFullBtn = $('#previewFullBtn');

    // =========================================================================    // State
    // =========================================================================
    var state = {
        sessionId: null,
        voice: 'en-US-AriaNeural',
        leftVoice: null,
        rightVoice: null,
        centerVoice: null,
        tracksGenerated: false,
        maskUploaded: false,
        maskDuration: null,
        vocalMaxDuration: null,
        isGenerating: false,
        audioLoaded: false,
        lastSettingsHash: '',   // for stale preview detection
        previewDuration: 10,    // default 10s clip
        playerInterval: null,
        energyPresets: null,    // loaded from /api/energy/presets
    };

    // =========================================================================
    //  Initialization
    // =========================================================================

    function init() {
        createBgParticles();
        setupEventListeners();
        createSession().then(function () {
            return loadVoices();
        }).then(function () {
            return loadEnergyPresets();
        });
    }

    function createBgParticles() {
        var container = $('#particles');
        for (var i = 0; i < 20; i++) {
            var p = document.createElement('div');
            p.className = 'bg-particle';
            var size = 2 + Math.random() * 4;
            p.style.width = size + 'px';
            p.style.height = size + 'px';
            p.style.left = Math.random() * 100 + '%';
            p.style.animationDuration = (8 + Math.random() * 15) + 's';
            p.style.animationDelay = Math.random() * 15 + 's';
            p.style.opacity = (0.1 + Math.random() * 0.3);
            container.appendChild(p);
        }
    }

    // =========================================================================
    //  Session & Voice Loading
    // =========================================================================

    function createSession() {
        return API.createSession().then(function (data) {
            state.sessionId = data.session_id;
            setStatus('ready', 'Ready');
        }).catch(function () {
            setStatus('error', 'Cannot connect to server');
            showToast('Cannot reach the server. Please ensure it is running.', 'error');
        });
    }

    function loadVoices() {
        return API.getVoices().then(function (data) {
            var voices = data.voices;
            var defaultCode = data.default;

            function buildOptions(selectedCode) {
                var html = '';
                var keys = Object.keys(voices);
                for (var i = 0; i < keys.length; i++) {
                    var name = keys[i];
                    var code = voices[name];
                    var sel = code === selectedCode ? ' selected' : '';
                    html += '<option value="' + code + '"' + sel + '>' + name + '</option>';
                }
                return html;
            }

            voiceSelect.innerHTML = buildOptions(defaultCode);
            var ptOpts = '<option value="" selected>Same as default</option>' + buildOptions(null);
            leftVoiceSelect.innerHTML = ptOpts;
            rightVoiceSelect.innerHTML = ptOpts;
            centerVoiceSelect.innerHTML = ptOpts;
            state.voice = voiceSelect.value;
            computeSettingsHash();
        }).catch(function () {
            var errHtml = '<option>Failed to load voices</option>';
            voiceSelect.innerHTML = errHtml;
            leftVoiceSelect.innerHTML = errHtml;
            rightVoiceSelect.innerHTML = errHtml;
            centerVoiceSelect.innerHTML = errHtml;
        });
    }

    function loadEnergyPresets() {
        return API.getEnergyPresets().then(function (data) {
            state.energyPresets = data;
            buildSolfeggioGrid(data.solfeggio_frequencies);
            buildEnergyPresetCards(data.energy_presets || {});
        }).catch(function () {
            // Energy presets unavailable — build default grid
            state.energyPresets = { brainwave_presets: {}, solfeggio_frequencies: [], schumann_hz: 7.83, energy_presets: {} };
            buildSolfeggioGrid([]);
            buildEnergyPresetCards({});
        });
    }

    function buildSolfeggioGrid(freqs) {
        solfeggioGrid.innerHTML = '';
        if (!freqs || freqs.length === 0) {
            // Default Solfeggio frequencies
            freqs = [
                {hz: 174, label: 'Pain relief'},
                {hz: 285, label: 'Regeneration'},
                {hz: 396, label: 'Liberating guilt'},
                {hz: 417, label: 'Undoing situations'},
                {hz: 528, label: 'Transformation'},
                {hz: 639, label: 'Connection'},
                {hz: 741, label: 'Awakening'},
                {hz: 852, label: 'Spiritual order'},
                {hz: 963, label: 'Pineal gland'},
            ];
        }
        freqs.forEach(function (f) {
            var chip = document.createElement('div');
            chip.className = 'solfeggio-chip';
            chip.title = f.label;
            chip.dataset.hz = f.hz;
            chip.innerHTML = '<span class="chip-check">✓</span><span class="chip-hz">' + f.hz + ' Hz</span>';
            chip.addEventListener('click', function () {
                chip.classList.toggle('selected');
                onSettingChanged();
            });
            solfeggioGrid.appendChild(chip);
        });
    }

    function buildEnergyPresetCards(presets) {
        energyPresetsGrid.innerHTML = '';
        if (!presets || Object.keys(presets).length === 0) {
            // Default presets if API doesn't return any
            presets = {
                "deep_sleep": {
                    label: "Deep Sleep & Healing",
                    desc: "Delta + Schumann + grounding Solfeggio",
                    entrainment_method: "binaural",
                    entrainment_preset: "delta",
                    solfeggio_freqs: [174, 285],
                    schumann: true,
                    energy_amplitude: 0.15,
                },
                "meditation": {
                    label: "Deep Meditation",
                    desc: "Theta + Schumann + Solfeggio triad",
                    entrainment_method: "binaural",
                    entrainment_preset: "theta",
                    solfeggio_freqs: [396, 528, 639],
                    schumann: true,
                    energy_amplitude: 0.15,
                },
                "focus": {
                    label: "Focus & Concentration",
                    desc: "Beta isochronic + clarity Solfeggio",
                    entrainment_method: "isochronic",
                    entrainment_preset: "beta",
                    solfeggio_freqs: [528, 741],
                    schumann: false,
                    energy_amplitude: 0.12,
                },
                "creativity": {
                    label: "Creativity & Flow",
                    desc: "Theta binaural + creative Solfeggio",
                    entrainment_method: "binaural",
                    entrainment_preset: "theta",
                    solfeggio_freqs: [417, 528, 639],
                    schumann: false,
                    energy_amplitude: 0.15,
                },
                "manifestation": {
                    label: "Manifestation",
                    desc: "Theta + full Solfeggio for abundance",
                    entrainment_method: "binaural",
                    entrainment_preset: "theta",
                    solfeggio_freqs: [396, 417, 528, 639, 741],
                    schumann: true,
                    energy_amplitude: 0.18,
                },
                "energy_boost": {
                    label: "Energy Boost",
                    desc: "Gamma isochronic + high Solfeggio",
                    entrainment_method: "isochronic",
                    entrainment_preset: "gamma",
                    solfeggio_freqs: [528, 963],
                    schumann: false,
                    energy_amplitude: 0.12,
                },
            };
        }

        var keys = Object.keys(presets);
        keys.forEach(function (key) {
            var p = presets[key];
            var card = document.createElement('div');
            card.className = 'energy-preset-card';
            card.dataset.presetKey = key;

            // Build tag list
            var tags = [];
            if (p.entrainment_preset) tags.push(p.entrainment_preset);
            if (p.schumann) tags.push('Schumann');
            if (p.solfeggio_freqs && p.solfeggio_freqs.length) tags.push(p.solfeggio_freqs.length + ' tones');
            var tagsHtml = tags.map(function (t) {
                return '<span class="preset-card-tag">' + t + '</span>';
            }).join('');

            card.innerHTML = [
                '<div class="preset-card-title">' + p.label + '</div>',
                '<div class="preset-card-desc">' + (p.desc || '') + '</div>',
                tagsHtml ? '<div class="preset-card-tags">' + tagsHtml + '</div>' : '',
            ].join('');

            card.addEventListener('click', function () {
                applyEnergyPreset(key, presets[key]);
            });

            energyPresetsGrid.appendChild(card);
        });
    }

    function applyEnergyPreset(key, preset) {
        // Activate energy layers
        energyToggle.checked = true;
        energyPanel.style.display = 'block';
        binauralToggle.parentElement.style.display = 'none';

        // Set entrainment method
        var methodRadio = document.querySelector('input[name="entrainmentMethod"][value="' + (preset.entrainment_method || 'binaural') + '"]');
        if (methodRadio) methodRadio.checked = true;
        entrainmentPreset.disabled = false;

        // Set entrainment preset
        if (preset.entrainment_preset) {
            entrainmentPreset.value = preset.entrainment_preset;
        }

        // Set Solfeggio frequencies
        var solfFreqs = preset.solfeggio_freqs || [];
        var chips = solfeggioGrid.querySelectorAll('.solfeggio-chip');
        chips.forEach(function (c) {
            var hz = parseInt(c.dataset.hz);
            if (solfFreqs.indexOf(hz) !== -1) {
                c.classList.add('selected');
            } else {
                c.classList.remove('selected');
            }
        });

        // Set Schumann
        schumannToggle.checked = preset.schumann || false;

        // Set energy amplitude
        var ampPct = Math.round((preset.energy_amplitude || 0.15) * 100);
        energyAmpSlider.value = ampPct;
        energyAmpValue.textContent = ampPct + '%';

        // Highlight active preset card
        var cards = energyPresetsGrid.querySelectorAll('.energy-preset-card');
        cards.forEach(function (c) { c.classList.remove('active'); });
        var activeCard = energyPresetsGrid.querySelector('[data-preset-key="' + key + '"]');
        if (activeCard) activeCard.classList.add('active');

        // Turn off sweep mode when loading a preset
        sweepToggle.checked = false;
        sweepControls.style.display = 'none';

        onSettingChanged();
    }

    function getSelectedSolfeggio() {
        var chips = solfeggioGrid.querySelectorAll('.solfeggio-chip.selected');
        var freqs = [];
        chips.forEach(function (c) { freqs.push(parseInt(c.dataset.hz)); });
        return freqs;
    }

    function getSweepParams() {
        return {
            enabled: sweepToggle.checked,
            start_hz: parseFloat(sweepStartHz.value) || 20,
            end_hz: parseFloat(sweepEndHz.value) || 6,
        };
    }

    function getEffectiveDuration() {
        // Returns the expected audio duration in seconds, or null if unknown
        if (useCustomMask.checked && state.maskUploaded && state.maskDuration) {
            return state.maskDuration;
        }
        // Prefer vocal track max duration if known (from TTS generation)
        if (state.vocalMaxDuration && state.vocalMaxDuration > 0) {
            var inputDur = parseFloat(durationInput.value);
            if (!inputDur || isNaN(inputDur)) return state.vocalMaxDuration;
            return Math.max(state.vocalMaxDuration, inputDur);
        }
        var dur = parseFloat(durationInput.value);
        if (dur && dur > 0) return dur;
        return null;
    }

    function updateSweepInfo() {
        if (!sweepToggle.checked) return;
        var start = parseFloat(sweepStartHz.value) || 20;
        var end = parseFloat(sweepEndHz.value) || 6;
        var dur = getEffectiveDuration();

        if (dur && dur > 0) {
            var m = Math.floor(dur / 60);
            var s = Math.floor(dur % 60);
            var durStr = m > 0 ? m + 'm ' + s + 's' : s + 's';
            sweepInfo.innerHTML = '<span class="sweep-info-text">Sweep: ' + start.toFixed(1) + ' Hz → ' + end.toFixed(1) + ' Hz over ' + durStr + '</span>';
        } else {
            sweepInfo.innerHTML = '<span class="sweep-info-text">Sweep: ' + start.toFixed(1) + ' Hz → ' + end.toFixed(1) + ' Hz over full audio length</span>';
        }
    }

    // =========================================================================
    //  Settings Hash (stale preview detection)
    // =========================================================================

    function computeSettingsHash() {
        var parts = [
            leftText.value.trim(),
            rightText.value.trim(),
            centerText.value.trim(),
            methodMasked.checked ? '1' : '0',
            methodSilent.checked ? '1' : '0',
            binauralToggle.checked ? '1' : '0',
            speedSlider.value,
            volumeSlider.value,
            voiceSelect.value,
            leftVoiceSelect.value,
            rightVoiceSelect.value,
            centerVoiceSelect.value,
            useCustomMask.checked ? '1' : '0',
            durationInput.value,
            energyToggle.checked ? '1' : '0',
            getEntrainmentMethod(),
            entrainmentPreset.value,
            getSelectedSolfeggio().join(','),
            schumannToggle.checked ? '1' : '0',
            energyAmpSlider.value,
            sweepToggle.checked ? '1' : '0',
            sweepStartHz.value,
            sweepEndHz.value,
        ];
        return parts.join('|');
    }

    function markPreviewStale() {
        if (!state.audioLoaded) return;
        previewSection.classList.add('stale');
        previewLabel.textContent = '⚠ Current Preview is not up-to-date. Generate a new one!';
        previewLabel.classList.add('stale');
        previewLabel.classList.remove('ready');
    }

    function clearStaleWarning() {
        previewSection.classList.remove('stale');
        previewLabel.classList.remove('stale');
    }

    function onSettingChanged() {
        if (!state.tracksGenerated) return;
        var newHash = computeSettingsHash();
        if (state.lastSettingsHash && newHash !== state.lastSettingsHash) {
            markPreviewStale();
        }
    }

    // =========================================================================
    //  Event Listeners
    // =========================================================================

    function setupEventListeners() {
        // Text areas
        [leftText, rightText, centerText].forEach(function (ta) {
            ta.addEventListener('input', function () {
                updateCharCounts();
                onSettingChanged();
            });
        });

        // Settings
        speedSlider.addEventListener('input', function () {
            speedValue.textContent = parseFloat(speedSlider.value).toFixed(2) + 'x';
            onSettingChanged();
        });
        volumeSlider.addEventListener('input', function () {
            volumeValue.textContent = parseInt(volumeSlider.value) + ' dB';
            onSettingChanged();
        });
        voiceSelect.addEventListener('change', function () {
            state.voice = voiceSelect.value;
            onSettingChanged();
        });

        // Energy Layers
        energyToggle.addEventListener('change', function () {
            if (energyToggle.checked) {
                energyPanel.style.display = 'block';
                // Hide legacy binaural toggle (energy layers handle entrainment)
                binauralToggle.checked = false;
                binauralToggle.parentElement.style.display = 'none';
            } else {
                energyPanel.style.display = 'none';
                binauralToggle.parentElement.style.display = '';
                // Clear active preset highlight
                var cards = energyPresetsGrid.querySelectorAll('.energy-preset-card');
                cards.forEach(function (c) { c.classList.remove('active'); });
            }
            updateSweepInfo();
            onSettingChanged();
        });

        // Sweep controls
        sweepToggle.addEventListener('change', function () {
            if (sweepToggle.checked) {
                sweepControls.style.display = 'block';
            } else {
                sweepControls.style.display = 'none';
            }
            updateSweepInfo();
            onSettingChanged();
        });
        sweepStartHz.addEventListener('input', function () {
            updateSweepInfo();
            onSettingChanged();
        });
        sweepEndHz.addEventListener('input', function () {
            updateSweepInfo();
            onSettingChanged();
        });

        // Sweep preset buttons
        document.querySelectorAll('.sweep-preset-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                sweepStartHz.value = btn.dataset.start;
                sweepEndHz.value = btn.dataset.end;
                updateSweepInfo();
                onSettingChanged();
            });
        });

        // Entrainment method radio buttons
        document.querySelectorAll('input[name="entrainmentMethod"]').forEach(function (radio) {
            radio.addEventListener('change', function () {
                // Disable preset select if "none" selected
                entrainmentPreset.disabled = radio.value === 'none';
                onSettingChanged();
            });
        });
        entrainmentPreset.addEventListener('change', onSettingChanged);
        schumannToggle.addEventListener('change', onSettingChanged);
        energyAmpSlider.addEventListener('input', function () {
            energyAmpValue.textContent = energyAmpSlider.value + '%';
            onSettingChanged();
        });
        leftVoiceSelect.addEventListener('change', function () {
            state.leftVoice = leftVoiceSelect.value || null;
            onSettingChanged();
        });
        rightVoiceSelect.addEventListener('change', function () {
            state.rightVoice = rightVoiceSelect.value || null;
            onSettingChanged();
        });
        centerVoiceSelect.addEventListener('change', function () {
            state.centerVoice = centerVoiceSelect.value || null;
            onSettingChanged();
        });

        // Methods
        methodMasked.addEventListener('change', onSettingChanged);
        methodSilent.addEventListener('change', onSettingChanged);
        binauralToggle.addEventListener('change', onSettingChanged);

        // Mask
        useCustomMask.addEventListener('change', function () {
            if (useCustomMask.checked) {
                maskUploadArea.style.display = 'block';
                durationSection.style.display = 'none';
            } else {
                maskUploadArea.style.display = 'none';
                durationSection.style.display = 'block';
                maskInfo.style.display = 'none';
                state.maskUploaded = false;
                state.maskDuration = null;
                updateDurationHint();
                updateSweepInfo();
            }
            onSettingChanged();
        });

        uploadZone.addEventListener('click', function () { maskFileInput.click(); });
        maskFileInput.addEventListener('change', function (e) { handleMaskFile(e.target.files[0]); });
        uploadZone.addEventListener('dragover', function (e) { e.preventDefault(); uploadZone.classList.add('drag-over'); });
        uploadZone.addEventListener('dragleave', function () { uploadZone.classList.remove('drag-over'); });
        uploadZone.addEventListener('drop', function (e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            if (e.dataTransfer.files[0]) handleMaskFile(e.dataTransfer.files[0]);
        });
        removeMaskBtn.addEventListener('click', function () {
            state.maskUploaded = false;
            state.maskDuration = null;
            maskInfo.style.display = 'none';
            maskFileInput.value = '';
            uploadZone.style.display = 'flex';
            updateDurationHint();
            updateSweepInfo();
            onSettingChanged();
        });

        // Duration
        $$('.preset-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                $$('.preset-btn').forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                durationInput.value = btn.dataset.duration;
                updateDurationHint();
                updateSweepInfo();
                onSettingChanged();
            });
        });
        durationInput.addEventListener('input', function () {
            $$('.preset-btn').forEach(function (b) { b.classList.remove('active'); });
            updateDurationHint();
            updateSweepInfo();
            onSettingChanged();
        });

        // Buttons
        generateTTSBtn.addEventListener('click', handleGenerateTTS);
        previewPlayBtn.addEventListener('click', function () {
            if (state.audioLoaded && previewAudio.src) {
                togglePreviewPlayback();
            } else {
                openPreviewChoiceModal();
            }
        });
        exportBtn.addEventListener('click', handleExport);

        // Modal
        modalCloseBtn.addEventListener('click', closePreviewModal);
        previewChoiceModal.addEventListener('click', function (e) {
            if (e.target === previewChoiceModal) closePreviewModal();
        });
        preview10sBtn.addEventListener('click', function () {
            closePreviewModal();
            state.previewDuration = 10;
            doPreview();
        });
        previewFullBtn.addEventListener('click', function () {
            closePreviewModal();
            state.previewDuration = -1;  // full audio
            doPreview();
        });

        // Custom audio player events
        previewAudio.addEventListener('loadedmetadata', function () {
            previewTotalTime.textContent = fmtTime(previewAudio.duration);
            previewSeekBar.max = previewAudio.duration;
            state.audioLoaded = true;
        });
        previewAudio.addEventListener('timeupdate', function () {
            previewSeekBar.value = previewAudio.currentTime;
            previewCurrentTime.textContent = fmtTime(previewAudio.currentTime);
        });
        previewAudio.addEventListener('ended', function () {
            updatePlayIcon(false);
            previewLabel.textContent = 'Preview ended — ' + fmtTime(previewAudio.duration || 0);
        });
        previewAudio.addEventListener('play', function () { updatePlayIcon(true); });
        previewAudio.addEventListener('pause', function () { updatePlayIcon(false); });

        previewSeekBar.addEventListener('input', function () {
            previewAudio.currentTime = parseFloat(previewSeekBar.value);
            previewCurrentTime.textContent = fmtTime(previewAudio.currentTime);
        });

        // Keyboard
        document.addEventListener('keydown', function (e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            if (e.code === 'Space') {
                e.preventDefault();
                togglePreviewPlayback();
            }
        });
    }

    // =========================================================================
    //  Preview Choice Modal
    // =========================================================================

    function openPreviewChoiceModal() {
        if (!state.tracksGenerated || !state.sessionId) {
            showToast('Generate speech tracks first.', 'error');
            return;
        }
        previewChoiceModal.style.display = 'flex';
    }

    function closePreviewModal() {
        previewChoiceModal.style.display = 'none';
    }

    // =========================================================================
    //  Custom Audio Player
    // =========================================================================

    function updatePlayIcon(playing) {
        previewPlayBtn.innerHTML = playing
            ? '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
            : '<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
    }

    function togglePreviewPlayback() {
        if (!state.audioLoaded || !previewAudio.src) {
            openPreviewChoiceModal();
            return;
        }
        if (previewAudio.paused) {
            previewAudio.play().catch(function () {
                showToast('Cannot play audio. Try generating a new preview.', 'warning');
            });
        } else {
            previewAudio.pause();
        }
    }

    // =========================================================================
    //  UI Helpers
    // =========================================================================

    function updateCharCounts() {
        leftCharCount.textContent = leftText.value.length + ' chars';
        rightCharCount.textContent = rightText.value.length + ' chars';
        centerCharCount.textContent = centerText.value.length + ' chars';
    }

    function updateDurationHint() {
        if (state.tracksGenerated) {
            durationHint.textContent = 'Affirmations will loop to fill this duration.';
        } else {
            durationHint.textContent = 'Generate speech tracks first to see the base length.';
        }
        updateSweepInfo();
    }

    function setStatus(type, msg) {
        statusText.textContent = msg;
        statusDot.className = 'status-dot' + (type === 'busy' ? ' busy' : '');
    }

    function setProgress(percent, msg) {
        if (percent > 0) {
            progressContainer.style.display = 'flex';
            progressFill.style.width = percent + '%';
            progressText.textContent = msg || 'Processing...';
            progressPct.textContent = percent + '%';
        } else {
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
            progressPct.textContent = '0%';
        }
    }

    function showToast(message, type) {
        type = type || 'info';
        var container = $('#toastContainer');
        var toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () {
            toast.classList.add('toast-out');
            setTimeout(function () { toast.remove(); }, 300);
        }, 3500);
    }

    function fmtTime(seconds) {
        if (!seconds || isNaN(seconds) || seconds < 0) return '0:00';
        var m = Math.floor(seconds / 60);
        var s = Math.floor(seconds % 60);
        return m + ':' + (s < 10 ? '0' : '') + s;
    }

    function fmtDuration(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        var m = Math.floor(seconds / 60);
        var s = Math.floor(seconds % 60);
        if (m > 0) return m + 'm ' + s + 's';
        return s + 's';
    }

    // =========================================================================
    //  Mask Upload Handler
    // =========================================================================

    function handleMaskFile(file) {
        if (!file) return;
        if (!state.sessionId) {
            showToast('Session not ready. Please wait.', 'error');
            return;
        }
        setStatus('busy', 'Uploading mask...');
        uploadZone.style.display = 'none';

        API.uploadMask(state.sessionId, file).then(function (data) {
            state.maskUploaded = true;
            state.maskDuration = data.duration;
            maskFilename.textContent = file.name;
            maskDuration.textContent = '(' + fmtDuration(data.duration) + ')';
            maskInfo.style.display = 'flex';
            durationInput.value = Math.ceil(data.duration);
            updateSweepInfo();
            showToast('Mask loaded: ' + fmtDuration(data.duration), 'success');
            setStatus('ready', 'Mask ready');
            onSettingChanged();
        }).catch(function (err) {
            showToast('Failed to upload mask: ' + err.message, 'error');
            uploadZone.style.display = 'flex';
            setStatus('ready', 'Error');
        });
    }

    // =========================================================================
    //  TTS Generation
    // =========================================================================

    function handleGenerateTTS() {
        var l = leftText.value.trim();
        var r = rightText.value.trim();
        var c = centerText.value.trim();

        if (!l && !r && !c) {
            showToast('Please enter affirmations in at least one text area.', 'error');
            return;
        }
        if (!state.sessionId) {
            showToast('Session not ready. Please wait.', 'error');
            return;
        }

        setStatus('busy', 'Generating speech...');
        generateTTSBtn.disabled = true;
        generateTTSBtn.innerHTML =
            '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite;">' +
            '<circle cx="12" cy="12" r="10" stroke-opacity="0.3"/><path d="M12 2a10 10 0 019.95 9" stroke-linecap="round"/>' +
            '</svg> Generating...';
        setProgress(10, 'Contacting TTS server...');

        API.generateTTS(state.sessionId, l, r, c, state.voice,
            state.leftVoice, state.rightVoice, state.centerVoice
        ).then(function (data) {
            setProgress(50, 'Processing tracks...');

            var durs = [data.durations.left || 0, data.durations.right || 0, data.durations.center || 0];
            var maxDur = Math.max.apply(null, durs);
            state.vocalMaxDuration = maxDur;
            if (maxDur > 0) {
                durationHint.textContent = 'Longest vocal track: ' + fmtDuration(maxDur) + '. Will loop to fill target.';
            }

            state.tracksGenerated = true;
            state.audioLoaded = false;
            state.lastSettingsHash = computeSettingsHash();
            updateSweepInfo();

            // Show TTS status + preview section
            ttsStatus.style.display = 'flex';
            ttsStatusText.textContent = 'Speech tracks ready — ' +
                'L:' + fmtDuration(data.durations.left || 0) + ' ' +
                'R:' + fmtDuration(data.durations.right || 0) + ' ' +
                'C:' + fmtDuration(data.durations.center || 0);

            previewSection.style.display = 'block';
            previewLabel.textContent = 'Click Preview to hear your audio';
            previewLabel.classList.add('ready');
            clearStaleWarning();

            exportBtn.disabled = false;

            setProgress(0, '');
            setStatus('ready', 'Tracks ready');
            showToast('Speech tracks generated! Preview or export now.', 'success');
        }).catch(function (err) {
            showToast('TTS generation failed: ' + err.message, 'error');
            setStatus('ready', 'TTS error');
        }).then(function () {
            generateTTSBtn.disabled = false;
            generateTTSBtn.innerHTML =
                '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                '<polygon points="5 3 19 12 5 21 5 3"/>' +
                '</svg> Step 1: Generate Speech Tracks';
            setProgress(0, '');
        });
    }

    // =========================================================================
    //  Progress Polling
    // =========================================================================

    function startProgressPolling(onProgress, onDone) {
        var pollInterval = setInterval(function () {
            API.getProgress(state.sessionId).then(function (data) {
                onProgress(data.percent, data.message);
                if (data.done) {
                    clearInterval(pollInterval);
                    if (onDone) onDone();
                }
            }).catch(function () {
                // Server may not respond during heavy processing; keep polling
            });
        }, 500);
        return pollInterval;
    }

    // =========================================================================
    //  Preview
    // =========================================================================

    function doPreview() {
        if (!state.tracksGenerated || !state.sessionId) {
            showToast('Generate speech tracks first.', 'error');
            return;
        }

        var isFull = state.previewDuration < 0;
        var settings = getExportSettings();
        settings.preview_duration = isFull ? 999999 : 10.0;

        setStatus('busy', 'Generating preview...');
        setProgress(0, 'Starting preview...');
        previewPlayBtn.disabled = true;
        updatePlayIcon(false);

        previewEta.style.display = 'inline';
        previewEta.textContent = '0%';

        previewLabel.textContent = 'Generating preview...';
        previewLabel.classList.remove('stale');
        previewLabel.classList.remove('ready');

        // Start real progress polling
        var poller = startProgressPolling(
            function (pct, msg) {
                setProgress(pct, msg);
                previewEta.textContent = pct + '%';
            },
            null  // don't auto-clear; we clear in .then()/.catch()
        );

        API.generatePreview(state.sessionId, settings).then(function (data) {
            clearInterval(poller);
            setProgress(100, 'Preview ready!');
            previewEta.textContent = '100% — loading audio...';

            // Cache-bust: add timestamp to URL so volume/voice changes are picked up
            var previewUrl = API.getAudioUrl(state.sessionId, 'preview.wav') + '?t=' + Date.now();
            previewAudio.src = previewUrl;
            previewAudio.load();

            function tryPlay() {
                previewAudio.play().catch(function () {
                    showToast('Preview ready — click Play to hear it', 'info');
                });
            }

            if (previewAudio.readyState >= 3) {
                tryPlay();
            } else {
                previewAudio.oncanplaythrough = function () {
                    tryPlay();
                    previewAudio.oncanplaythrough = null;
                };
                setTimeout(function () {
                    if (previewAudio.paused && previewAudio.src) {
                        previewAudio.play().catch(function () {});
                    }
                }, 1000);
            }

            var labelText = isFull
                ? 'Full preview: ' + fmtDuration(data.duration)
                : '10s preview clip: ' + fmtDuration(data.duration);
            previewLabel.textContent = labelText;
            previewLabel.classList.add('ready');

            state.audioLoaded = true;
            state.lastSettingsHash = computeSettingsHash();
            clearStaleWarning();

            previewEta.style.display = 'none';
            setStatus('ready', 'Preview ready');
            showToast('Preview ready — ' + fmtDuration(data.duration), 'success');

            setTimeout(function () { setProgress(0, ''); }, 1500);
        }).catch(function (err) {
            clearInterval(poller);
            state.audioLoaded = false;
            showToast('Preview failed: ' + err.message, 'error');
            setProgress(0, '');
            setStatus('ready', 'Preview error');
            previewLabel.textContent = 'Preview failed';
            previewLabel.classList.remove('ready');
            previewEta.style.display = 'none';
        }).then(function () {
            previewPlayBtn.disabled = false;
            updatePlayIcon(!previewAudio.paused);
        });
    }

    // =========================================================================
    //  Export
    // =========================================================================

    function handleExport() {
        if (!state.tracksGenerated || !state.sessionId) {
            showToast('Generate speech tracks first.', 'error');
            return;
        }
        if (state.isGenerating) return;

        var fname = filenameInput.value.trim() || 'my_subliminal';
        var settings = getExportSettings();
        settings.output_filename = fname;

        // Step 1: Let user choose where to save the file BEFORE generation starts.
        // showSaveFilePicker() opens the native OS file picker — same UX as the
        // drag-and-drop import for masking music, but for saving.
        var fileHandle = null;
        var usePicker = typeof window.showSaveFilePicker === 'function';

        function startGeneration() {
            state.isGenerating = true;

            setStatus('busy', 'Generating...');
            exportBtn.disabled = true;
            exportBtn.innerHTML =
                '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite;">' +
                '<circle cx="12" cy="12" r="10" stroke-opacity="0.3"/><path d="M12 2a10 10 0 019.95 9" stroke-linecap="round"/>' +
                '</svg> Generating...';

            setProgress(0, 'Starting...');

            var t0 = Date.now();

            // Show percentage from real progress
            exportEta.style.display = 'block';
            exportEta.textContent = '0%';

            // Start real progress polling
            var poller = startProgressPolling(
                function (pct, msg) {
                    setProgress(pct, msg);
                    exportEta.textContent = pct + '% — ' + msg;
                },
                null
            );

            API.generateSubliminal(state.sessionId, settings).then(async function (data) {
                clearInterval(poller);
                var elapsed = ((Date.now() - t0) / 1000).toFixed(1);
                setProgress(100, 'Complete in ' + elapsed + 's!');
                exportEta.textContent = '100% — Completed in ' + elapsed + 's';

                // NOTE: async body inside .then() — errors from awaits are NOT caught
                // by the .catch() on the chain, so wrap the entire async block in try/catch.
                try {
                    if (fileHandle) {
                        // Write directly to the user-chosen file via File System Access API
                        var resp = await fetch('/api/audio/' + state.sessionId + '/' + data.output_file);
                        var blob = await resp.blob();
                        var writable = await fileHandle.createWritable();
                        await writable.write(blob);
                        await writable.close();
                        showToast('Saved: ' + data.output_file + ' (' + fmtDuration(data.duration) + ')', 'success');
                    } else {
                        // Fallback: trigger native Save As dialog via download endpoint
                        var downloadUrl = '/api/download/' + state.sessionId + '/' + data.output_file;
                        var a = document.createElement('a');
                        a.href = downloadUrl;
                        a.download = data.output_file;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        showToast('Saved: ' + data.output_file + ' (' + fmtDuration(data.duration) + ')', 'success');
                    }
                } catch (writeErr) {
                    showToast('File generated but could not save to chosen folder: ' + writeErr.message, 'warning');
                    // Fallback: still try download endpoint so the user can get the file
                    try {
                        var fallbackUrl = '/api/download/' + state.sessionId + '/' + data.output_file;
                        var fb = document.createElement('a');
                        fb.href = fallbackUrl;
                        fb.download = data.output_file;
                        document.body.appendChild(fb);
                        fb.click();
                        document.body.removeChild(fb);
                    } catch (_) {}
                }

                setStatus('ready', 'Exported: ' + data.output_file);

                setTimeout(function () { setProgress(0, ''); exportEta.style.display = 'none'; }, 3000);
            }).catch(function (err) {
                clearInterval(poller);
                showToast('Export failed: ' + err.message, 'error');
                setStatus('ready', 'Export error');
                setProgress(0, '');
                exportEta.style.display = 'none';
            }).then(function () {
                state.isGenerating = false;
                exportBtn.disabled = false;
                exportBtn.innerHTML =
                    '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                    '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>' +
                    '<polyline points="7 10 12 15 17 10"/>' +
                    '<line x1="12" y1="15" x2="12" y2="3"/>' +
                    '</svg> Step 3: Export Full Audio';
            });
        }

        if (usePicker) {
            // Open native OS file picker — user navigates to a folder and picks a filename
            window.showSaveFilePicker({
                suggestedName: fname + '.wav',
                types: [{
                    description: 'WAV Audio File',
                    accept: { 'audio/wav': ['.wav'] }
                }]
            }).then(function (handle) {
                fileHandle = handle;
                startGeneration();
            }).catch(function () {
                // User cancelled the file picker — do nothing
            });
        } else {
            // Browser doesn't support showSaveFilePicker — fall back to <a download>
            startGeneration();
        }
    }

    // =========================================================================
    //  Helpers
    // =========================================================================

    function getEntrainmentMethod() {
        var checked = document.querySelector('input[name="entrainmentMethod"]:checked');
        return checked ? checked.value : 'binaural';
    }

    function getExportSettings() {
        var useMasked = methodMasked.checked;
        var useSilent = methodSilent.checked;
        var method = 'masked';
        if (useMasked && useSilent) method = 'both';
        else if (useSilent) method = 'silent';

        var useMask = useCustomMask.checked && state.maskUploaded;
        var targetDur = useMask ? null : parseFloat(durationInput.value) || 300;

        var settings = {
            method: method,
            speed_factor: parseFloat(speedSlider.value),
            vocal_volume_db: parseFloat(volumeSlider.value),
            include_binaural: binauralToggle.checked,
            use_custom_mask: useMask,
            target_duration: targetDur,
        };

        // Energy layers
        if (energyToggle.checked) {
            var entMethod = getEntrainmentMethod();
            var sweep = getSweepParams();
            settings.energy_layers = {
                entrainment_method: entMethod === 'none' ? null : entMethod,
                entrainment_preset: entrainmentPreset.value,
                solfeggio_freqs: getSelectedSolfeggio(),
                schumann: schumannToggle.checked,
                energy_amplitude: parseFloat(energyAmpSlider.value) / 100.0,
                sweep_enabled: sweep.enabled,
                sweep_start_hz: sweep.start_hz,
                sweep_end_hz: sweep.end_hz,
            };
            // When energy layers active, entrainment is handled there;
            // the legacy binaural is explicitly off
            if (settings.energy_layers.entrainment_method) {
                settings.include_binaural = false;
            }
        }

        return settings;
    }

    // =========================================================================
    //  Start
    // =========================================================================

    document.addEventListener('DOMContentLoaded', init);
})();

// Injected styles
(function () {
    var style = document.createElement('style');
    style.textContent =
        '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }' +
        '.upload-zone { display: flex; flex-direction: column; align-items: center; }' +
        '.upload-zone.drag-over { border-color: rgba(255,255,255,0.25); background: rgba(255,255,255,0.02); }';
    document.head.appendChild(style);
})();

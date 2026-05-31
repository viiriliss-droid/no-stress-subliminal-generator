/**
 * API Client — Communicates with the Flask backend.
 */

const API = {
    BASE: '/api',

    async _fetch(url, options = {}) {
        try {
            const res = await fetch(url, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options,
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || `HTTP ${res.status}`);
            }
            return data;
        } catch (err) {
            if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
                throw new Error('Cannot reach the server. Is it running?');
            }
            throw err;
        }
    },

    async createSession() {
        return this._fetch(`${this.BASE}/session/create`, { method: 'POST' });
    },

    async getVoices() {
        return this._fetch(`${this.BASE}/voices`);
    },

    async generateTTS(sessionId, leftText, rightText, centerText, voice, leftVoice, rightVoice, centerVoice) {
        return this._fetch(`${this.BASE}/tts/generate`, {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                left_text: leftText,
                right_text: rightText,
                center_text: centerText,
                voice: voice,
                left_voice: leftVoice || null,
                right_voice: rightVoice || null,
                center_voice: centerVoice || null,
            }),
        });
    },

    async uploadMask(sessionId, file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);

        const res = await fetch(`${this.BASE}/mask/upload`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Upload failed');
        return data;
    },

    async generateSubliminal(sessionId, settings) {
        return this._fetch(`${this.BASE}/generate`, {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, ...settings }),
        });
    },

    async generatePreview(sessionId, settings) {
        return this._fetch(`${this.BASE}/preview`, {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, ...settings }),
        });
    },

    getAudioUrl(sessionId, filename) {
        return `${this.BASE}/audio/${sessionId}/${filename}`;
    },

    async getProgress(sessionId) {
        return this._fetch(`${this.BASE}/progress/${sessionId}`);
    },

    async getEnergyPresets() {
        return this._fetch(`${this.BASE}/energy/presets`);
    },

};

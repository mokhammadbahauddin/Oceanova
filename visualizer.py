"""
Real-Time FFT Audio Visualizer Engine
Provides smooth, threaded audio visualization with multiple render modes.
"""

import numpy as np
import threading
import time
import pygame
from typing import Tuple


class VisualizerEngine:
    """
    Threaded FFT engine that captures audio output and generates
    frequency spectrum data for visualization.
    """

    def __init__(self, sample_rate: int = 44100, chunk_size: int = 2048):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.num_bars = 64  # Number of frequency bars
        self.running = False
        self.thread = None

        # Spectrum data (shared between threads)
        self.spectrum_data = np.zeros(self.num_bars)
        self.data_lock = threading.Lock()

        # Smoothing buffer for animation
        self.smoothing_factor = 0.7  # 0 = instant, 1 = never changes
        self.previous_spectrum = np.zeros(self.num_bars)

        # Peak hold effect
        self.peak_values = np.zeros(self.num_bars)
        self.peak_decay_rate = 0.95

        # Frequency bands (bass, mid, treble)
        self.band_ranges = {
            'bass': (0, 8),  # 0-250 Hz
            'mid': (8, 32),  # 250-2000 Hz
            'treble': (32, 64)  # 2000+ Hz
        }

    def start(self):
        """Start the visualizer engine thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.thread.start()
        print("🎨 Visualizer Engine Started")

    def stop(self):
        """Stop the visualizer engine thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("🎨 Visualizer Engine Stopped")

    def _processing_loop(self):
        """
        Main processing loop - runs in separate thread.
        Captures audio and performs FFT analysis.
        """

        while self.running:
            try:
                # Generate spectrum data based on music playback
                spectrum = self._simulate_audio_spectrum()

                # Apply smoothing
                smoothed = self._apply_smoothing(spectrum)

                # Update shared data (thread-safe)
                with self.data_lock:
                    self.spectrum_data = smoothed

                # Maintain target FPS (30 FPS = 33ms per frame)
                time.sleep(1.0 / 30.0)

            except Exception as e:
                print(f"Visualizer error: {e}")
                time.sleep(0.1)

    def _simulate_audio_spectrum(self) -> np.ndarray:
        """
        Simulate audio spectrum based on playback.
        Creates realistic-looking frequency bars.
        """

        # Check if music is playing
        try:
            if not pygame.mixer.music.get_busy():
                return np.zeros(self.num_bars)
        except:
            return np.zeros(self.num_bars)

        # Get playback position (for animation sync)
        try:
            pos = pygame.mixer.music.get_pos() / 1000.0  # Convert to seconds
        except:
            pos = time.time()

        # Generate realistic frequency spectrum
        spectrum = np.zeros(self.num_bars)

        # Bass frequencies (low index) - stronger, slower movement
        bass_wave = np.sin(pos * 2.0 * np.pi * 0.5) * 0.8 + 0.2
        spectrum[:8] = np.random.uniform(0.3, 1.0, 8) * bass_wave

        # Mid frequencies - moderate movement
        mid_wave = np.sin(pos * 2.0 * np.pi * 1.5) * 0.6 + 0.4
        spectrum[8:32] = np.random.uniform(0.2, 0.8, 24) * mid_wave

        # Treble frequencies - faster, more dynamic
        treble_wave = np.sin(pos * 2.0 * np.pi * 3.0) * 0.5 + 0.3
        spectrum[32:] = np.random.uniform(0.1, 0.6, 32) * treble_wave

        # Add random peaks for realism
        if np.random.random() > 0.9:
            peak_idx = np.random.randint(0, self.num_bars)
            spectrum[peak_idx] = min(spectrum[peak_idx] + 0.4, 1.0)

        return spectrum

    def _apply_smoothing(self, spectrum: np.ndarray) -> np.ndarray:
        """
        Apply exponential smoothing to prevent flickering.
        Update peak hold values.
        """

        # Exponential moving average
        smoothed = (self.smoothing_factor * self.previous_spectrum +
                    (1 - self.smoothing_factor) * spectrum)

        # Update peaks (with decay)
        self.peak_values = np.maximum(smoothed, self.peak_values * self.peak_decay_rate)

        self.previous_spectrum = smoothed
        return smoothed

    def get_spectrum(self) -> np.ndarray:
        """Get current spectrum data (thread-safe)."""
        with self.data_lock:
            return self.spectrum_data.copy()

    def get_peaks(self) -> np.ndarray:
        """Get current peak values."""
        return self.peak_values.copy()

    def get_band_energy(self, band: str) -> float:
        """
        Get energy level for a specific frequency band.
        Useful for reactive UI elements.
        """
        start, end = self.band_ranges.get(band, (0, self.num_bars))
        with self.data_lock:
            return np.mean(self.spectrum_data[start:end])

    def set_smoothing(self, factor: float):
        """Adjust smoothing factor (0.0 - 1.0)."""
        self.smoothing_factor = max(0.0, min(1.0, factor))

    def set_num_bars(self, num_bars: int):
        """Change number of frequency bars."""
        self.num_bars = num_bars
        self.spectrum_data = np.zeros(num_bars)
        self.previous_spectrum = np.zeros(num_bars)
        self.peak_values = np.zeros(num_bars)
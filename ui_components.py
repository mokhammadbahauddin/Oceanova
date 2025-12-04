"""
CustomTkinter Visualizer UI Components
Provides canvas-based visualizer widgets with multiple render modes.
"""

import customtkinter as ctk
import numpy as np


class AudioVisualizer(ctk.CTkCanvas):
    """
    Real-time audio visualizer canvas with multiple render modes.
    Displays frequency spectrum as animated bars.
    """

    def __init__(self, master, visualizer_engine, mode='bars', **kwargs):
        """
        Args:
            master: Parent widget
            visualizer_engine: VisualizerEngine instance
            mode: 'bars', 'wave', 'circular', 'radial'
        """

        # Default canvas settings
        default_kwargs = {
            'width': 600,
            'height': 200,
            'bg': '#1E1A3D',
            'highlightthickness': 0
        }
        default_kwargs.update(kwargs)

        super().__init__(master, **default_kwargs)

        self.engine = visualizer_engine
        self.mode = mode
        self.animating = False
        self.animation_id = None

        # Visual settings
        self.bar_color = '#5FAEF8'
        self.peak_color = '#F0F0F0'
        self.bg_color = '#1E1A3D'
        self.gradient_colors = ['#5FAEF8', '#6A55F5', '#5FAEF8']

        # Bar settings
        self.bar_width_ratio = 0.8  # Bar width as ratio of spacing
        self.bar_spacing = 10
        self.bar_min_height = 5

        # Animation settings
        self.fps = 30
        self.frame_delay = int(1000 / self.fps)  # ms

        # Bind resize event
        self.bind('<Configure>', self._on_resize)

    def start_animation(self):
        """Start the visualization animation loop."""
        if not self.animating:
            self.animating = True
            self._animate()

    def stop_animation(self):
        """Stop the visualization animation loop."""
        self.animating = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        self.delete('all')  # Clear canvas

    def _animate(self):
        """Main animation loop."""
        if not self.animating:
            return

        # Render frame based on mode
        if self.mode == 'bars':
            self._render_bars()
        elif self.mode == 'wave':
            self._render_wave()
        elif self.mode == 'circular':
            self._render_circular()
        elif self.mode == 'radial':
            self._render_radial()

        # Schedule next frame
        self.animation_id = self.after(self.frame_delay, self._animate)

    def _render_bars(self):
        """Render vertical frequency bars."""
        self.delete('all')  # Clear previous frame

        # Get spectrum data
        spectrum = self.engine.get_spectrum()
        peaks = self.engine.get_peaks()

        if len(spectrum) == 0:
            return

        # Canvas dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            return

        # Calculate bar dimensions
        num_bars = len(spectrum)
        bar_width = (canvas_width / num_bars) * self.bar_width_ratio
        bar_gap = canvas_width / num_bars

        # Draw bars
        for i, (value, peak) in enumerate(zip(spectrum, peaks)):
            x = i * bar_gap + (bar_gap - bar_width) / 2

            # Bar height (inverted Y axis)
            bar_height = max(value * canvas_height, self.bar_min_height)
            y_top = canvas_height - bar_height

            # Gradient color based on frequency
            color = self._get_gradient_color(i / num_bars)

            # Draw bar
            self.create_rectangle(
                x, y_top,
                x + bar_width, canvas_height,
                fill=color,
                outline=''
            )

            # Draw peak indicator
            peak_height = peak * canvas_height
            peak_y = canvas_height - peak_height
            self.create_line(
                x, peak_y,
                x + bar_width, peak_y,
                fill=self.peak_color,
                width=2
            )

    def _render_wave(self):
        """Render waveform visualization."""
        self.delete('all')

        spectrum = self.engine.get_spectrum()
        if len(spectrum) == 0:
            return

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        center_y = canvas_height / 2

        # Create points for wave
        points = []
        for i, value in enumerate(spectrum):
            x = (i / len(spectrum)) * canvas_width
            y = center_y + (value - 0.5) * canvas_height
            points.extend([x, y])

        if len(points) >= 4:  # Need at least 2 points
            self.create_line(
                points,
                fill=self.bar_color,
                width=3,
                smooth=True
            )

    def _render_circular(self):
        """Render circular frequency visualization."""
        self.delete('all')

        spectrum = self.engine.get_spectrum()
        if len(spectrum) == 0:
            return

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        max_radius = min(canvas_width, canvas_height) / 2 - 10

        num_bars = len(spectrum)
        angle_step = 360 / num_bars

        for i, value in enumerate(spectrum):
            angle = np.radians(i * angle_step)

            # Inner and outer radius
            inner_r = max_radius * 0.3
            outer_r = inner_r + (value * max_radius * 0.7)

            # Calculate bar endpoints
            x1 = center_x + inner_r * np.cos(angle)
            y1 = center_y + inner_r * np.sin(angle)
            x2 = center_x + outer_r * np.cos(angle)
            y2 = center_y + outer_r * np.sin(angle)

            color = self._get_gradient_color(i / num_bars)

            self.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=3
            )

    def _render_radial(self):
        """Render radial burst visualization."""
        self.delete('all')

        # Get bass energy for reactive center circle
        bass_energy = self.engine.get_band_energy('bass')

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Draw reactive center circle
        circle_radius = 30 + (bass_energy * 50)
        self.create_oval(
            center_x - circle_radius, center_y - circle_radius,
            center_x + circle_radius, center_y + circle_radius,
            fill=self.bar_color,
            outline=''
        )

        # Draw radial bars
        spectrum = self.engine.get_spectrum()
        num_bars = len(spectrum)
        angle_step = 360 / num_bars
        max_length = min(canvas_width, canvas_height) / 2 - 50

        for i, value in enumerate(spectrum):
            angle = np.radians(i * angle_step)

            bar_length = value * max_length
            start_r = circle_radius + 10
            end_r = start_r + bar_length

            x1 = center_x + start_r * np.cos(angle)
            y1 = center_y + start_r * np.sin(angle)
            x2 = center_x + end_r * np.cos(angle)
            y2 = center_y + end_r * np.sin(angle)

            color = self._get_gradient_color(value)

            self.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=2
            )

    def _get_gradient_color(self, position: float) -> str:
        """
        Interpolate color from gradient based on position (0.0 - 1.0).
        """
        # Simple gradient between two colors
        if position < 0.5:
            return self.gradient_colors[0]
        else:
            return self.gradient_colors[2]

    def _on_resize(self, event):
        """Handle canvas resize."""
        pass  # Canvas will redraw on next animation frame

    def set_colors(self, bar_color: str, peak_color: str, bg_color: str):
        """Update visualizer colors."""
        self.bar_color = bar_color
        self.peak_color = peak_color
        self.bg_color = bg_color
        self.configure(bg=bg_color)

    def set_mode(self, mode: str):
        """Change visualization mode."""
        if mode in ['bars', 'wave', 'circular', 'radial']:
            self.mode = mode


class FullscreenVisualizer(ctk.CTkToplevel):
    """
    Fullscreen visualizer window with controls.
    """

    def __init__(self, parent, visualizer_engine, song_title="Now Playing"):
        super().__init__(parent)

        self.title("Visualizer")
        self.geometry("1200x800")
        self.configure(fg_color="#0A0A0A")

        # Header with song info
        header = ctk.CTkFrame(self, fg_color="transparent", height=80)
        header.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            header,
            text=song_title,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#FFFFFF"
        ).pack()

        # Visualizer canvas
        self.visualizer = AudioVisualizer(
            self,
            visualizer_engine,
            mode='radial',
            width=1200,
            height=600,
            bg='#0A0A0A'
        )
        self.visualizer.pack(fill="both", expand=True, padx=20, pady=20)

        # Controls
        controls = ctk.CTkFrame(self, fg_color="transparent", height=60)
        controls.pack(fill="x", padx=20, pady=(0, 20))

        modes = ['bars', 'wave', 'circular', 'radial']
        for mode in modes:
            ctk.CTkButton(
                controls,
                text=mode.capitalize(),
                width=100,
                command=lambda m=mode: self.visualizer.set_mode(m)
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls,
            text="Close",
            width=100,
            command=self.close_visualizer
        ).pack(side="right", padx=5)

        # Start animation
        self.visualizer.start_animation()

        # Bind escape key
        self.bind('<Escape>', lambda e: self.close_visualizer())

    def close_visualizer(self):
        """Stop animation and close window."""
        self.visualizer.stop_animation()
        self.destroy()
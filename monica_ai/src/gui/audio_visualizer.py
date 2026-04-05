"""
Sci-Fi Audio Level Visualizer for Monica AI
Dynamic visualization with cyberpunk colors
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import threading
import time
import colorsys
from collections import deque

class AudioVisualizer:
    """Sci-fi audio level visualization widget."""
    
    def __init__(self, parent, width=800, height=60):
        """Initialize audio visualizer."""
        self.parent = parent
        self.width = width
        self.height = height
        
        # Create canvas
        self.canvas = Canvas(
            parent,
            width=width,
            height=height,
            bg='#0a0a0a',
            highlightthickness=0
        )
        
        # Sci-fi color scheme
        self.colors = {
            'silent': '#003366',      # Deep blue
            'quiet': '#006699',       # Medium blue
            'normal': '#00ccff',      # Cyan
            'speaking': '#00ff99',    # Neon green
            'loud': '#ffaa00',        # Orange
            'peak': '#ff0066',        # Hot pink
            'glow': '#00ffff',        # Aqua glow
        }
        
        # Audio level tracking
        self.current_level = 0.0
        self.peak_level = 0.0
        self.peak_decay = 0.95
        self.smoothed_level = 0.0
        self.level_history = deque(maxlen=100)
        
        # Animation
        self.bars = []
        self.num_bars = 40
        self.bar_width = width // self.num_bars - 2
        self.animation_frame = 0
        self.is_speaking = False
        
        # Create initial bars
        self._create_bars()
        
        # Start animation
        self.running = True
        self.animation_thread = threading.Thread(target=self._animate, daemon=True)
        self.animation_thread.start()
    
    def _create_bars(self):
        """Create the visualization bars."""
        for i in range(self.num_bars):
            x = i * (self.bar_width + 2) + 2
            
            # Create main bar
            bar = self.canvas.create_rectangle(
                x, self.height,
                x + self.bar_width, self.height - 2,
                fill=self.colors['silent'],
                outline='',
                tags=f'bar_{i}'
            )
            
            # Create glow effect
            glow = self.canvas.create_rectangle(
                x - 1, self.height,
                x + self.bar_width + 1, self.height - 2,
                fill='',
                outline=self.colors['glow'],
                width=0,
                tags=f'glow_{i}'
            )
            
            self.bars.append({'bar': bar, 'glow': glow, 'height': 0})
    
    def update_level(self, audio_data: np.ndarray = None, energy: float = None):
        """Update audio level from audio data or energy value."""
        if audio_data is not None:
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_data ** 2))
        
        if energy is not None:
            # Store raw level
            self.current_level = min(energy * 50, 1.0)  # Scale and clamp
            self.level_history.append(self.current_level)
            
            # Update peak
            if self.current_level > self.peak_level:
                self.peak_level = self.current_level
            else:
                self.peak_level *= self.peak_decay
            
            # Smooth the level for display
            self.smoothed_level = self.smoothed_level * 0.7 + self.current_level * 0.3
    
    def set_speaking(self, is_speaking: bool):
        """Set speaking state for enhanced visualization."""
        self.is_speaking = is_speaking
    
    def _animate(self):
        """Animation loop for the visualizer."""
        while self.running:
            try:
                self.animation_frame += 1
                
                # Calculate frequency-like distribution
                base_height = self.smoothed_level * self.height
                
                for i, bar_info in enumerate(self.bars):
                    # Create wave effect
                    wave = np.sin((self.animation_frame * 0.1) + (i * 0.3))
                    
                    # Calculate bar height with wave modulation
                    if self.is_speaking:
                        # Active speaking animation
                        variation = np.sin(i * 0.5 + self.animation_frame * 0.2) * 0.3 + 0.7
                        target_height = base_height * variation * (1 + wave * 0.2)
                        
                        # Add random sparkle effect
                        if np.random.random() < self.current_level * 0.1:
                            target_height *= 1.5
                    else:
                        # Idle animation
                        target_height = base_height * (0.5 + wave * 0.5)
                    
                    # Smooth height transition
                    current_height = bar_info['height']
                    bar_info['height'] = current_height * 0.6 + target_height * 0.4
                    
                    # Clamp height
                    bar_height = max(2, min(self.height - 2, bar_info['height']))
                    
                    # Determine color based on level
                    if bar_height < self.height * 0.2:
                        color = self.colors['silent']
                        glow_width = 0
                    elif bar_height < self.height * 0.4:
                        color = self.colors['quiet']
                        glow_width = 0
                    elif bar_height < self.height * 0.6:
                        color = self.colors['normal']
                        glow_width = 1 if self.is_speaking else 0
                    elif bar_height < self.height * 0.8:
                        color = self.colors['speaking']
                        glow_width = 2 if self.is_speaking else 1
                    else:
                        # Peak level - animate color
                        if self.animation_frame % 4 < 2:
                            color = self.colors['loud']
                        else:
                            color = self.colors['peak']
                        glow_width = 3
                    
                    # Apply cyberpunk color shift when speaking
                    if self.is_speaking:
                        # Create color pulse effect
                        hue = (self.animation_frame * 2 + i * 10) % 360
                        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.8, 1.0)
                        pulse_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
                        
                        # Mix with base color
                        if bar_height > self.height * 0.5:
                            color = pulse_color
                    
                    # Get bar position
                    x1, y1, x2, y2 = self.canvas.coords(bar_info['bar'])
                    
                    # Update bar
                    self.canvas.coords(
                        bar_info['bar'],
                        x1, self.height,
                        x2, self.height - bar_height
                    )
                    self.canvas.itemconfig(bar_info['bar'], fill=color)
                    
                    # Update glow
                    if glow_width > 0:
                        self.canvas.coords(
                            bar_info['glow'],
                            x1 - 1, self.height,
                            x2 + 1, self.height - bar_height
                        )
                        self.canvas.itemconfig(
                            bar_info['glow'],
                            outline=self.colors['glow'],
                            width=glow_width
                        )
                    else:
                        self.canvas.itemconfig(bar_info['glow'], width=0)
                
                # Add peak indicator line
                if self.peak_level > 0.1:
                    peak_y = self.height - (self.peak_level * self.height)
                    
                    # Delete old peak line
                    self.canvas.delete('peak_line')
                    
                    # Draw new peak line
                    self.canvas.create_line(
                        0, peak_y,
                        self.width, peak_y,
                        fill=self.colors['peak'],
                        width=1,
                        tags='peak_line'
                    )
                
                # Update display text
                self.canvas.delete('level_text')
                if self.current_level > 0.01:
                    # Show level indicator
                    level_percent = int(self.current_level * 100)
                    status = "SPEAKING" if self.is_speaking else "DETECTING"
                    
                    self.canvas.create_text(
                        self.width - 10, 10,
                        text=f"{status}: {level_percent}%",
                        fill=self.colors['speaking'] if self.is_speaking else self.colors['normal'],
                        font=('Consolas', 10, 'bold'),
                        anchor='ne',
                        tags='level_text'
                    )
                
                time.sleep(0.03)  # ~33 FPS
                
            except Exception as e:
                print(f"[VISUALIZER] Animation error: {e}")
                time.sleep(0.1)
    
    def pack(self, **kwargs):
        """Pack the canvas widget."""
        self.canvas.pack(**kwargs)
    
    def destroy(self):
        """Clean up the visualizer."""
        self.running = False
        if self.animation_thread.is_alive():
            self.animation_thread.join(timeout=0.5)
        self.canvas.destroy()

class MiniAudioMeter:
    """Compact audio level meter for status bar."""
    
    def __init__(self, parent, width=200, height=20):
        """Initialize mini meter."""
        self.canvas = Canvas(
            parent,
            width=width,
            height=height,
            bg='#0a0a0a',
            highlightthickness=1,
            highlightbackground='#00ff99'
        )
        
        self.width = width
        self.height = height
        
        # Create meter bar
        self.meter = self.canvas.create_rectangle(
            2, 2,
            2, height - 2,
            fill='#00ff99',
            outline=''
        )
        
        # Create peak indicator
        self.peak_line = self.canvas.create_line(
            2, height // 2,
            2, height // 2,
            fill='#ff0066',
            width=2
        )
        
        self.current_level = 0
        self.peak_level = 0
    
    def update(self, level: float):
        """Update meter level."""
        self.current_level = min(level * 50, 1.0)
        
        # Update peak
        if self.current_level > self.peak_level:
            self.peak_level = self.current_level
        else:
            self.peak_level *= 0.95
        
        # Update meter bar
        bar_width = max(2, self.current_level * (self.width - 4))
        self.canvas.coords(
            self.meter,
            2, 2,
            2 + bar_width, self.height - 2
        )
        
        # Color based on level
        if self.current_level < 0.3:
            color = '#006699'
        elif self.current_level < 0.6:
            color = '#00ff99'
        elif self.current_level < 0.8:
            color = '#ffaa00'
        else:
            color = '#ff0066'
        
        self.canvas.itemconfig(self.meter, fill=color)
        
        # Update peak line
        peak_x = 2 + self.peak_level * (self.width - 4)
        self.canvas.coords(
            self.peak_line,
            peak_x, 2,
            peak_x, self.height - 2
        )
    
    def pack(self, **kwargs):
        """Pack the widget."""
        self.canvas.pack(**kwargs)

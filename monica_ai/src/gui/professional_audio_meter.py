"""
Professional Audio Level Meter for Monica AI
Broadcast-quality VU meter with proper dB scaling
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import threading
import time
from collections import deque
import math

class ProfessionalAudioMeter:
    """Professional broadcast-quality audio level meter."""
    
    def __init__(self, parent, width=400, height=100):
        """Initialize professional audio meter."""
        self.parent = parent
        self.width = width
        self.height = height
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#1a1a1a')
        
        # Title label
        self.title_label = tk.Label(
            self.frame,
            text="AUDIO LEVEL MONITOR",
            font=('Arial', 9, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        self.title_label.pack(pady=(5, 2))
        
        # Create canvas
        self.canvas = Canvas(
            self.frame,
            width=width,
            height=height,
            bg='#000000',
            highlightthickness=1,
            highlightbackground='#333333'
        )
        self.canvas.pack(padx=10, pady=5)
        
        # Professional color gradient (dB levels)
        self.color_zones = [
            (-60, -40, '#0066cc'),  # Blue: Very quiet
            (-40, -20, '#00cc66'),  # Green: Normal
            (-20, -12, '#66cc00'),  # Yellow-green: Good
            (-12, -6, '#cccc00'),   # Yellow: Caution
            (-6, -3, '#ff9900'),    # Orange: Loud
            (-3, 0, '#ff3333'),     # Red: Peak/Clipping
        ]
        
        # Level tracking
        self.current_db = -60.0
        self.peak_db = -60.0
        self.peak_hold_time = 2.0  # Hold peak for 2 seconds
        self.peak_timestamp = time.time()
        self.rms_history = deque(maxlen=30)  # RMS averaging
        self.peak_history = deque(maxlen=150)  # Peak history for graph
        
        # Meter configuration
        self.meter_segments = 50
        self.segment_spacing = 2
        self.meter_height = height * 0.4
        self.meter_y = height * 0.3
        
        # Create meter segments
        self._create_meter()
        
        # Create dB scale
        self._create_db_scale()
        
        # Status indicators
        self.status_text = self.canvas.create_text(
            10, height - 10,
            text="IDLE",
            font=('Consolas', 8),
            fill='#666666',
            anchor='sw'
        )
        
        self.level_text = self.canvas.create_text(
            width - 10, height - 10,
            text="-∞ dB",
            font=('Consolas', 10, 'bold'),
            fill='#00ff00',
            anchor='se'
        )
        
        # Animation thread
        self.running = True
        self.update_lock = threading.Lock()
        self.animation_thread = threading.Thread(target=self._animate, daemon=True)
        self.animation_thread.start()
    
    def _create_meter(self):
        """Create professional meter segments."""
        self.segments = []
        segment_width = (self.width - 20) / self.meter_segments
        
        for i in range(self.meter_segments):
            x = 10 + i * segment_width
            
            # Calculate dB value for this position
            db_value = -60 + (i / self.meter_segments) * 60
            
            # Get color for this dB level
            color = self._get_color_for_db(db_value)
            
            segment = self.canvas.create_rectangle(
                x, self.meter_y,
                x + segment_width - self.segment_spacing, 
                self.meter_y + self.meter_height,
                fill='#111111',
                outline=color,
                width=1,
                tags=f'segment_{i}'
            )
            self.segments.append({
                'id': segment,
                'db': db_value,
                'color': color,
                'lit': False
            })
    
    def _create_db_scale(self):
        """Create dB scale markings."""
        # Main dB markers
        db_marks = [0, -3, -6, -12, -20, -30, -40, -50, -60]
        
        for db in db_marks:
            # Calculate x position
            if db <= -60:
                x = 10
            else:
                x = 10 + ((db + 60) / 60) * (self.width - 20)
            
            # Draw tick mark
            self.canvas.create_line(
                x, self.meter_y - 5,
                x, self.meter_y,
                fill='#666666',
                width=1
            )
            
            # Draw label
            self.canvas.create_text(
                x, self.meter_y - 8,
                text=str(db),
                font=('Arial', 7),
                fill='#888888',
                anchor='s'
            )
    
    def _get_color_for_db(self, db):
        """Get color for a given dB level."""
        for min_db, max_db, color in self.color_zones:
            if min_db <= db <= max_db:
                return color
        return '#0066cc'  # Default to blue
    
    def update_level(self, audio_data: np.ndarray = None, level: float = None):
        """Update meter with audio data or level."""
        with self.update_lock:
            if audio_data is not None:
                # Calculate RMS
                rms = np.sqrt(np.mean(audio_data ** 2))
                
                # Calculate peak
                peak = np.max(np.abs(audio_data))
                
                # Convert to dB (avoid log(0))
                if rms > 0:
                    rms_db = 20 * np.log10(max(rms, 1e-10))
                else:
                    rms_db = -60
                
                if peak > 0:
                    peak_db = 20 * np.log10(max(peak, 1e-10))
                else:
                    peak_db = -60
                
            elif level is not None:
                # Convert linear level to dB
                if level > 0:
                    rms_db = 20 * np.log10(max(level, 1e-10))
                    peak_db = rms_db + 3  # Estimate peak as +3dB
                else:
                    rms_db = -60
                    peak_db = -60
            else:
                return
            
            # Clamp values
            rms_db = max(-60, min(0, rms_db))
            peak_db = max(-60, min(0, peak_db))
            
            # Update RMS with smoothing
            self.rms_history.append(rms_db)
            self.current_db = np.mean(self.rms_history)
            
            # Update peak with hold
            if peak_db > self.peak_db:
                self.peak_db = peak_db
                self.peak_timestamp = time.time()
            elif time.time() - self.peak_timestamp > self.peak_hold_time:
                # Decay peak
                self.peak_db *= 0.95
                if self.peak_db < -60:
                    self.peak_db = -60
            
            # Store for history graph
            self.peak_history.append(self.current_db)
    
    def _animate(self):
        """Animation loop for meter - with robust error handling."""
        while self.running:
            try:
                with self.update_lock:
                    # Update segments based on current level
                    active_segments = int((self.current_db + 60) / 60 * self.meter_segments)
                    
                    for i, segment in enumerate(self.segments):
                        should_be_lit = i < active_segments
                        
                        if should_be_lit != segment['lit']:
                            segment['lit'] = should_be_lit
                            
                            try:
                                if should_be_lit:
                                    # Light up segment
                                    color = segment['color']
                                    self.canvas.itemconfig(
                                        segment['id'],
                                        fill=color,
                                        outline=color
                                    )
                                else:
                                    # Dim segment
                                    self.canvas.itemconfig(
                                        segment['id'],
                                        fill='#111111',
                                        outline=segment['color']
                                    )
                            except Exception:
                                pass  # Skip if canvas not ready
                    
                    # Update peak indicator
                    try:
                        if self.peak_db > -60:
                            peak_x = 10 + ((self.peak_db + 60) / 60) * (self.width - 20)
                            
                            # Delete old peak line
                            self.canvas.delete('peak_indicator')
                            
                            # Draw peak line
                            peak_color = self._get_color_for_db(self.peak_db)
                            self.canvas.create_line(
                                peak_x, self.meter_y - 2,
                                peak_x, self.meter_y + self.meter_height + 2,
                                fill=peak_color,
                                width=2,
                                tags='peak_indicator'
                            )
                    except Exception:
                        pass
                    
                    # Update status
                    try:
                        if self.current_db > -3:
                            status = "CLIPPING!"
                            status_color = '#ff0000'
                        elif self.current_db > -12:
                            status = "LOUD"
                            status_color = '#ff9900'
                        elif self.current_db > -40:
                            status = "ACTIVE"
                            status_color = '#00ff00'
                        elif self.current_db > -55:
                            status = "QUIET"
                            status_color = '#0099ff'
                        else:
                            status = "SILENT"
                            status_color = '#666666'
                        
                        self.canvas.itemconfig(self.status_text, text=status, fill=status_color)
                        
                        # Update level text
                        if self.current_db <= -60:
                            level_text = "-∞ dB"
                        else:
                            level_text = f"{self.current_db:.1f} dB"
                        
                        level_color = self._get_color_for_db(self.current_db)
                        self.canvas.itemconfig(self.level_text, text=level_text, fill=level_color)
                    except Exception:
                        pass
                    
                    # Draw mini waveform history
                    try:
                        self.canvas.delete('history')
                        if len(self.peak_history) > 1:
                            points = []
                            for idx, db in enumerate(self.peak_history):
                                x = 10 + (idx / len(self.peak_history)) * (self.width - 20)
                                y = self.height - 25 - ((db + 60) / 60) * 15
                                points.extend([x, y])
                            
                            if len(points) > 4:
                                self.canvas.create_line(
                                    points,
                                    fill='#00ff99',
                                    width=1,
                                    smooth=True,
                                    tags='history'
                                )
                    except Exception:
                        pass
                
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                # Silently handle errors to prevent crashes
                time.sleep(0.1)
    
    def pack(self, **kwargs):
        """Pack the meter widget."""
        self.frame.pack(**kwargs)
    
    def destroy(self):
        """Clean up the meter."""
        self.running = False
        if self.animation_thread.is_alive():
            self.animation_thread.join(timeout=0.5)
        self.canvas.destroy()
        self.frame.destroy()

"""
Thread-Safe Audio Level Meter for Monica AI
Uses Tkinter after() for all GUI updates - NO THREADING
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import time
from collections import deque
import math


class SafeAudioMeter:
    """Thread-safe audio level meter using only after() for updates."""
    
    def __init__(self, parent, width=400, height=100):
        """Initialize safe audio meter."""
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
        self.current_db = -60.0  # Start at silent
        self.peak_db = -60.0  # Start at silent
        self.peak_hold_time = 2.0
        self.peak_timestamp = time.time()
        self.rms_history = deque([-60.0] * 10, maxlen=30)  # Pre-fill with silent values
        self.peak_history = deque([-60.0] * 10, maxlen=150)  # Pre-fill with silent values
        
        # Meter configuration
        self.meter_segments = 50
        self.segment_spacing = 2
        self.meter_height = height * 0.4
        self.meter_y = height * 0.3
        
        # Create meter segments
        self.segments = []
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
        
        # Running flag
        self.running = True
        
        # Start animation using after() - THREAD SAFE!
        self._schedule_update()
    
    def _create_meter(self):
        """Create professional meter segments."""
        segment_width = (self.width - 20) / self.meter_segments - self.segment_spacing
        
        for i in range(self.meter_segments):
            x = 10 + i * (segment_width + self.segment_spacing)
            
            # Determine color based on position (dB level)
            db_level = -60 + (i / self.meter_segments) * 60
            color = self._get_color_for_db(db_level)
            
            segment_id = self.canvas.create_rectangle(
                x, self.meter_y,
                x + segment_width, self.meter_y + self.meter_height,
                fill='#111111',
                outline=color,
                width=1
            )
            
            self.segments.append({
                'id': segment_id,
                'color': color,
                'lit': False
            })
    
    def _create_db_scale(self):
        """Create dB scale markings."""
        scale_y = self.meter_y + self.meter_height + 15
        
        db_marks = [-60, -40, -20, -12, -6, -3, 0]
        
        for db in db_marks:
            x = 10 + ((db + 60) / 60) * (self.width - 20)
            
            self.canvas.create_line(
                x, self.meter_y + self.meter_height,
                x, self.meter_y + self.meter_height + 5,
                fill='#666666'
            )
            
            self.canvas.create_text(
                x, scale_y,
                text=str(db),
                font=('Consolas', 7),
                fill='#888888',
                anchor='n'
            )
    
    def _get_color_for_db(self, db):
        """Get color for a given dB level."""
        for low, high, color in self.color_zones:
            if low <= db < high:
                return color
        return '#ff3333'
    
    def update_level(self, audio_data=None, energy=None):
        """Update meter with new audio data (called from any thread)."""
        if audio_data is not None:
            # Calculate RMS and peak from audio data
            if len(audio_data) > 0:
                # Normalize to 0-1 range if 16-bit audio
                audio_float = audio_data.astype(np.float32)
                if np.max(np.abs(audio_float)) > 1.0:
                    audio_float = audio_float / 32768.0  # 16-bit normalization
                
                rms = np.sqrt(np.mean(audio_float ** 2))
                peak = np.max(np.abs(audio_float))
                
                # Convert to dB (0 dB = full scale)
                rms_db = 20 * np.log10(max(rms, 1e-10))
                peak_db = 20 * np.log10(max(peak, 1e-10))
                
                # Clamp to -60 to 0 range
                rms_db = max(-60, min(0, rms_db))
                peak_db = max(-60, min(0, peak_db))
            else:
                rms_db = -60
                peak_db = -60
        elif energy is not None:
            # Energy is typically 0-1 range from audio manager
            # Scale appropriately for display
            if energy > 0:
                # Map energy (0-1) to dB scale (-60 to 0)
                # Use logarithmic scaling for better visual response
                rms_db = 20 * np.log10(max(energy, 1e-10))
                # Clamp to reasonable range
                rms_db = max(-60, min(0, rms_db))
            else:
                rms_db = -60
            peak_db = rms_db
        else:
            return
        
        # Update RMS with smoothing
        self.rms_history.append(rms_db)
        self.current_db = np.mean(list(self.rms_history))
        
        # Update peak with hold
        if peak_db > self.peak_db:
            self.peak_db = peak_db
            self.peak_timestamp = time.time()
        elif time.time() - self.peak_timestamp > self.peak_hold_time:
            self.peak_db *= 0.95
            if self.peak_db < -60:
                self.peak_db = -60
        
        # Store for history graph
        self.peak_history.append(self.current_db)
    
    def _schedule_update(self):
        """Schedule the next GUI update using after()."""
        if not self.running:
            return
        
        # Check if parent window exists and is not busy
        try:
            if not self.parent.winfo_exists():
                return
        except Exception:
            return
        
        self._do_update()
        
        # Schedule next update in 33ms (~30 FPS)
        try:
            self.parent.after(33, self._schedule_update)
        except Exception:
            pass  # Widget destroyed
    
    def _do_update(self):
        """Perform GUI update - ONLY called from main thread via after()."""
        if not self.running:
            return
            
        try:
            # Update segments based on current level
            active_segments = int((self.current_db + 60) / 60 * self.meter_segments)
            
            for i, segment in enumerate(self.segments):
                should_be_lit = i < active_segments
                
                if should_be_lit != segment['lit']:
                    segment['lit'] = should_be_lit
                    
                    if should_be_lit:
                        color = segment['color']
                        self.canvas.itemconfig(
                            segment['id'],
                            fill=color,
                            outline=color
                        )
                    else:
                        self.canvas.itemconfig(
                            segment['id'],
                            fill='#111111',
                            outline=segment['color']
                        )
            
            # Update peak indicator
            if self.peak_db > -60:
                peak_x = 10 + ((self.peak_db + 60) / 60) * (self.width - 20)
                
                self.canvas.delete('peak_indicator')
                
                peak_color = self._get_color_for_db(self.peak_db)
                self.canvas.create_line(
                    peak_x, self.meter_y - 2,
                    peak_x, self.meter_y + self.meter_height + 2,
                    fill=peak_color,
                    width=2,
                    tags='peak_indicator'
                )
            
            # Update status
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
            
            # Draw mini waveform history
            self.canvas.delete('history')
            if len(self.peak_history) > 1:
                points = []
                history_list = list(self.peak_history)
                for idx, db in enumerate(history_list):
                    x = 10 + (idx / len(history_list)) * (self.width - 20)
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
            pass  # Silently handle any errors
    
    def pack(self, **kwargs):
        """Pack the meter widget."""
        self.frame.pack(**kwargs)
    
    def destroy(self):
        """Clean up the meter."""
        self.running = False
        try:
            self.canvas.destroy()
            self.frame.destroy()
        except Exception:
            pass

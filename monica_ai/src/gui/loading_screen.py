"""
Animated Loading Screen for Monica AI
Shows animated logo and capabilities while loading
Monica randomly chooses her animation style each time!
"""
import tkinter as tk
from tkinter import ttk, font as tkfont
import threading
import time
import math
import random

class LoadingScreen:
    """Animated loading screen with Monica logo."""
    
    # Animation styles Monica can choose from
    ANIMATION_STYLES = [
        'mechanical',      # Original mechanical split effect
        'pulse',           # Pulsing glow effect
        'wave',            # Wave motion effect
        'matrix',          # Matrix-style digital rain
        'hologram',        # Holographic flicker
        'particles',       # Particle burst effect
        'typewriter',      # Typewriter reveal
        'glitch',          # Glitch/distortion effect
    ]
    
    def __init__(self, parent=None):
        """Initialize loading screen."""
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Monica AI - Loading")
        self.root.overrideredirect(True)  # No window decorations
        self.root.configure(bg='#0a0a0a')
        
        # Center the window
        self.root.update_idletasks()
        width = 800
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make it stay on top
        self.root.attributes('-topmost', True)
        
        # Monica chooses her animation style!
        self.animation_style = random.choice(self.ANIMATION_STYLES)
        print(f"[LOADING] Monica chose animation style: {self.animation_style}")
        
        # Animation variables
        self.animation_frame = 0
        self.capabilities_index = 0
        self.loading_progress = 0
        self.is_closing = False
        self.typewriter_index = 0
        self.particles = []
        
        # Create UI
        self._create_ui()
        
        # Start animations
        self._start_animations()
    
    def _create_ui(self):
        """Create the loading screen UI."""
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(expand=True, fill='both', padx=50, pady=30)
        
        # Logo container - slightly smaller to make room
        logo_frame = tk.Frame(main_frame, bg='#0a0a0a', height=220)
        logo_frame.pack(fill='x', pady=(30, 10))
        logo_frame.pack_propagate(False)
        
        # Create animated logo canvas
        self.logo_canvas = tk.Canvas(
            logo_frame,
            width=500,
            height=180,
            bg='#0a0a0a',
            highlightthickness=0
        )
        self.logo_canvas.pack(expand=True)
        
        # Draw initial logo
        self._draw_logo()
        
        # Capabilities text (cycles through) - LARGER and positioned HIGHER
        # This is now between the animation and the loader
        self.capability_label = tk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 22, 'italic'),  # Larger font (was 16)
            fg='#00ffaa',
            bg='#0a0a0a'
        )
        self.capability_label.pack(pady=(15, 25))  # More space, positioned higher
        
        # Progress bar container - positioned lower
        progress_frame = tk.Frame(main_frame, bg='#0a0a0a')
        progress_frame.pack(fill='x', pady=(10, 5))
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Monica.Horizontal.TProgressbar",
            background='#00ffaa',
            darkcolor='#008866',
            lightcolor='#00ffcc',
            bordercolor='#0a0a0a',
            troughcolor='#1a1a1a'
        )
        
        self.progress = ttk.Progressbar(
            progress_frame,
            style="Monica.Horizontal.TProgressbar",
            length=400,
            mode='determinate',
            maximum=100
        )
        self.progress.pack()
        
        # Loading status
        self.status_label = tk.Label(
            main_frame,
            text="Initializing Neural Networks...",
            font=('Segoe UI', 11),
            fg='#888888',
            bg='#0a0a0a'
        )
        self.status_label.pack(pady=(10, 5))
        
        # Animation style indicator (subtle)
        style_label = tk.Label(
            main_frame,
            text=f"[Sparkle] {self.animation_style.title()} Mode",
            font=('Segoe UI', 9, 'italic'),
            fg='#444444',
            bg='#0a0a0a'
        )
        style_label.pack(pady=5)
        
        # Version/Creator info
        creator_label = tk.Label(
            main_frame,
            text="Created by MJP",
            font=('Segoe UI', 9),
            fg='#555555',
            bg='#0a0a0a'
        )
        creator_label.pack(side='bottom', pady=5)
    
    def _draw_logo(self):
        """Draw the animated Monica AI logo based on chosen style."""
        self.logo_canvas.delete("all")
        
        # Center position
        cx, cy = 250, 90
        
        # Call the appropriate animation style
        if self.animation_style == 'mechanical':
            self._draw_mechanical(cx, cy)
        elif self.animation_style == 'pulse':
            self._draw_pulse(cx, cy)
        elif self.animation_style == 'wave':
            self._draw_wave(cx, cy)
        elif self.animation_style == 'matrix':
            self._draw_matrix(cx, cy)
        elif self.animation_style == 'hologram':
            self._draw_hologram(cx, cy)
        elif self.animation_style == 'particles':
            self._draw_particles(cx, cy)
        elif self.animation_style == 'typewriter':
            self._draw_typewriter(cx, cy)
        elif self.animation_style == 'glitch':
            self._draw_glitch(cx, cy)
        else:
            self._draw_mechanical(cx, cy)
    
    def _draw_mechanical(self, cx, cy):
        """Original mechanical split animation."""
        offset = math.sin(self.animation_frame * 0.1) * 3
        split_offset = abs(math.sin(self.animation_frame * 0.15)) * 5
        
        main_color = '#00ffaa'
        accent_color = '#00ff88'
        
        # Draw 'M' with mechanical split
        self.logo_canvas.create_text(
            cx - 170 - split_offset, cy + offset,
            text='M',
            font=('Arial Black', 64, 'bold'),
            fill=main_color,
            anchor='w'
        )
        
        # Mechanical line
        self.logo_canvas.create_line(
            cx - 130, cy - 30, cx - 130, cy + 30,
            fill=accent_color, width=2
        )
        
        # Draw 'onica'
        self.logo_canvas.create_text(
            cx - 110, cy,
            text='onica',
            font=('Segoe UI', 42),
            fill='#ffffff',
            anchor='w'
        )
        
        # Draw 'AI' with split
        self.logo_canvas.create_text(
            cx + 90, cy - split_offset,
            text='AI',
            font=('Arial Black', 50, 'bold'),
            fill=main_color,
            anchor='w'
        )
    
    def _draw_pulse(self, cx, cy):
        """Pulsing glow effect."""
        pulse = abs(math.sin(self.animation_frame * 0.08))
        
        # Draw glowing layers
        for i in range(5, 0, -1):
            alpha = pulse * (0.3 - i * 0.05)
            size = 48 + i * 4
            color = f'#{int(alpha*255):02x}{int(255*alpha):02x}{int(170*alpha):02x}'
            self.logo_canvas.create_text(
                cx, cy,
                text='Monica AI',
                font=('Arial Black', size, 'bold'),
                fill=color,
                anchor='center'
            )
        
        # Main text
        main_color = f'#{0:02x}{int(200 + 55*pulse):02x}{int(150 + 50*pulse):02x}'
        self.logo_canvas.create_text(
            cx, cy,
            text='Monica AI',
            font=('Arial Black', 48, 'bold'),
            fill=main_color,
            anchor='center'
        )
    
    def _draw_wave(self, cx, cy):
        """Wave motion effect - each letter moves independently."""
        text = "Monica AI"
        main_color = '#00ffaa'
        
        # Calculate starting x position
        start_x = cx - 150
        
        for i, char in enumerate(text):
            # Each letter has its own wave offset
            wave_offset = math.sin(self.animation_frame * 0.15 + i * 0.5) * 10
            
            # Color variation
            hue_shift = int(abs(math.sin(self.animation_frame * 0.1 + i * 0.3)) * 50)
            color = f'#00{200 + hue_shift:02x}{150 + hue_shift:02x}'
            
            self.logo_canvas.create_text(
                start_x + i * 35, cy + wave_offset,
                text=char,
                font=('Arial Black', 48, 'bold'),
                fill=color,
                anchor='center'
            )
    
    def _draw_matrix(self, cx, cy):
        """Matrix-style digital rain effect."""
        # Draw falling characters in background
        chars = "01"
        for i in range(15):
            x = random.randint(50, 450)
            y = (self.animation_frame * 3 + i * 40) % 200
            char = random.choice(chars)
            alpha = 1 - (y / 200)
            color = f'#00{int(100 + 100*alpha):02x}{int(50 + 50*alpha):02x}'
            self.logo_canvas.create_text(
                x, y,
                text=char,
                font=('Consolas', 14),
                fill=color
            )
        
        # Main text with glow
        self.logo_canvas.create_text(
            cx, cy,
            text='Monica AI',
            font=('Arial Black', 48, 'bold'),
            fill='#00ff00',
            anchor='center'
        )
        
        # Scanline effect
        scanline_y = (self.animation_frame * 2) % 180
        self.logo_canvas.create_line(
            0, scanline_y, 500, scanline_y,
            fill='#00ff0033', width=2
        )
    
    def _draw_hologram(self, cx, cy):
        """Holographic flicker effect."""
        # Random flicker
        flicker = random.random()
        
        # RGB split effect
        offset = int(math.sin(self.animation_frame * 0.2) * 3)
        
        # Red channel (offset left)
        if flicker > 0.1:
            self.logo_canvas.create_text(
                cx - offset, cy,
                text='Monica AI',
                font=('Arial Black', 48, 'bold'),
                fill='#ff000066',
                anchor='center'
            )
        
        # Blue channel (offset right)
        if flicker > 0.15:
            self.logo_canvas.create_text(
                cx + offset, cy,
                text='Monica AI',
                font=('Arial Black', 48, 'bold'),
                fill='#0066ff66',
                anchor='center'
            )
        
        # Main cyan/green text
        if flicker > 0.05:
            self.logo_canvas.create_text(
                cx, cy,
                text='Monica AI',
                font=('Arial Black', 48, 'bold'),
                fill='#00ffaa',
                anchor='center'
            )
        
        # Horizontal scan lines
        for y in range(0, 180, 4):
            if random.random() > 0.7:
                self.logo_canvas.create_line(
                    0, y, 500, y,
                    fill='#00ffaa11', width=1
                )
    
    def _draw_particles(self, cx, cy):
        """Particle burst effect."""
        # Update particles
        if len(self.particles) < 30:
            # Add new particle from center
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': cx,
                'y': cy,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 60,
                'size': random.randint(2, 5)
            })
        
        # Draw and update particles
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            if p['life'] > 0:
                alpha = p['life'] / 60
                color = f'#00{int(255*alpha):02x}{int(170*alpha):02x}'
                self.logo_canvas.create_oval(
                    p['x'] - p['size'], p['y'] - p['size'],
                    p['x'] + p['size'], p['y'] + p['size'],
                    fill=color, outline=''
                )
                new_particles.append(p)
        
        self.particles = new_particles
        
        # Main text
        self.logo_canvas.create_text(
            cx, cy,
            text='Monica AI',
            font=('Arial Black', 48, 'bold'),
            fill='#00ffaa',
            anchor='center'
        )
    
    def _draw_typewriter(self, cx, cy):
        """Typewriter reveal effect."""
        full_text = "Monica AI"
        
        # Increment typewriter index slowly
        if self.animation_frame % 8 == 0:
            self.typewriter_index = (self.typewriter_index + 1) % (len(full_text) + 10)
        
        # Show partial text
        visible_chars = min(self.typewriter_index, len(full_text))
        visible_text = full_text[:visible_chars]
        
        # Draw visible text
        self.logo_canvas.create_text(
            cx - 120, cy,
            text=visible_text,
            font=('Courier New', 48, 'bold'),
            fill='#00ffaa',
            anchor='w'
        )
        
        # Blinking cursor
        if self.animation_frame % 20 < 10 and visible_chars < len(full_text):
            cursor_x = cx - 120 + visible_chars * 30
            self.logo_canvas.create_text(
                cursor_x, cy,
                text='_',
                font=('Courier New', 48, 'bold'),
                fill='#00ffaa',
                anchor='w'
            )
    
    def _draw_glitch(self, cx, cy):
        """Glitch/distortion effect."""
        # Random glitch chance
        glitch = random.random() < 0.15
        
        if glitch:
            # Slice the text into horizontal strips
            for i in range(5):
                y_offset = (i - 2) * 15
                x_offset = random.randint(-20, 20) if random.random() < 0.3 else 0
                
                # Random color glitch
                colors = ['#00ffaa', '#ff00aa', '#00aaff', '#ffaa00']
                color = random.choice(colors) if random.random() < 0.2 else '#00ffaa'
                
                self.logo_canvas.create_text(
                    cx + x_offset, cy + y_offset,
                    text='Monica AI',
                    font=('Arial Black', 48, 'bold'),
                    fill=color,
                    anchor='center'
                )
        else:
            # Normal display with subtle movement
            offset = math.sin(self.animation_frame * 0.1) * 2
            self.logo_canvas.create_text(
                cx + offset, cy,
                text='Monica AI',
                font=('Arial Black', 48, 'bold'),
                fill='#00ffaa',
                anchor='center'
            )
        
        # Occasional full glitch
        if random.random() < 0.05:
            self.logo_canvas.create_rectangle(
                random.randint(0, 400), random.randint(0, 150),
                random.randint(100, 500), random.randint(20, 180),
                fill='#00ffaa', outline=''
            )
    
    def _start_animations(self):
        """Start all animations."""
        # Logo animation
        self._animate_logo()
        
        # Capabilities cycling
        self._cycle_capabilities()
        
        # Progress animation
        self._animate_progress()
    
    def _animate_logo(self):
        """Animate the logo."""
        if self.is_closing:
            return
        
        self.animation_frame += 1
        self._draw_logo()
        
        # Continue animation
        self.root.after(50, self._animate_logo)
    
    def _cycle_capabilities(self):
        """Cycle through Monica's capabilities."""
        if self.is_closing:
            return
        
        capabilities = [
            "[Brain] Psychology & Behavioral Sciences",
            "[Core] Biology & Life Sciences",
            "[Core] Philosophy & Ethics",
            "[Core] Complete K-12 Education",
            "[Core] 60+ Languages",
            "[Vision] Computer Vision",
            "[Core] Real-Time Global Cameras",
            "[Core] Advanced Mathematics",
            "[Core] Programming & Software",
            "[Art] Creative Arts",
            "[Core] Medical Knowledge",
            "[Core] Counseling & Therapy",
            "[Stats] Data Analysis",
            "[Music] Music Theory",
            "[Core] Quantum Physics",
        ]
        
        # Update capability text
        self.capability_label.config(text=capabilities[self.capabilities_index])
        
        # Fade effect
        self._fade_in_text()
        
        # Next capability
        self.capabilities_index = (self.capabilities_index + 1) % len(capabilities)
        
        # Continue cycling
        self.root.after(2000, self._cycle_capabilities)
    
    def _fade_in_text(self):
        """Create fade in effect for text."""
        colors = ['#004433', '#006644', '#008855', '#00aa77', '#00cc99', '#00ffaa']
        
        def fade(index=0):
            if index < len(colors) and not self.is_closing:
                self.capability_label.config(fg=colors[index])
                self.root.after(50, lambda: fade(index + 1))
        
        fade()
    
    def _animate_progress(self):
        """Animate the progress bar."""
        if self.is_closing:
            return
        
        # Update progress
        if self.loading_progress < 100:
            self.loading_progress += 2
            self.progress['value'] = self.loading_progress
            
            # Update status based on progress
            if self.loading_progress < 20:
                self.status_label.config(text="Initializing Neural Networks...")
            elif self.loading_progress < 40:
                self.status_label.config(text="Loading Knowledge Bases...")
            elif self.loading_progress < 60:
                self.status_label.config(text="Activating Vision System...")
            elif self.loading_progress < 80:
                self.status_label.config(text="Preparing Speech Recognition...")
            else:
                self.status_label.config(text="Monica is almost ready...")
            
            # Continue animation
            self.root.after(100, self._animate_progress)
        else:
            # Loading complete
            self.status_label.config(text="[Sparkle] Monica AI Ready!")
            self.root.after(1000, self.close)
    
    def set_progress(self, value: int, status: str = ""):
        """Set progress from external source."""
        self.loading_progress = min(value, 100)
        self.progress['value'] = self.loading_progress
        if status:
            self.status_label.config(text=status)
    
    def close(self):
        """Close the loading screen."""
        self.is_closing = True
        
        # Fade out effect
        def fade_out(alpha=1.0):
            if alpha > 0:
                self.root.attributes('-alpha', alpha)
                self.root.after(20, lambda: fade_out(alpha - 0.05))
            else:
                self.root.destroy()
        
        fade_out()

def show_loading_screen(parent=None, duration=5000):
    """Show loading screen for specified duration."""
    screen = LoadingScreen(parent)
    
    # Auto-close after duration
    if duration:
        screen.root.after(duration, screen.close)
    
    return screen

# Quick test
if __name__ == "__main__":
    screen = show_loading_screen(duration=10000)
    screen.root.mainloop()

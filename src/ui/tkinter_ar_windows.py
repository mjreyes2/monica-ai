"""
Tkinter-based AR Window Display
Replaces OpenCV windows with tkinter for Windows compatibility
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import threading
import time
from typing import Optional, Callable
import math

class TkinterARWindow:
    """Tkinter-based AR window for Windows compatibility"""
    
    def __init__(self, title: str, width: int = 600, height: int = 600):
        self.title = title
        self.width = width
        self.height = height
        self.root = None
        self.canvas = None
        self.running = False
        self.thread = None
        self.visible = False
        
    def _create_window(self):
        """Create tkinter window"""
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.configure(bg='black')
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.attributes('-topmost', False)
        
        self.canvas = Canvas(self.root, width=self.width, height=self.height, bg='green', highlightthickness=0)
        self.canvas.pack()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        
    def start(self):
        """Start window in thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
    def stop(self):
        """Stop window"""
        self.running = False
        self.visible = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def show(self):
        """Show window"""
        self.visible = True
        if not self.running:
            self.start()
        elif self.root:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.root.after(100, lambda: self.root.attributes('-topmost', False))
            except:
                pass
                
    def hide(self):
        """Hide window"""
        self.visible = False
        if self.root:
            try:
                self.root.withdraw()
            except:
                pass


class TkinterOrbWindow(TkinterARWindow):
    """Tkinter-based Orb window"""
    
    def __init__(self):
        super().__init__("Monica Orb", 500, 500)
        self.time = 0
        
    def _run_loop(self):
        """Main render loop"""
        self._create_window()
        
        def update_display():
            if not self.running or not self.root:
                return
                
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw green background
            self.canvas.configure(bg='green')
            
            # Draw animated orb
            center_x = self.width // 2
            center_y = self.height // 2
            radius = 100
            
            # Pulsing effect
            pulse = math.sin(self.time * 2) * 10
            current_radius = radius + pulse
            
            # Draw orb circles
            for i in range(5):
                r = current_radius - i * 15
                if r > 0:
                    alpha = 255 - i * 50
                    color = f'#{alpha:02x}{alpha:02x}ff'
                    self.canvas.create_oval(
                        center_x - r, center_y - r,
                        center_x + r, center_y + r,
                        outline=color, width=2
                    )
            
            # Draw center glow
            self.canvas.create_oval(
                center_x - 20, center_y - 20,
                center_x + 20, center_y + 20,
                fill='white', outline='cyan', width=2
            )
            
            self.time += 0.05
            
            # Schedule next update
            if self.running:
                self.root.after(50, update_display)  # 20 FPS
        
        update_display()
        
        # Start tkinter main loop
        try:
            self.root.mainloop()
        except:
            pass


class TkinterGlobeWindow(TkinterARWindow):
    """Tkinter-based Globe window"""
    
    def __init__(self):
        super().__init__("Monica Globe", 600, 600)
        self.rotation = 0
        
    def _run_loop(self):
        """Main render loop"""
        self._create_window()
        
        def update_display():
            if not self.running or not self.root:
                return
                
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw green background
            self.canvas.configure(bg='green')
            
            # Draw globe
            center_x = self.width // 2
            center_y = self.height // 2
            radius = 150
            
            # Draw globe outline
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline='white', width=2
            )
            
            # Draw rotating lines
            for i in range(8):
                angle = self.rotation + i * math.pi / 4
                x1 = center_x + radius * 0.9 * math.cos(angle)
                y1 = center_y + radius * 0.3 * math.sin(angle)
                x2 = center_x - radius * 0.9 * math.cos(angle)
                y2 = center_y - radius * 0.3 * math.sin(angle)
                
                self.canvas.create_line(x1, y1, x2, y2, fill='cyan', width=1)
            
            # Draw horizontal lines
            for i in range(-2, 3):
                y = center_y + i * radius * 0.3
                x_offset = math.sqrt(max(0, radius**2 - (i * radius * 0.3)**2))
                self.canvas.create_line(
                    center_x - x_offset, y,
                    center_x + x_offset, y,
                    fill='cyan', width=1
                )
            
            self.rotation += 0.02
            
            # Schedule next update
            if self.running:
                self.root.after(50, update_display)  # 20 FPS
        
        update_display()
        
        # Start tkinter main loop
        try:
            self.root.mainloop()
        except:
            pass


class TkinterKeyboardWindow(TkinterARWindow):
    """Tkinter-based Keyboard window"""
    
    def __init__(self):
        super().__init__("Monica Keyboard", 800, 300)
        self.typed_text = ""
        
    def _run_loop(self):
        """Main render loop"""
        self._create_window()
        
        def update_display():
            if not self.running or not self.root:
                return
                
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw green background
            self.canvas.configure(bg='green')
            
            # Draw keyboard keys
            keys = "QWERTYUIOPASDFGHJKLZXCVBNM"
            key_width = 40
            key_height = 40
            start_x = 50
            start_y = 50
            
            # First row
            for i, key in enumerate(keys[:10]):
                x = start_x + i * (key_width + 5)
                y = start_y
                self.canvas.create_rectangle(
                    x, y, x + key_width, y + key_height,
                    fill='black', outline='white', width=2
                )
                self.canvas.create_text(
                    x + key_width//2, y + key_height//2,
                    text=key, fill='white', font=('Arial', 12, 'bold')
                )
            
            # Second row
            for i, key in enumerate(keys[10:19]):
                x = start_x + 30 + i * (key_width + 5)
                y = start_y + key_height + 10
                self.canvas.create_rectangle(
                    x, y, x + key_width, y + key_height,
                    fill='black', outline='white', width=2
                )
                self.canvas.create_text(
                    x + key_width//2, y + key_height//2,
                    text=key, fill='white', font=('Arial', 12, 'bold')
                )
            
            # Third row
            for i, key in enumerate(keys[19:]):
                x = start_x + 60 + i * (key_width + 5)
                y = start_y + 2 * (key_height + 10)
                self.canvas.create_rectangle(
                    x, y, x + key_width, y + key_height,
                    fill='black', outline='white', width=2
                )
                self.canvas.create_text(
                    x + key_width//2, y + key_height//2,
                    text=key, fill='white', font=('Arial', 12, 'bold')
                )
            
            # Draw typed text
            self.canvas.create_rectangle(
                50, start_y + 3 * (key_height + 10) + 10,
                750, start_y + 3 * (key_height + 10) + 40,
                fill='black', outline='white', width=2
            )
            self.canvas.create_text(
                60, start_y + 3 * (key_height + 10) + 25,
                text=self.typed_text[-30:], fill='lime', 
                font=('Courier', 14), anchor='w'
            )
            
            # Schedule next update
            if self.running:
                self.root.after(100, update_display)  # 10 FPS
        
        update_display()
        
        # Start tkinter main loop
        try:
            self.root.mainloop()
        except:
            pass


class TkinterDialWindow(TkinterARWindow):
    """Tkinter-based Dial window"""
    
    def __init__(self):
        super().__init__("Monica Dial", 400, 400)
        self.value = 0.5
        self.rotation = 0
        
    def _run_loop(self):
        """Main render loop"""
        self._create_window()
        
        def update_display():
            if not self.running or not self.root:
                return
                
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw green background
            self.canvas.configure(bg='green')
            
            # Draw dial
            center_x = self.width // 2
            center_y = self.height // 2
            radius = 120
            
            # Draw outer circle
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline='white', width=3
            )
            
            # Draw inner circle
            self.canvas.create_oval(
                center_x - radius * 0.8, center_y - radius * 0.8,
                center_x + radius * 0.8, center_y + radius * 0.8,
                outline='cyan', width=2
            )
            
            # Draw tick marks
            for i in range(12):
                angle = i * math.pi / 6
                x1 = center_x + radius * 0.9 * math.cos(angle)
                y1 = center_y + radius * 0.9 * math.sin(angle)
                x2 = center_x + radius * 0.7 * math.cos(angle)
                y2 = center_y + radius * 0.7 * math.sin(angle)
                
                self.canvas.create_line(x1, y1, x2, y2, fill='white', width=2)
            
            # Draw needle
            needle_angle = self.rotation + self.value * math.pi * 1.5 - math.pi * 0.75
            needle_x = center_x + radius * 0.8 * math.cos(needle_angle)
            needle_y = center_y + radius * 0.8 * math.sin(needle_angle)
            
            self.canvas.create_line(
                center_x, center_y, needle_x, needle_y,
                fill='red', width=4, capstyle='round'
            )
            
            # Draw center
            self.canvas.create_oval(
                center_x - 10, center_y - 10,
                center_x + 10, center_y + 10,
                fill='black', outline='white', width=2
            )
            
            # Draw value text
            self.canvas.create_text(
                center_x, center_y + radius + 30,
                text=f"Value: {self.value:.2f}", fill='white',
                font=('Arial', 12, 'bold')
            )
            
            self.rotation += 0.01
            
            # Schedule next update
            if self.running:
                self.root.after(50, update_display)  # 20 FPS
        
        update_display()
        
        # Start tkinter main loop
        try:
            self.root.mainloop()
        except:
            pass

"""
Simple Window Display for Monica AR Windows
Uses tkinter for better Windows compatibility instead of OpenCV
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import threading
import time
from typing import Optional, Callable

class SimpleDisplayWindow:
    """Simple window using tkinter to display AR content"""
    
    def __init__(self, title: str, width: int = 600, height: int = 600):
        self.title = title
        self.width = width
        self.height = height
        self.root = None
        self.canvas = None
        self.running = False
        self.thread = None
        self.update_callback = None
        
    def set_update_callback(self, callback: Callable):
        """Set callback to generate frames"""
        self.update_callback = callback
        
    def _create_window(self):
        """Create tkinter window in main thread"""
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
        
    def _run_loop(self):
        """Main render loop"""
        self._create_window()
        
        def update_display():
            if not self.running or not self.root:
                return
                
            # Get frame from callback if available
            if self.update_callback:
                frame = self.update_callback()
                if frame is not None:
                    # Convert numpy array to PhotoImage
                    try:
                        from PIL import Image, ImageTk
                        # Convert BGR to RGB
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(rgb_frame)
                        photo = ImageTk.PhotoImage(image=img)
                        
                        # Update canvas
                        self.canvas.delete("all")
                        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                        self.canvas.image = photo  # Keep reference
                    except:
                        # Fallback to green screen
                        self.canvas.configure(bg='green')
            
            # Schedule next update
            if self.running:
                self.root.after(16, update_display)  # ~60 FPS
        
        update_display()
        
        # Start tkinter main loop
        try:
            self.root.mainloop()
        except:
            pass
            
    def start(self):
        """Start window in thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
    def stop(self):
        """Stop window"""
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def bring_to_front(self):
        """Bring window to front"""
        if self.root:
            try:
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.root.after(100, lambda: self.root.attributes('-topmost', False))
            except:
                pass

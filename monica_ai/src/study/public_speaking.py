"""
Monica Public Speaking Auditorium
A virtual auditorium for practicing public speaking with AI feedback.
Monica watches and listens to your presentation and provides detailed feedback.

Author: Monica AI
Date: December 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import cv2
from PIL import Image, ImageTk
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Try to import camera
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


@dataclass
class SpeechMetrics:
    """Metrics for a speech/presentation."""
    duration_seconds: float = 0
    word_count: int = 0
    words_per_minute: float = 0
    filler_words: int = 0
    pauses: int = 0
    questions_asked: int = 0
    eye_contact_score: float = 0  # 0-100
    volume_consistency: float = 0  # 0-100
    pace_consistency: float = 0  # 0-100


@dataclass
class SpeechFeedback:
    """Feedback for a speech/presentation."""
    overall_score: float  # 0-100
    strengths: List[str]
    improvements: List[str]
    detailed_feedback: str
    metrics: SpeechMetrics


# Filler words to detect
FILLER_WORDS = [
    'um', 'uh', 'er', 'ah', 'like', 'you know', 'basically', 'actually',
    'literally', 'so', 'well', 'right', 'okay', 'i mean', 'sort of', 'kind of'
]

# Speech topics for practice
SPEECH_TOPICS = {
    'impromptu': [
        "The most important lesson I've learned",
        "If I could change one thing about the world",
        "My favorite place and why",
        "A person who inspires me",
        "The best advice I've ever received",
        "What success means to me",
        "A challenge I overcame",
        "Why [hobby] is important to me",
        "The future of technology",
        "What makes a good leader",
    ],
    'persuasive': [
        "Why everyone should learn a second language",
        "The importance of mental health awareness",
        "Why we should reduce screen time",
        "The benefits of reading books",
        "Why voting matters",
        "The case for renewable energy",
        "Why arts education is essential",
        "The importance of financial literacy",
    ],
    'informative': [
        "How [technology] works",
        "The history of [topic]",
        "Understanding [scientific concept]",
        "The process of [skill]",
        "Key facts about [subject]",
    ],
    'storytelling': [
        "A time when I failed and what I learned",
        "My most memorable experience",
        "A turning point in my life",
        "The day everything changed",
        "An unexpected friendship",
    ]
}


class PublicSpeakingAuditorium:
    """
    Virtual auditorium for public speaking practice.
    """
    
    def __init__(self, parent=None, ai_manager=None, speech_recognizer=None):
        self.parent = parent
        self.ai_manager = ai_manager
        self.speech_recognizer = speech_recognizer
        
        # Session state
        self.is_recording = False
        self.start_time = None
        self.transcript = []
        self.current_topic = None
        self.metrics = SpeechMetrics()
        
        # Camera
        self.camera = None
        self.camera_active = False
        
        # Create window
        self.window = None
        self._create_window()
    
    def _create_window(self):
        """Create the auditorium window."""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()
        
        self.window.title("[Mic] Monica Public Speaking Auditorium")
        self.window.geometry("1200x800")
        self.window.configure(bg='#1a1a2e')
        
        # Create layout
        self._create_header()
        self._create_main_area()
        self._create_controls()
        self._create_feedback_panel()
        
        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_header(self):
        """Create header with title and topic."""
        header = tk.Frame(self.window, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Title
        tk.Label(header, text="[Mic] Public Speaking Auditorium",
                font=('Segoe UI', 20, 'bold'), bg='#16213e', fg='white').pack(side=tk.LEFT, padx=20, pady=20)
        
        # Topic display
        self.topic_label = tk.Label(header, text="Select a topic or speak freely",
                                   font=('Segoe UI', 12), bg='#16213e', fg='#888')
        self.topic_label.pack(side=tk.RIGHT, padx=20)
    
    def _create_main_area(self):
        """Create main area with camera view and audience."""
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Camera/Stage
        stage_frame = tk.Frame(main_frame, bg='#0f0f23', width=700)
        stage_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        stage_frame.pack_propagate(False)
        
        # Stage label
        tk.Label(stage_frame, text="[*] Your Stage",
                font=('Segoe UI', 14, 'bold'), bg='#0f0f23', fg='white').pack(pady=10)
        
        # Camera view
        self.camera_frame = tk.Frame(stage_frame, bg='#000', width=640, height=480)
        self.camera_frame.pack(pady=10)
        self.camera_frame.pack_propagate(False)
        
        self.camera_label = tk.Label(self.camera_frame, bg='#000',
                                    text="[Camera] Camera will appear here\nClick 'Start Camera' to begin",
                                    fg='#666', font=('Segoe UI', 12))
        self.camera_label.pack(expand=True)
        
        # Timer
        self.timer_label = tk.Label(stage_frame, text="00:00",
                                   font=('Consolas', 24, 'bold'), bg='#0f0f23', fg='#4CAF50')
        self.timer_label.pack(pady=10)
        
        # Right side - Audience visualization
        audience_frame = tk.Frame(main_frame, bg='#16213e', width=400)
        audience_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        audience_frame.pack_propagate(False)
        
        tk.Label(audience_frame, text="[*] Virtual Audience",
                font=('Segoe UI', 14, 'bold'), bg='#16213e', fg='white').pack(pady=10)
        
        # Audience canvas (visual representation)
        self.audience_canvas = tk.Canvas(audience_frame, bg='#1a1a2e', 
                                        width=380, height=300, highlightthickness=0)
        self.audience_canvas.pack(pady=10)
        self._draw_audience()
        
        # Monica's live feedback
        tk.Label(audience_frame, text="[*] Monica's Notes",
                font=('Segoe UI', 12, 'bold'), bg='#16213e', fg='white').pack(pady=(20, 5))
        
        self.live_feedback = scrolledtext.ScrolledText(
            audience_frame, bg='#0f0f23', fg='#aaa',
            font=('Segoe UI', 10), height=8, width=45, wrap=tk.WORD
        )
        self.live_feedback.pack(padx=10, pady=5)
        self.live_feedback.insert(tk.END, "I'm ready to watch your presentation!\n\nTips:\n• Speak clearly and at a steady pace\n• Make eye contact with the camera\n• Use gestures naturally\n• Avoid filler words like 'um' and 'uh'\n\nClick 'Start Presentation' when ready!")
    
    def _draw_audience(self):
        """Draw virtual audience on canvas."""
        canvas = self.audience_canvas
        canvas.delete("all")
        
        # Draw rows of audience members (simple circles)
        colors = ['#4a4a6a', '#3a3a5a', '#2a2a4a']
        
        for row in range(3):
            y = 50 + row * 90
            num_people = 8 - row * 2
            spacing = 380 / (num_people + 1)
            
            for i in range(num_people):
                x = spacing * (i + 1)
                # Head
                canvas.create_oval(x-15, y-15, x+15, y+15, 
                                  fill=colors[row], outline='')
                # Body
                canvas.create_oval(x-20, y+10, x+20, y+50,
                                  fill=colors[row], outline='')
        
        # Monica in the front
        canvas.create_oval(170, 250, 210, 290, fill='#e94560', outline='#fff', width=2)
        canvas.create_text(190, 310, text="Monica", fill='#e94560', font=('Segoe UI', 10, 'bold'))
    
    def _create_controls(self):
        """Create control buttons."""
        controls = tk.Frame(self.window, bg='#1a1a2e')
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        # Left controls
        left_controls = tk.Frame(controls, bg='#1a1a2e')
        left_controls.pack(side=tk.LEFT)
        
        self.camera_btn = tk.Button(left_controls, text="[Camera] Start Camera",
                                   command=self._toggle_camera,
                                   bg='#3498db', fg='white', font=('Segoe UI', 11),
                                   padx=15, pady=8)
        self.camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.record_btn = tk.Button(left_controls, text="[Mic] Start Presentation",
                                   command=self._toggle_recording,
                                   bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
                                   padx=20, pady=8)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Topic selection
        tk.Label(left_controls, text="Topic:", bg='#1a1a2e', fg='white',
                font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=(20, 5))
        
        self.topic_var = tk.StringVar(value="Free Speech")
        topic_menu = ttk.Combobox(left_controls, textvariable=self.topic_var,
                                 values=["Free Speech", "Random Impromptu", "Random Persuasive",
                                        "Random Storytelling", "Custom Topic..."],
                                 width=20, state='readonly')
        topic_menu.pack(side=tk.LEFT, padx=5)
        topic_menu.bind('<<ComboboxSelected>>', self._on_topic_change)
        
        # Right controls
        right_controls = tk.Frame(controls, bg='#1a1a2e')
        right_controls.pack(side=tk.RIGHT)
        
        tk.Button(right_controls, text="[Stats] Get Feedback",
                 command=self._get_feedback,
                 bg='#9b59b6', fg='white', font=('Segoe UI', 11),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(right_controls, text="[Refresh] New Session",
                 command=self._new_session,
                 bg='#e67e22', fg='white', font=('Segoe UI', 11),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
    
    def _create_feedback_panel(self):
        """Create feedback panel at bottom."""
        feedback_frame = tk.Frame(self.window, bg='#16213e', height=150)
        feedback_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        feedback_frame.pack_propagate(False)
        
        # Transcript
        left_panel = tk.Frame(feedback_frame, bg='#16213e')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(left_panel, text="[Note] Live Transcript",
                font=('Segoe UI', 11, 'bold'), bg='#16213e', fg='white').pack(anchor=tk.W)
        
        self.transcript_text = scrolledtext.ScrolledText(
            left_panel, bg='#0f0f23', fg='#ddd',
            font=('Segoe UI', 10), height=5, wrap=tk.WORD
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Metrics
        right_panel = tk.Frame(feedback_frame, bg='#16213e', width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        right_panel.pack_propagate(False)
        
        tk.Label(right_panel, text="[Stats] Live Metrics",
                font=('Segoe UI', 11, 'bold'), bg='#16213e', fg='white').pack(anchor=tk.W)
        
        metrics_frame = tk.Frame(right_panel, bg='#16213e')
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.wpm_label = tk.Label(metrics_frame, text="WPM: --",
                                 font=('Consolas', 11), bg='#16213e', fg='#4CAF50')
        self.wpm_label.pack(anchor=tk.W)
        
        self.words_label = tk.Label(metrics_frame, text="Words: 0",
                                   font=('Consolas', 11), bg='#16213e', fg='#2196F3')
        self.words_label.pack(anchor=tk.W)
        
        self.filler_label = tk.Label(metrics_frame, text="Fillers: 0",
                                    font=('Consolas', 11), bg='#16213e', fg='#FF9800')
        self.filler_label.pack(anchor=tk.W)
    
    def _toggle_camera(self):
        """Toggle camera on/off."""
        if self.camera_active:
            self._stop_camera()
        else:
            self._start_camera()
    
    def _start_camera(self):
        """Start the camera."""
        if not HAS_CV2:
            messagebox.showerror("Error", "OpenCV not available for camera")
            return
        
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                return
            
            self.camera_active = True
            self.camera_btn.config(text="[Camera] Stop Camera", bg='#e74c3c')
            
            # Start camera thread
            threading.Thread(target=self._camera_loop, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {e}")
    
    def _stop_camera(self):
        """Stop the camera."""
        self.camera_active = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_btn.config(text="[Camera] Start Camera", bg='#3498db')
        self.camera_label.config(image='', text="[Camera] Camera stopped")
    
    def _camera_loop(self):
        """Camera capture loop."""
        while self.camera_active and self.camera:
            ret, frame = self.camera.read()
            if ret:
                # Flip horizontally (mirror)
                frame = cv2.flip(frame, 1)
                
                # Convert to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to fit
                frame_rgb = cv2.resize(frame_rgb, (640, 480))
                
                # Convert to PhotoImage
                img = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image=img)
                
                # Update label
                self.camera_label.config(image=photo, text='')
                self.camera_label.image = photo
            
            time.sleep(0.033)  # ~30 FPS
    
    def _toggle_recording(self):
        """Toggle presentation recording."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start recording the presentation."""
        self.is_recording = True
        self.start_time = time.time()
        self.transcript = []
        self.metrics = SpeechMetrics()
        
        self.record_btn.config(text="⏹ Stop Presentation", bg='#e74c3c')
        
        # Clear transcript
        self.transcript_text.delete('1.0', tk.END)
        
        # Update live feedback
        self.live_feedback.delete('1.0', tk.END)
        self.live_feedback.insert(tk.END, "[Mic] Recording started!\n\nI'm listening and watching...\n")
        
        # Start timer thread
        threading.Thread(target=self._timer_loop, daemon=True).start()
        
        # Start speech recognition if available
        if self.speech_recognizer:
            threading.Thread(target=self._speech_loop, daemon=True).start()
    
    def _stop_recording(self):
        """Stop recording the presentation."""
        self.is_recording = False
        
        # Calculate final metrics
        if self.start_time:
            self.metrics.duration_seconds = time.time() - self.start_time
            if self.metrics.duration_seconds > 0:
                self.metrics.words_per_minute = (self.metrics.word_count / self.metrics.duration_seconds) * 60
        
        self.record_btn.config(text="[Mic] Start Presentation", bg='#27ae60')
        
        # Update feedback
        self.live_feedback.insert(tk.END, "\n\n[OK] Presentation complete!\nClick 'Get Feedback' for detailed analysis.")
    
    def _timer_loop(self):
        """Update timer display."""
        while self.is_recording:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            time.sleep(1)
    
    def _speech_loop(self):
        """Listen for speech and transcribe."""
        # This would integrate with the speech recognizer
        # For now, we'll simulate with placeholder
        pass
    
    def _add_transcript(self, text: str):
        """Add text to transcript and analyze."""
        self.transcript.append(text)
        
        # Update transcript display
        self.transcript_text.insert(tk.END, text + " ")
        self.transcript_text.see(tk.END)
        
        # Count words
        words = text.split()
        self.metrics.word_count += len(words)
        self.words_label.config(text=f"Words: {self.metrics.word_count}")
        
        # Check for filler words
        text_lower = text.lower()
        for filler in FILLER_WORDS:
            if filler in text_lower:
                self.metrics.filler_words += text_lower.count(filler)
        self.filler_label.config(text=f"Fillers: {self.metrics.filler_words}")
        
        # Update WPM
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                wpm = (self.metrics.word_count / elapsed) * 60
                self.wpm_label.config(text=f"WPM: {wpm:.0f}")
    
    def _on_topic_change(self, event=None):
        """Handle topic selection change."""
        selection = self.topic_var.get()
        
        if selection == "Free Speech":
            self.current_topic = None
            self.topic_label.config(text="Speak about anything you'd like")
        
        elif "Random" in selection:
            category = selection.replace("Random ", "").lower()
            if category in SPEECH_TOPICS:
                import random
                topic = random.choice(SPEECH_TOPICS[category])
                self.current_topic = topic
                self.topic_label.config(text=f"Topic: {topic}")
        
        elif selection == "Custom Topic...":
            # Show dialog for custom topic
            topic = tk.simpledialog.askstring("Custom Topic", "Enter your topic:")
            if topic:
                self.current_topic = topic
                self.topic_label.config(text=f"Topic: {topic}")
    
    def _get_feedback(self):
        """Get detailed feedback on the presentation."""
        if not self.transcript and self.metrics.word_count == 0:
            messagebox.showinfo("No Data", "No presentation recorded yet. Start a presentation first!")
            return
        
        # Generate feedback
        feedback = self._generate_feedback()
        
        # Show feedback window
        self._show_feedback_window(feedback)
    
    def _generate_feedback(self) -> SpeechFeedback:
        """Generate detailed feedback."""
        strengths = []
        improvements = []
        
        # Analyze metrics
        wpm = self.metrics.words_per_minute
        
        if 120 <= wpm <= 150:
            strengths.append("Excellent speaking pace (120-150 WPM)")
        elif wpm < 100:
            improvements.append("Try speaking a bit faster - aim for 120-150 WPM")
        elif wpm > 180:
            improvements.append("Try slowing down a bit - you're speaking quite fast")
        
        # Filler words
        filler_ratio = self.metrics.filler_words / max(self.metrics.word_count, 1) * 100
        if filler_ratio < 2:
            strengths.append("Very few filler words - great job!")
        elif filler_ratio > 5:
            improvements.append(f"Try to reduce filler words (you used {self.metrics.filler_words})")
        
        # Duration
        duration_min = self.metrics.duration_seconds / 60
        if duration_min >= 2:
            strengths.append(f"Good presentation length ({duration_min:.1f} minutes)")
        else:
            improvements.append("Try to speak for at least 2 minutes for better practice")
        
        # Generate AI feedback if available
        detailed = ""
        if self.ai_manager and self.transcript:
            transcript_text = " ".join(self.transcript)
            prompt = f"""Analyze this speech transcript and provide constructive feedback:

Topic: {self.current_topic or 'Free speech'}
Duration: {self.metrics.duration_seconds:.0f} seconds
Words: {self.metrics.word_count}
WPM: {self.metrics.words_per_minute:.0f}
Filler words: {self.metrics.filler_words}

Transcript:
{transcript_text[:2000]}

Provide feedback on:
1. Content and structure
2. Clarity of message
3. Engagement level
4. Specific suggestions for improvement

Be encouraging but constructive. Keep it to 4-5 sentences."""

            try:
                detailed = self.ai_manager.get_response(prompt)
            except:
                detailed = "Great effort! Keep practicing to improve your public speaking skills."
        else:
            detailed = "Great effort! Keep practicing to improve your public speaking skills."
        
        # Calculate overall score
        score = 70  # Base score
        score += min(len(strengths) * 10, 20)
        score -= min(len(improvements) * 5, 15)
        score = max(0, min(100, score))
        
        return SpeechFeedback(
            overall_score=score,
            strengths=strengths,
            improvements=improvements,
            detailed_feedback=detailed,
            metrics=self.metrics
        )
    
    def _show_feedback_window(self, feedback: SpeechFeedback):
        """Show feedback in a new window."""
        fb_window = tk.Toplevel(self.window)
        fb_window.title("[Stats] Presentation Feedback")
        fb_window.geometry("600x500")
        fb_window.configure(bg='#1a1a2e')
        
        # Score
        score_frame = tk.Frame(fb_window, bg='#16213e')
        score_frame.pack(fill=tk.X, padx=20, pady=20)
        
        score_color = '#27ae60' if feedback.overall_score >= 70 else '#e67e22' if feedback.overall_score >= 50 else '#e74c3c'
        
        tk.Label(score_frame, text=f"{feedback.overall_score:.0f}",
                font=('Segoe UI', 48, 'bold'), bg='#16213e', fg=score_color).pack()
        tk.Label(score_frame, text="Overall Score",
                font=('Segoe UI', 14), bg='#16213e', fg='#888').pack()
        
        # Metrics
        metrics_frame = tk.Frame(fb_window, bg='#1a1a2e')
        metrics_frame.pack(fill=tk.X, padx=20)
        
        metrics_text = f"Duration: {feedback.metrics.duration_seconds/60:.1f} min | Words: {feedback.metrics.word_count} | WPM: {feedback.metrics.words_per_minute:.0f} | Fillers: {feedback.metrics.filler_words}"
        tk.Label(metrics_frame, text=metrics_text,
                font=('Segoe UI', 11), bg='#1a1a2e', fg='#aaa').pack()
        
        # Strengths
        if feedback.strengths:
            tk.Label(fb_window, text="[OK] Strengths",
                    font=('Segoe UI', 14, 'bold'), bg='#1a1a2e', fg='#27ae60').pack(anchor=tk.W, padx=20, pady=(20, 5))
            for s in feedback.strengths:
                tk.Label(fb_window, text=f"  • {s}",
                        font=('Segoe UI', 11), bg='#1a1a2e', fg='#ddd').pack(anchor=tk.W, padx=20)
        
        # Improvements
        if feedback.improvements:
            tk.Label(fb_window, text="[*] Areas for Improvement",
                    font=('Segoe UI', 14, 'bold'), bg='#1a1a2e', fg='#e67e22').pack(anchor=tk.W, padx=20, pady=(20, 5))
            for i in feedback.improvements:
                tk.Label(fb_window, text=f"  • {i}",
                        font=('Segoe UI', 11), bg='#1a1a2e', fg='#ddd').pack(anchor=tk.W, padx=20)
        
        # Detailed feedback
        tk.Label(fb_window, text="[*] Monica's Feedback",
                font=('Segoe UI', 14, 'bold'), bg='#1a1a2e', fg='#3498db').pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        feedback_text = scrolledtext.ScrolledText(fb_window, bg='#16213e', fg='#ddd',
                                                  font=('Segoe UI', 11), height=6, wrap=tk.WORD)
        feedback_text.pack(fill=tk.X, padx=20, pady=5)
        feedback_text.insert(tk.END, feedback.detailed_feedback)
        feedback_text.config(state=tk.DISABLED)
        
        # Close button
        tk.Button(fb_window, text="Close", command=fb_window.destroy,
                 bg='#3498db', fg='white', font=('Segoe UI', 11),
                 padx=20, pady=8).pack(pady=20)
    
    def _new_session(self):
        """Start a new session."""
        self.transcript = []
        self.metrics = SpeechMetrics()
        self.current_topic = None
        
        self.transcript_text.delete('1.0', tk.END)
        self.timer_label.config(text="00:00")
        self.wpm_label.config(text="WPM: --")
        self.words_label.config(text="Words: 0")
        self.filler_label.config(text="Fillers: 0")
        self.topic_label.config(text="Select a topic or speak freely")
        
        self.live_feedback.delete('1.0', tk.END)
        self.live_feedback.insert(tk.END, "New session started!\n\nReady for your next presentation.")
    
    def _on_close(self):
        """Handle window close."""
        self._stop_camera()
        self.is_recording = False
        self.window.destroy()
    
    def run(self):
        """Run the auditorium."""
        if self.parent is None:
            self.window.mainloop()


def open_auditorium(parent=None, ai_manager=None) -> PublicSpeakingAuditorium:
    """Open the public speaking auditorium."""
    return PublicSpeakingAuditorium(parent, ai_manager)


# Test
if __name__ == "__main__":
    auditorium = PublicSpeakingAuditorium()
    auditorium.run()

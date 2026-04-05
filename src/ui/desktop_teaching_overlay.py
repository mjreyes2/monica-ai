"""
Monica AI - Desktop Teaching Overlay System
Captures the user's desktop, highlights areas to click, and provides
step-by-step guided instruction overlays.

Features:
- Screen capture of user's desktop
- Highlight rectangles/circles on areas to click
- Step-by-step tutorial rendering with arrows and callouts
- Works as a transparent overlay window (tkinter Toplevel)
- Integrates with Monica's AI to generate teaching context
"""
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger("Monica.DesktopTeacher")

# Screen capture
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import tkinter as tk
    HAS_TK = True
except ImportError:
    HAS_TK = False


@dataclass
class TeachingStep:
    """A single step in a teaching lesson."""
    step_number: int
    title: str
    instruction: str
    highlight_region: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    highlight_type: str = "rectangle"  # rectangle, circle, arrow
    arrow_target: Optional[Tuple[int, int]] = None  # (x, y) for arrow tip
    explanation: str = ""
    keyboard_shortcut: str = ""
    completed: bool = False


@dataclass
class Lesson:
    """A complete teaching lesson."""
    title: str
    subject: str
    difficulty: str = "beginner"
    steps: List[TeachingStep] = field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0

    def __post_init__(self):
        self.total_steps = len(self.steps)


class DesktopTeachingOverlay:
    """
    Creates a transparent overlay on top of the desktop to highlight
    UI elements and guide the user through tutorials.
    """

    def __init__(self):
        self.is_active = False
        self.current_lesson: Optional[Lesson] = None
        self.overlay_window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.info_window: Optional[tk.Toplevel] = None
        self._root: Optional[tk.Tk] = None
        self._screen_w = 1920
        self._screen_h = 1080
        self._lesson_library = self._build_lesson_library()
        logger.info("DesktopTeachingOverlay initialized")

    def _build_lesson_library(self) -> Dict[str, List[Lesson]]:
        """Build the built-in lesson library."""
        return {
            "programming": self._programming_lessons(),
            "computer_science": self._cs_lessons(),
            "python_basics": self._python_lessons(),
            "web_development": self._web_dev_lessons(),
            "windows_basics": self._windows_lessons(),
        }

    def set_root(self, root: tk.Tk):
        """Set the tkinter root for creating overlay windows."""
        self._root = root
        try:
            self._screen_w = root.winfo_screenwidth()
            self._screen_h = root.winfo_screenheight()
        except Exception:
            pass

    def start_lesson(self, lesson: Lesson):
        """Start a teaching lesson with overlay."""
        self.current_lesson = lesson
        self.current_lesson.current_step = 0
        self.is_active = True
        self._show_current_step()
        logger.info(f"Started lesson: {lesson.title} ({lesson.total_steps} steps)")

    def start_lesson_by_name(self, category: str, index: int = 0):
        """Start a lesson from the built-in library by category name."""
        lessons = self._lesson_library.get(category, [])
        if lessons and index < len(lessons):
            self.start_lesson(lessons[index])
            return True
        return False

    def next_step(self):
        """Advance to the next step."""
        if not self.current_lesson:
            return
        if self.current_lesson.current_step < self.current_lesson.total_steps - 1:
            step = self.current_lesson.steps[self.current_lesson.current_step]
            step.completed = True
            self.current_lesson.current_step += 1
            self._show_current_step()
        else:
            self._complete_lesson()

    def prev_step(self):
        """Go back to the previous step."""
        if not self.current_lesson or self.current_lesson.current_step <= 0:
            return
        self.current_lesson.current_step -= 1
        self._show_current_step()

    def stop_lesson(self):
        """Stop the current lesson and hide overlay."""
        self.is_active = False
        self.current_lesson = None
        self._hide_overlay()
        self._hide_info()

    def capture_screen(self) -> Optional[Image.Image]:
        """Capture the current desktop screen."""
        if not HAS_PIL:
            return None
        try:
            return ImageGrab.grab()
        except Exception as e:
            logger.warning(f"Screen capture failed: {e}")
            return None

    def get_lesson_categories(self) -> List[str]:
        """Get available lesson categories."""
        return list(self._lesson_library.keys())

    def get_lessons_in_category(self, category: str) -> List[Dict[str, str]]:
        """Get lesson summaries in a category."""
        lessons = self._lesson_library.get(category, [])
        return [{"title": l.title, "subject": l.subject, "difficulty": l.difficulty,
                 "steps": l.total_steps} for l in lessons]

    def _show_current_step(self):
        """Render the current teaching step."""
        if not self.current_lesson:
            return
        step = self.current_lesson.steps[self.current_lesson.current_step]
        self._show_info_panel(step)
        if step.highlight_region:
            self._show_highlight(step)

    def _show_info_panel(self, step: TeachingStep):
        """Show the instruction panel for the current step."""
        if not HAS_TK or not self._root:
            return

        if self.info_window and self.info_window.winfo_exists():
            self.info_window.destroy()

        self.info_window = tk.Toplevel(self._root)
        self.info_window.title("Monica Teaching")
        self.info_window.geometry(f"480x340+{self._screen_w - 510}+50")
        self.info_window.configure(bg="#0a0a2e")
        self.info_window.attributes("-topmost", True)
        self.info_window.resizable(False, False)

        # Header
        header = tk.Frame(self.info_window, bg="#16213e", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        lesson_title = self.current_lesson.title if self.current_lesson else "Lesson"
        tk.Label(header, text=f"[BOOKS] {lesson_title}",
                 bg="#16213e", fg="#00d4ff", font=("Segoe UI", 12, "bold")).pack(
            side=tk.LEFT, padx=10, pady=10)

        progress = f"Step {step.step_number}/{self.current_lesson.total_steps}" if self.current_lesson else ""
        tk.Label(header, text=progress,
                 bg="#16213e", fg="#00ff88", font=("Segoe UI", 10)).pack(
            side=tk.RIGHT, padx=10, pady=10)

        # Step title
        tk.Label(self.info_window, text=step.title,
                 bg="#0a0a2e", fg="#ffffff", font=("Segoe UI", 11, "bold"),
                 wraplength=440, justify=tk.LEFT).pack(
            anchor=tk.W, padx=15, pady=(10, 5))

        # Instruction
        instr_frame = tk.Frame(self.info_window, bg="#111133", bd=1, relief=tk.SOLID)
        instr_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(instr_frame, text=step.instruction,
                 bg="#111133", fg="#e0e0e0", font=("Segoe UI", 10),
                 wraplength=430, justify=tk.LEFT).pack(padx=10, pady=8)

        # Keyboard shortcut (if any)
        if step.keyboard_shortcut:
            tk.Label(self.info_window,
                     text=f" Shortcut: {step.keyboard_shortcut}",
                     bg="#0a0a2e", fg="#ffcc00", font=("Segoe UI", 10)).pack(
                anchor=tk.W, padx=15, pady=(2, 0))

        # Explanation
        if step.explanation:
            tk.Label(self.info_window, text=step.explanation,
                     bg="#0a0a2e", fg="#aaaaaa", font=("Segoe UI", 9),
                     wraplength=440, justify=tk.LEFT).pack(
                anchor=tk.W, padx=15, pady=(5, 0))

        # Navigation buttons
        btn_frame = tk.Frame(self.info_window, bg="#0a0a2e")
        btn_frame.pack(fill=tk.X, padx=15, pady=10, side=tk.BOTTOM)

        tk.Button(btn_frame, text="◀ Previous", bg="#16213e", fg="#00d4ff",
                  activebackground="#1a1a4e", font=("Segoe UI", 10), relief=tk.FLAT,
                  command=self.prev_step).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame, text="Next ▶", bg="#16213e", fg="#00ff88",
                  activebackground="#1a1a4e", font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                  command=self.next_step).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame, text=" Stop", bg="#3e1616", fg="#ff4444",
                  activebackground="#4e1a1a", font=("Segoe UI", 10), relief=tk.FLAT,
                  command=self.stop_lesson).pack(side=tk.RIGHT)

    def _show_highlight(self, step: TeachingStep):
        """Show a highlight overlay on the screen region."""
        if not HAS_TK or not self._root or not step.highlight_region:
            return

        x, y, w, h = step.highlight_region

        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()

        self.overlay_window = tk.Toplevel(self._root)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.attributes("-topmost", True)

        pad = 6
        self.overlay_window.geometry(f"{w + pad*2}x{h + pad*2}+{x - pad}+{y - pad}")

        try:
            self.overlay_window.attributes("-transparentcolor", "black")
            self.overlay_window.configure(bg="black")
        except Exception:
            self.overlay_window.attributes("-alpha", 0.4)
            self.overlay_window.configure(bg="yellow")

        canvas = tk.Canvas(self.overlay_window, bg="black",
                           highlightthickness=0, width=w + pad*2, height=h + pad*2)
        canvas.pack(fill=tk.BOTH, expand=True)

        if step.highlight_type == "circle":
            canvas.create_oval(pad, pad, w + pad, h + pad,
                               outline="#00ff88", width=3)
        else:
            canvas.create_rectangle(pad, pad, w + pad, h + pad,
                                    outline="#00ff88", width=3)
            # Pulsing corners
            for cx, cy in [(pad, pad), (w+pad, pad), (pad, h+pad), (w+pad, h+pad)]:
                canvas.create_rectangle(cx-4, cy-4, cx+4, cy+4,
                                        fill="#00ff88", outline="")

    def _hide_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None

    def _hide_info(self):
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.destroy()
            self.info_window = None

    def _complete_lesson(self):
        """Called when all steps are done."""
        if self.current_lesson:
            self.current_lesson.steps[-1].completed = True
        self._hide_overlay()
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.destroy()

        if HAS_TK and self._root:
            self.info_window = tk.Toplevel(self._root)
            self.info_window.title("Lesson Complete!")
            self.info_window.geometry("400x200+500+300")
            self.info_window.configure(bg="#0a2e0a")
            self.info_window.attributes("-topmost", True)
            tk.Label(self.info_window, text="[PARTY] Lesson Complete!",
                     bg="#0a2e0a", fg="#00ff88", font=("Segoe UI", 16, "bold")).pack(pady=20)
            title = self.current_lesson.title if self.current_lesson else "Lesson"
            tk.Label(self.info_window, text=f"You finished: {title}",
                     bg="#0a2e0a", fg="#e0e0e0", font=("Segoe UI", 11)).pack(pady=5)
            tk.Button(self.info_window, text="Close", bg="#16213e", fg="#00d4ff",
                      font=("Segoe UI", 11), relief=tk.FLAT,
                      command=self.stop_lesson).pack(pady=15)
        self.is_active = False

    # ========== LESSON LIBRARIES ==========

    def _programming_lessons(self) -> List[Lesson]:
        return [Lesson(
            title="Introduction to Programming Concepts",
            subject="programming",
            difficulty="beginner",
            steps=[
                TeachingStep(1, "What is Programming?",
                    "Programming is giving instructions to a computer in a language it understands. "
                    "Just like you follow a recipe to cook, a computer follows your code to perform tasks.",
                    explanation="Computers are very fast but very literal — they do exactly what you tell them, nothing more."),
                TeachingStep(2, "Variables — Storing Information",
                    "A variable is like a labeled box that holds data.\n\n"
                    "Example in Python:\n  name = 'Monica'\n  age = 25\n  is_ai = True",
                    explanation="Variables can hold text (strings), numbers (int/float), or true/false (boolean)."),
                TeachingStep(3, "Data Types",
                    "Every piece of data has a type:\n"
                    "- str — text: 'hello'\n"
                    "- int — whole numbers: 42\n"
                    "- float — decimals: 3.14\n"
                    "- bool — True or False\n"
                    "- list — ordered collection: [1, 2, 3]\n"
                    "- dict — key-value pairs: {'name': 'Monica'}",
                    explanation="Python automatically detects the type. Use type(x) to check."),
                TeachingStep(4, "Conditional Logic (if/else)",
                    "Computers make decisions using conditions:\n\n"
                    "temperature = 85\n"
                    "if temperature > 80:\n"
                    "    print('It is hot!')\n"
                    "elif temperature > 60:\n"
                    "    print('Nice weather')\n"
                    "else:\n"
                    "    print('It is cold')",
                    explanation="Indentation matters in Python! Use 4 spaces for each level."),
                TeachingStep(5, "Loops — Repeating Actions",
                    "Loops let you repeat code:\n\n"
                    "# For loop — known iterations\n"
                    "for i in range(5):\n"
                    "    print(i)  # prints 0,1,2,3,4\n\n"
                    "# While loop — until condition is false\n"
                    "count = 0\n"
                    "while count < 5:\n"
                    "    print(count)\n"
                    "    count += 1",
                    explanation="Be careful with while loops — make sure the condition eventually becomes False!"),
                TeachingStep(6, "Functions — Reusable Code Blocks",
                    "Functions let you package code for reuse:\n\n"
                    "def greet(name):\n"
                    "    return f'Hello, {name}!'\n\n"
                    "result = greet('Marvin')\n"
                    "print(result)  # Hello, Marvin!",
                    explanation="Functions take parameters (inputs) and can return values (outputs). DRY = Don't Repeat Yourself."),
                TeachingStep(7, "Practice: Your First Program",
                    "Open any text editor and type:\n\n"
                    "name = input('What is your name? ')\n"
                    "print(f'Hello, {name}! Welcome to programming!')\n\n"
                    "Save as hello.py and run: python hello.py",
                    keyboard_shortcut="Ctrl+S to save"),
            ]
        )]

    def _cs_lessons(self) -> List[Lesson]:
        return [Lesson(
            title="Computer Science Fundamentals",
            subject="computer_science",
            difficulty="beginner",
            steps=[
                TeachingStep(1, "How Computers Work",
                    "A computer has 4 main components:\n"
                    "- CPU — the 'brain' that executes instructions\n"
                    "- RAM — fast temporary memory (lost when powered off)\n"
                    "- Storage — permanent memory (SSD/HDD)\n"
                    "- I/O — input (keyboard, mouse) and output (screen, speakers)",
                    explanation="Everything a computer does is: INPUT → PROCESS → OUTPUT"),
                TeachingStep(2, "Binary — The Language of Computers",
                    "Computers only understand 0s and 1s (binary).\n"
                    "Each digit is a 'bit'. 8 bits = 1 byte.\n\n"
                    "Examples:\n"
                    "  0 = 0000  |  5 = 0101\n"
                    "  1 = 0001  |  8 = 1000\n"
                    "  3 = 0011  | 15 = 1111\n\n"
                    "Text is encoded: A=65, B=66, a=97 (ASCII).",
                    explanation="1 KB = 1024 bytes, 1 MB = 1024 KB, 1 GB = 1024 MB"),
                TeachingStep(3, "Algorithms & Big O Notation",
                    "An algorithm is a step-by-step procedure to solve a problem.\n\n"
                    "Big O measures efficiency:\n"
                    "- O(1) — constant time (instant lookup)\n"
                    "- O(log n) — binary search\n"
                    "- O(n) — linear search\n"
                    "- O(n log n) — efficient sorting (merge sort)\n"
                    "- O(n²) — bubble sort (slow for large data)",
                    explanation="Always aim for the lowest Big O possible for better performance."),
                TeachingStep(4, "Data Structures",
                    "How we organize data:\n"
                    "- Array/List — ordered, indexed: [1,2,3]\n"
                    "- Stack — LIFO (last in, first out) like a stack of plates\n"
                    "- Queue — FIFO (first in, first out) like a line\n"
                    "- Hash Table/Dict — key→value, O(1) lookup\n"
                    "- Tree — hierarchical (file system, DOM)\n"
                    "- Graph — nodes + edges (social networks, maps)",
                    explanation="Choosing the right data structure is 80% of solving any problem."),
                TeachingStep(5, "Networking Basics",
                    "The Internet works on layers:\n"
                    "- IP Address — unique computer identifier (192.168.1.1)\n"
                    "- DNS — translates names to IPs (google.com → 142.250.x.x)\n"
                    "- HTTP/HTTPS — web communication protocol\n"
                    "- TCP/IP — reliable data delivery\n"
                    "- Ports — different services (80=HTTP, 443=HTTPS, 22=SSH)",
                    explanation="When you visit a website: DNS lookup → TCP connection → HTTP request → response"),
                TeachingStep(6, "Operating Systems",
                    "The OS manages all hardware and software:\n"
                    "- Process Management — running programs\n"
                    "- Memory Management — allocating RAM\n"
                    "- File System — organizing files on disk\n"
                    "- Device Drivers — talking to hardware\n"
                    "- Security — user accounts, permissions\n\n"
                    "Major OSes: Windows, macOS, Linux, Android, iOS",
                    explanation="Your programs run ON TOP of the OS. The OS is the middleman between your code and hardware."),
            ]
        )]

    def _python_lessons(self) -> List[Lesson]:
        return [Lesson(
            title="Python Programming — From Zero to Hero",
            subject="python",
            difficulty="beginner",
            steps=[
                TeachingStep(1, "Setting Up Python",
                    "Check if Python is installed:\n"
                    "Open Command Prompt and type: python --version\n\n"
                    "If not installed, download from python.org\n"
                    "Make sure to check 'Add Python to PATH' during install!",
                    keyboard_shortcut="Win+R, type 'cmd', press Enter"),
                TeachingStep(2, "Python REPL — Interactive Mode",
                    "Type 'python' in cmd to enter interactive mode:\n\n"
                    ">>> 2 + 2\n4\n>>> 'Hello' + ' World'\n'Hello World'\n"
                    ">>> len('Monica')\n6\n>>> type(42)\n<class 'int'>\n\n"
                    "Type exit() to leave.",
                    explanation="The REPL (Read-Eval-Print Loop) is great for quick experiments."),
                TeachingStep(3, "Lists and List Comprehensions",
                    "Lists are Python's most versatile data structure:\n\n"
                    "fruits = ['apple', 'banana', 'cherry']\n"
                    "fruits.append('date')  # add to end\n"
                    "fruits[0]  # 'apple' (zero-indexed!)\n"
                    "fruits[-1]  # 'date' (last item)\n\n"
                    "# List comprehension — powerful one-liner\n"
                    "squares = [x**2 for x in range(10)]\n"
                    "# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]",
                    explanation="Lists are mutable (can be changed). Tuples are immutable."),
                TeachingStep(4, "Dictionaries — Key-Value Storage",
                    "Dictionaries map keys to values:\n\n"
                    "person = {\n"
                    "    'name': 'Marvin',\n"
                    "    'age': 30,\n"
                    "    'skills': ['Python', 'AI']\n"
                    "}\n"
                    "person['name']  # 'Marvin'\n"
                    "person.get('email', 'N/A')  # safe access\n"
                    "person['city'] = 'Miami'  # add new key",
                    explanation="Dicts are O(1) lookup — extremely fast. Use them for structured data."),
                TeachingStep(5, "Error Handling (try/except)",
                    "Gracefully handle errors:\n\n"
                    "try:\n"
                    "    result = 10 / 0\n"
                    "except ZeroDivisionError:\n"
                    "    print('Cannot divide by zero!')\n"
                    "except Exception as e:\n"
                    "    print(f'Error: {e}')\n"
                    "finally:\n"
                    "    print('This always runs')",
                    explanation="Never let your program crash silently. Always handle expected errors."),
                TeachingStep(6, "Classes and OOP",
                    "Object-Oriented Programming:\n\n"
                    "class Dog:\n"
                    "    def __init__(self, name, breed):\n"
                    "        self.name = name\n"
                    "        self.breed = breed\n\n"
                    "    def bark(self):\n"
                    "        return f'{self.name} says Woof!'\n\n"
                    "rex = Dog('Rex', 'German Shepherd')\n"
                    "print(rex.bark())  # Rex says Woof!",
                    explanation="OOP lets you model real-world things as objects with properties and behaviors."),
                TeachingStep(7, "File I/O",
                    "Reading and writing files:\n\n"
                    "# Write\n"
                    "with open('notes.txt', 'w') as f:\n"
                    "    f.write('Hello from Python!')\n\n"
                    "# Read\n"
                    "with open('notes.txt', 'r') as f:\n"
                    "    content = f.read()\n"
                    "    print(content)\n\n"
                    "# JSON\n"
                    "import json\n"
                    "data = json.loads('{\"key\": \"value\"}')",
                    explanation="Always use 'with' for files — it automatically closes the file."),
                TeachingStep(8, "pip & External Libraries",
                    "Install packages with pip:\n\n"
                    "pip install requests\n"
                    "pip install numpy pandas matplotlib\n\n"
                    "Then use them:\n"
                    "import requests\n"
                    "response = requests.get('https://api.github.com')\n"
                    "print(response.json())",
                    keyboard_shortcut="pip list — see installed packages"),
            ]
        )]

    def _web_dev_lessons(self) -> List[Lesson]:
        return [Lesson(
            title="Web Development Basics",
            subject="web_development",
            difficulty="beginner",
            steps=[
                TeachingStep(1, "HTML — The Structure",
                    "HTML defines the structure of a webpage:\n\n"
                    "<!DOCTYPE html>\n"
                    "<html>\n"
                    "<head><title>My Page</title></head>\n"
                    "<body>\n"
                    "  <h1>Hello World</h1>\n"
                    "  <p>This is a paragraph.</p>\n"
                    "  <a href='https://example.com'>Link</a>\n"
                    "</body>\n"
                    "</html>",
                    explanation="HTML uses tags (<tag>) to define elements. Most tags have an opening and closing tag."),
                TeachingStep(2, "CSS — The Style",
                    "CSS controls how HTML looks:\n\n"
                    "body { font-family: Arial; background: #1a1a2e; color: white; }\n"
                    "h1 { color: #00d4ff; font-size: 2em; }\n"
                    ".highlight { background: yellow; padding: 5px; }\n"
                    "#header { display: flex; justify-content: space-between; }",
                    explanation="CSS selectors: element (h1), class (.highlight), id (#header)"),
                TeachingStep(3, "JavaScript — The Behavior",
                    "JavaScript makes pages interactive:\n\n"
                    "// Variables\n"
                    "let count = 0;\n"
                    "const name = 'Monica';\n\n"
                    "// Function\n"
                    "function greet(who) {\n"
                    "    return `Hello, ${who}!`;\n"
                    "}\n\n"
                    "// DOM manipulation\n"
                    "document.getElementById('btn').addEventListener('click', () => {\n"
                    "    count++;\n"
                    "    document.getElementById('output').textContent = count;\n"
                    "});",
                    explanation="HTML = skeleton, CSS = clothing, JavaScript = muscles and brain."),
                TeachingStep(4, "Developer Tools (F12)",
                    "Every browser has Developer Tools:\n\n"
                    "- Elements tab — inspect/edit HTML & CSS live\n"
                    "- Console tab — run JavaScript, see errors\n"
                    "- Network tab — see all HTTP requests\n"
                    "- Sources tab — debug JavaScript\n"
                    "- Application tab — cookies, localStorage",
                    keyboard_shortcut="F12 or Ctrl+Shift+I to open DevTools"),
            ]
        )]

    def _windows_lessons(self) -> List[Lesson]:
        return [Lesson(
            title="Windows Power User Tips",
            subject="windows",
            difficulty="beginner",
            steps=[
                TeachingStep(1, "Essential Keyboard Shortcuts",
                    "Master these shortcuts:\n"
                    "- Win+E — Open File Explorer\n"
                    "- Win+D — Show Desktop\n"
                    "- Win+L — Lock Screen\n"
                    "- Win+Tab — Task View\n"
                    "- Alt+Tab — Switch Windows\n"
                    "- Ctrl+Shift+Esc — Task Manager\n"
                    "- Win+. — Emoji Picker\n"
                    "- Win+V — Clipboard History",
                    keyboard_shortcut="Try Win+E right now!"),
                TeachingStep(2, "Command Prompt & PowerShell",
                    "Open PowerShell (Win+X, then I):\n\n"
                    "dir — list files\n"
                    "cd folder — change directory\n"
                    "mkdir newdir — create folder\n"
                    "type file.txt — display file\n"
                    "ipconfig — network info\n"
                    "ping google.com — test connectivity\n"
                    "tasklist — running processes",
                    keyboard_shortcut="Win+X opens Power User menu"),
                TeachingStep(3, "File Explorer Tips",
                    "- Address bar — type a path directly\n"
                    "- Quick Access — pin frequent folders\n"
                    "- Search — type in the search box (top right)\n"
                    "- Preview pane — Alt+P to toggle\n"
                    "- New tab — Ctrl+T (Windows 11)\n"
                    "- Copy path — Ctrl+Shift+C",
                    keyboard_shortcut="Ctrl+L to select the address bar"),
            ]
        )]


# Singleton
_desktop_teacher = None


def get_desktop_teacher() -> DesktopTeachingOverlay:
    global _desktop_teacher
    if _desktop_teacher is None:
        _desktop_teacher = DesktopTeachingOverlay()
    return _desktop_teacher

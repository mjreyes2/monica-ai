"""
Monica Quiz and Test System
Interactive quizzes and tests for learning with grading and mistake tracking.

Author: Monica AI
Date: December 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import random
import time
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"


@dataclass
class Question:
    """Represents a quiz/test question."""
    id: str
    question: str
    question_type: QuestionType
    correct_answer: str
    options: List[str] = field(default_factory=list)  # For multiple choice
    explanation: str = ""
    subject: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    points: int = 1


@dataclass
class QuizResult:
    """Result of a quiz/test."""
    quiz_id: str
    subject: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score_percentage: float
    time_taken: float  # seconds
    date: str
    mistakes: List[Dict] = field(default_factory=list)  # Questions answered wrong


class QuizGenerator:
    """
    Generates quizzes and tests for various subjects.
    """
    
    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager
        
        # Question banks by subject
        self.question_banks = self._init_question_banks()
    
    def _init_question_banks(self) -> Dict[str, List[Question]]:
        """Initialize built-in question banks."""
        return {
            'mathematics': self._math_questions(),
            'reading': self._reading_questions(),
            'grammar': self._grammar_questions(),
            'vocabulary': self._vocabulary_questions(),
            'literature': self._literature_questions(),
            'python': self._python_questions(),
            'javascript': self._javascript_questions(),
            'general_coding': self._coding_questions(),
        }
    
    def _math_questions(self) -> List[Question]:
        """Mathematics questions."""
        questions = []
        
        # Basic arithmetic
        questions.extend([
            Question("math_1", "What is 15 × 12?", QuestionType.MULTIPLE_CHOICE,
                    "180", ["160", "170", "180", "190"], 
                    "15 × 12 = 15 × 10 + 15 × 2 = 150 + 30 = 180", "mathematics", "easy"),
            Question("math_2", "What is 144 ÷ 12?", QuestionType.MULTIPLE_CHOICE,
                    "12", ["10", "11", "12", "14"],
                    "144 ÷ 12 = 12 because 12 × 12 = 144", "mathematics", "easy"),
            Question("math_3", "What is 25% of 80?", QuestionType.MULTIPLE_CHOICE,
                    "20", ["15", "20", "25", "30"],
                    "25% = 1/4, so 80 ÷ 4 = 20", "mathematics", "easy"),
        ])
        
        # Algebra
        questions.extend([
            Question("math_4", "Solve for x: 2x + 5 = 15", QuestionType.MULTIPLE_CHOICE,
                    "5", ["3", "4", "5", "6"],
                    "2x + 5 = 15 → 2x = 10 → x = 5", "mathematics", "medium"),
            Question("math_5", "What is the value of x² when x = 7?", QuestionType.MULTIPLE_CHOICE,
                    "49", ["42", "47", "49", "56"],
                    "7² = 7 × 7 = 49", "mathematics", "easy"),
            Question("math_6", "Simplify: 3(x + 4) - 2x", QuestionType.MULTIPLE_CHOICE,
                    "x + 12", ["x + 4", "x + 12", "5x + 4", "5x + 12"],
                    "3x + 12 - 2x = x + 12", "mathematics", "medium"),
        ])
        
        # Geometry
        questions.extend([
            Question("math_7", "What is the area of a rectangle with length 8 and width 5?",
                    QuestionType.MULTIPLE_CHOICE, "40", ["13", "26", "40", "80"],
                    "Area = length × width = 8 × 5 = 40", "mathematics", "easy"),
            Question("math_8", "How many degrees are in a triangle?", QuestionType.MULTIPLE_CHOICE,
                    "180", ["90", "180", "270", "360"],
                    "The sum of angles in a triangle is always 180°", "mathematics", "easy"),
            Question("math_9", "What is the circumference of a circle with radius 7? (Use π ≈ 22/7)",
                    QuestionType.MULTIPLE_CHOICE, "44", ["22", "44", "154", "308"],
                    "C = 2πr = 2 × 22/7 × 7 = 44", "mathematics", "medium"),
        ])
        
        # Fractions
        questions.extend([
            Question("math_10", "What is 1/2 + 1/4?", QuestionType.MULTIPLE_CHOICE,
                    "3/4", ["1/4", "2/4", "3/4", "1"],
                    "1/2 = 2/4, so 2/4 + 1/4 = 3/4", "mathematics", "easy"),
            Question("math_11", "What is 3/5 as a decimal?", QuestionType.MULTIPLE_CHOICE,
                    "0.6", ["0.35", "0.53", "0.6", "0.65"],
                    "3 ÷ 5 = 0.6", "mathematics", "easy"),
        ])
        
        return questions
    
    def _reading_questions(self) -> List[Question]:
        """Reading comprehension questions."""
        return [
            Question("read_1", "What is the main idea of a paragraph?",
                    QuestionType.MULTIPLE_CHOICE,
                    "The central point the author is making",
                    ["The first sentence", "The last sentence", 
                     "The central point the author is making", "A random detail"],
                    "The main idea is the central message or point of a text.",
                    "reading", "easy"),
            Question("read_2", "What does 'inference' mean in reading?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Drawing conclusions from evidence in the text",
                    ["Copying text exactly", "Drawing conclusions from evidence in the text",
                     "Skipping difficult words", "Reading out loud"],
                    "Inference means using clues in the text to understand unstated information.",
                    "reading", "medium"),
            Question("read_3", "What is a 'theme' in literature?",
                    QuestionType.MULTIPLE_CHOICE,
                    "The underlying message or lesson",
                    ["The setting of the story", "The main character",
                     "The underlying message or lesson", "The plot summary"],
                    "Theme is the central idea or message that the author conveys.",
                    "reading", "medium"),
        ]
    
    def _grammar_questions(self) -> List[Question]:
        """Grammar questions."""
        return [
            Question("gram_1", "Which sentence is correct?",
                    QuestionType.MULTIPLE_CHOICE,
                    "She and I went to the store.",
                    ["Me and her went to the store.", "Her and me went to the store.",
                     "She and I went to the store.", "Her and I went to the store."],
                    "Use subject pronouns (I, she) as subjects of sentences.",
                    "grammar", "medium"),
            Question("gram_2", "Choose the correct word: 'Their/There/They're going to the park.'",
                    QuestionType.MULTIPLE_CHOICE,
                    "They're",
                    ["Their", "There", "They're", "Theyre"],
                    "They're = They are. Their = possession. There = location.",
                    "grammar", "easy"),
            Question("gram_3", "Which is correct: 'affect' or 'effect'? 'The rain will ___ the game.'",
                    QuestionType.MULTIPLE_CHOICE,
                    "affect",
                    ["affect", "effect", "either", "neither"],
                    "Affect is usually a verb (to influence). Effect is usually a noun (result).",
                    "grammar", "medium"),
            Question("gram_4", "Identify the error: 'Everyone should bring their own lunch.'",
                    QuestionType.MULTIPLE_CHOICE,
                    "Subject-verb agreement (everyone is singular)",
                    ["No error", "Subject-verb agreement (everyone is singular)",
                     "Wrong punctuation", "Spelling error"],
                    "Traditionally, 'everyone' takes singular pronouns, though 'their' is now widely accepted.",
                    "grammar", "hard"),
            Question("gram_5", "Which sentence uses the comma correctly?",
                    QuestionType.MULTIPLE_CHOICE,
                    "After the movie, we went to dinner.",
                    ["After the movie we went to dinner.", "After, the movie we went to dinner.",
                     "After the movie, we went to dinner.", "After the movie we, went to dinner."],
                    "Use a comma after introductory phrases.",
                    "grammar", "medium"),
        ]
    
    def _vocabulary_questions(self) -> List[Question]:
        """Vocabulary questions."""
        return [
            Question("vocab_1", "What does 'ubiquitous' mean?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Present everywhere",
                    ["Very rare", "Present everywhere", "Extremely loud", "Highly intelligent"],
                    "Ubiquitous means existing or being everywhere at the same time.",
                    "vocabulary", "hard"),
            Question("vocab_2", "What is a synonym for 'benevolent'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Kind",
                    ["Cruel", "Kind", "Lazy", "Angry"],
                    "Benevolent means well-meaning and kindly.",
                    "vocabulary", "medium"),
            Question("vocab_3", "What does 'ephemeral' mean?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Lasting for a very short time",
                    ["Lasting forever", "Lasting for a very short time", "Very beautiful", "Extremely large"],
                    "Ephemeral means lasting for a very short time.",
                    "vocabulary", "hard"),
            Question("vocab_4", "What is the antonym of 'verbose'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Concise",
                    ["Wordy", "Concise", "Loud", "Quiet"],
                    "Verbose means using more words than needed. Concise is the opposite.",
                    "vocabulary", "medium"),
        ]
    
    def _literature_questions(self) -> List[Question]:
        """Literature questions."""
        return [
            Question("lit_1", "Who wrote 'Romeo and Juliet'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "William Shakespeare",
                    ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
                    "Shakespeare wrote Romeo and Juliet around 1594-1596.",
                    "literature", "easy"),
            Question("lit_2", "What is the setting of '1984' by George Orwell?",
                    QuestionType.MULTIPLE_CHOICE,
                    "A dystopian future London",
                    ["Victorian England", "A dystopian future London", "Ancient Rome", "Modern New York"],
                    "1984 is set in a totalitarian future version of London.",
                    "literature", "medium"),
            Question("lit_3", "Who is the author of 'Pride and Prejudice'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Jane Austen",
                    ["Emily Bronte", "Jane Austen", "Virginia Woolf", "Mary Shelley"],
                    "Jane Austen published Pride and Prejudice in 1813.",
                    "literature", "easy"),
            Question("lit_4", "What literary device is 'The wind whispered through the trees'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Personification",
                    ["Simile", "Metaphor", "Personification", "Alliteration"],
                    "Personification gives human qualities to non-human things.",
                    "literature", "medium"),
        ]
    
    def _python_questions(self) -> List[Question]:
        """Python programming questions."""
        return [
            Question("py_1", "What is the output of: print(type([]))?",
                    QuestionType.MULTIPLE_CHOICE,
                    "<class 'list'>",
                    ["<class 'dict'>", "<class 'list'>", "<class 'tuple'>", "<class 'set'>"],
                    "[] creates an empty list in Python.",
                    "python", "easy"),
            Question("py_2", "How do you create a function in Python?",
                    QuestionType.MULTIPLE_CHOICE,
                    "def function_name():",
                    ["function function_name():", "def function_name():", 
                     "create function_name():", "func function_name():"],
                    "Python uses 'def' keyword to define functions.",
                    "python", "easy"),
            Question("py_3", "What does 'len()' do in Python?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Returns the length of an object",
                    ["Returns the length of an object", "Creates a new list",
                     "Converts to integer", "Prints output"],
                    "len() returns the number of items in a sequence or collection.",
                    "python", "easy"),
            Question("py_4", "What is the result of: 5 // 2?",
                    QuestionType.MULTIPLE_CHOICE,
                    "2",
                    ["2", "2.5", "3", "2.0"],
                    "// is floor division, which rounds down to the nearest integer.",
                    "python", "medium"),
            Question("py_5", "Which is the correct way to create a dictionary?",
                    QuestionType.MULTIPLE_CHOICE,
                    "{'key': 'value'}",
                    ["['key': 'value']", "{'key': 'value'}", "('key': 'value')", "<'key': 'value'>"],
                    "Dictionaries use curly braces {} with key: value pairs.",
                    "python", "easy"),
        ]
    
    def _javascript_questions(self) -> List[Question]:
        """JavaScript programming questions."""
        return [
            Question("js_1", "How do you declare a constant in JavaScript?",
                    QuestionType.MULTIPLE_CHOICE,
                    "const",
                    ["var", "let", "const", "constant"],
                    "const declares a constant that cannot be reassigned.",
                    "javascript", "easy"),
            Question("js_2", "What is the output of: typeof null?",
                    QuestionType.MULTIPLE_CHOICE,
                    "object",
                    ["null", "undefined", "object", "number"],
                    "This is a known quirk in JavaScript - typeof null returns 'object'.",
                    "javascript", "medium"),
            Question("js_3", "How do you write a comment in JavaScript?",
                    QuestionType.MULTIPLE_CHOICE,
                    "// comment",
                    ["# comment", "// comment", "<!-- comment -->", "** comment **"],
                    "JavaScript uses // for single-line comments and /* */ for multi-line.",
                    "javascript", "easy"),
            Question("js_4", "What does '===' mean in JavaScript?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Strict equality (value and type)",
                    ["Assignment", "Loose equality", "Strict equality (value and type)", "Not equal"],
                    "=== checks both value and type, while == only checks value.",
                    "javascript", "medium"),
        ]
    
    def _coding_questions(self) -> List[Question]:
        """General coding questions."""
        return [
            Question("code_1", "What does 'DRY' stand for in programming?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Don't Repeat Yourself",
                    ["Do Repeat Yourself", "Don't Repeat Yourself", 
                     "Data Retrieval Yield", "Dynamic Runtime Yield"],
                    "DRY is a principle to reduce repetition in code.",
                    "general_coding", "easy"),
            Question("code_2", "What is a 'loop' in programming?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Code that repeats until a condition is met",
                    ["A type of variable", "Code that repeats until a condition is met",
                     "A function call", "A data structure"],
                    "Loops execute code repeatedly based on conditions.",
                    "general_coding", "easy"),
            Question("code_3", "What is 'debugging'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Finding and fixing errors in code",
                    ["Writing new code", "Finding and fixing errors in code",
                     "Deleting code", "Copying code"],
                    "Debugging is the process of identifying and removing bugs.",
                    "general_coding", "easy"),
            Question("code_4", "What is an 'API'?",
                    QuestionType.MULTIPLE_CHOICE,
                    "Application Programming Interface",
                    ["Advanced Programming Input", "Application Programming Interface",
                     "Automated Program Installation", "Application Process Integration"],
                    "APIs allow different software to communicate with each other.",
                    "general_coding", "medium"),
        ]
    
    def generate_quiz(self, subject: str, num_questions: int = 10, 
                     difficulty: str = None) -> List[Question]:
        """Generate a quiz for a subject."""
        questions = self.question_banks.get(subject, [])
        
        if difficulty:
            questions = [q for q in questions if q.difficulty == difficulty]
        
        if len(questions) < num_questions:
            # If not enough questions, use AI to generate more
            if self.ai_manager:
                ai_questions = self._generate_ai_questions(subject, num_questions - len(questions))
                questions.extend(ai_questions)
        
        random.shuffle(questions)
        return questions[:num_questions]
    
    def _generate_ai_questions(self, subject: str, count: int) -> List[Question]:
        """Generate questions using AI."""
        if not self.ai_manager:
            return []
        
        prompt = f"""Generate {count} multiple choice questions about {subject}.
Format each question as:
Q: [question]
A: [correct answer]
B: [wrong answer]
C: [wrong answer]
D: [wrong answer]
CORRECT: [A/B/C/D]
EXPLANATION: [brief explanation]

Make questions educational and appropriate difficulty."""
        
        try:
            response = self.ai_manager.get_response(prompt)
            # Parse response into questions (simplified)
            questions = []
            # Would need proper parsing here
            return questions
        except:
            return []
    
    def get_available_subjects(self) -> List[str]:
        """Get list of available subjects."""
        return list(self.question_banks.keys())


class QuizWindow:
    """
    Interactive quiz/test window with grading.
    """
    
    def __init__(self, parent=None, ai_manager=None, subject: str = "mathematics",
                 num_questions: int = 10, is_test: bool = False):
        self.parent = parent
        self.ai_manager = ai_manager
        self.subject = subject
        self.num_questions = num_questions
        self.is_test = is_test  # Test mode has timer and no hints
        
        # Quiz state
        self.generator = QuizGenerator(ai_manager)
        self.questions: List[Question] = []
        self.current_index = 0
        self.answers: Dict[int, str] = {}
        self.start_time = None
        self.result: Optional[QuizResult] = None
        
        # Mistake tracking
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.mistakes_file = self.data_dir / "quiz_mistakes.json"
        self.mistakes_history = self._load_mistakes()
        
        # Create window
        self.window = None
        self._create_window()
    
    def _create_window(self):
        """Create the quiz window."""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()
        
        title = "Test" if self.is_test else "Quiz"
        self.window.title(f"Monica {title} - {self.subject.replace('_', ' ').title()}")
        self.window.geometry("800x600")
        self.window.configure(bg='#2d2d2d')
        
        # Generate questions
        self.questions = self.generator.generate_quiz(self.subject, self.num_questions)
        
        if not self.questions:
            messagebox.showerror("Error", f"No questions available for {self.subject}")
            self.window.destroy()
            return
        
        self.start_time = time.time()
        
        # Create UI
        self._create_header()
        self._create_question_area()
        self._create_navigation()
        self._create_footer()
        
        # Show first question
        self._show_question(0)
    
    def _create_header(self):
        """Create header with progress and timer."""
        header = tk.Frame(self.window, bg='#1e1e1e', height=60)
        header.pack(fill=tk.X, padx=10, pady=10)
        header.pack_propagate(False)
        
        # Subject label
        tk.Label(header, text=f"[*] {self.subject.replace('_', ' ').title()}",
                font=('Segoe UI', 14, 'bold'), bg='#1e1e1e', fg='white').pack(side=tk.LEFT, padx=10)
        
        # Progress
        self.progress_label = tk.Label(header, text="Question 1 of 10",
                                       font=('Segoe UI', 12), bg='#1e1e1e', fg='#888')
        self.progress_label.pack(side=tk.LEFT, padx=20)
        
        # Timer (for tests)
        if self.is_test:
            self.timer_label = tk.Label(header, text="⏱[*] 00:00",
                                        font=('Segoe UI', 12), bg='#1e1e1e', fg='#4CAF50')
            self.timer_label.pack(side=tk.RIGHT, padx=10)
            self._update_timer()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(header, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=10)
    
    def _create_question_area(self):
        """Create main question area."""
        self.question_frame = tk.Frame(self.window, bg='#2d2d2d')
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Question text
        self.question_label = tk.Label(self.question_frame, text="",
                                       font=('Segoe UI', 14), bg='#2d2d2d', fg='white',
                                       wraplength=700, justify=tk.LEFT)
        self.question_label.pack(anchor=tk.W, pady=20)
        
        # Options frame
        self.options_frame = tk.Frame(self.question_frame, bg='#2d2d2d')
        self.options_frame.pack(fill=tk.X, pady=10)
        
        # Answer variable
        self.answer_var = tk.StringVar()
        self.option_buttons: List[tk.Radiobutton] = []
    
    def _create_navigation(self):
        """Create navigation buttons."""
        nav_frame = tk.Frame(self.window, bg='#2d2d2d')
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.prev_btn = tk.Button(nav_frame, text="← Previous", command=self._prev_question,
                                  bg='#3c3c3c', fg='white', font=('Segoe UI', 11),
                                  padx=20, pady=10)
        self.prev_btn.pack(side=tk.LEFT)
        
        self.next_btn = tk.Button(nav_frame, text="Next →", command=self._next_question,
                                  bg='#4CAF50', fg='white', font=('Segoe UI', 11),
                                  padx=20, pady=10)
        self.next_btn.pack(side=tk.RIGHT)
        
        # Submit button (hidden until last question)
        self.submit_btn = tk.Button(nav_frame, text="[*] Submit", command=self._submit_quiz,
                                    bg='#2196F3', fg='white', font=('Segoe UI', 11, 'bold'),
                                    padx=20, pady=10)
    
    def _create_footer(self):
        """Create footer with question navigator."""
        footer = tk.Frame(self.window, bg='#1e1e1e', height=80)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        footer.pack_propagate(False)
        
        # Question number buttons
        btn_frame = tk.Frame(footer, bg='#1e1e1e')
        btn_frame.pack(pady=10)
        
        self.question_btns = []
        for i in range(len(self.questions)):
            btn = tk.Button(btn_frame, text=str(i + 1), width=3,
                           command=lambda idx=i: self._show_question(idx),
                           bg='#3c3c3c', fg='white')
            btn.pack(side=tk.LEFT, padx=2)
            self.question_btns.append(btn)
    
    def _show_question(self, index: int):
        """Display a question."""
        if index < 0 or index >= len(self.questions):
            return
        
        # Save current answer
        if self.answer_var.get():
            self.answers[self.current_index] = self.answer_var.get()
        
        self.current_index = index
        question = self.questions[index]
        
        # Update question text
        self.question_label.config(text=f"Q{index + 1}. {question.question}")
        
        # Clear old options
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.option_buttons.clear()
        
        # Create new options
        self.answer_var.set(self.answers.get(index, ""))
        
        for i, option in enumerate(question.options):
            letter = chr(65 + i)  # A, B, C, D
            rb = tk.Radiobutton(self.options_frame, text=f"{letter}. {option}",
                               variable=self.answer_var, value=option,
                               font=('Segoe UI', 12), bg='#2d2d2d', fg='white',
                               selectcolor='#4CAF50', activebackground='#3c3c3c',
                               activeforeground='white', anchor=tk.W)
            rb.pack(fill=tk.X, pady=5)
            self.option_buttons.append(rb)
        
        # Update progress
        self.progress_label.config(text=f"Question {index + 1} of {len(self.questions)}")
        self.progress_bar['value'] = ((index + 1) / len(self.questions)) * 100
        
        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if index > 0 else tk.DISABLED)
        
        if index == len(self.questions) - 1:
            self.next_btn.pack_forget()
            self.submit_btn.pack(side=tk.RIGHT)
        else:
            self.submit_btn.pack_forget()
            self.next_btn.pack(side=tk.RIGHT)
        
        # Update question navigator
        for i, btn in enumerate(self.question_btns):
            if i == index:
                btn.config(bg='#4CAF50')
            elif i in self.answers:
                btn.config(bg='#2196F3')
            else:
                btn.config(bg='#3c3c3c')
    
    def _prev_question(self):
        """Go to previous question."""
        self._show_question(self.current_index - 1)
    
    def _next_question(self):
        """Go to next question."""
        # Save answer
        if self.answer_var.get():
            self.answers[self.current_index] = self.answer_var.get()
        
        self._show_question(self.current_index + 1)
    
    def _update_timer(self):
        """Update timer display."""
        if not self.window.winfo_exists():
            return
        
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.config(text=f"⏱[*] {minutes:02d}:{seconds:02d}")
        
        self.window.after(1000, self._update_timer)
    
    def _submit_quiz(self):
        """Submit and grade the quiz."""
        # Save last answer
        if self.answer_var.get():
            self.answers[self.current_index] = self.answer_var.get()
        
        # Check if all questions answered
        unanswered = len(self.questions) - len(self.answers)
        if unanswered > 0:
            if not messagebox.askyesno("Confirm", 
                f"You have {unanswered} unanswered question(s). Submit anyway?"):
                return
        
        # Grade quiz
        self._grade_quiz()
    
    def _grade_quiz(self):
        """Grade the quiz and show results."""
        correct = 0
        wrong = 0
        mistakes = []
        
        for i, question in enumerate(self.questions):
            user_answer = self.answers.get(i, "")
            
            if user_answer == question.correct_answer:
                correct += 1
            else:
                wrong += 1
                mistakes.append({
                    'question': question.question,
                    'your_answer': user_answer or "(No answer)",
                    'correct_answer': question.correct_answer,
                    'explanation': question.explanation,
                    'subject': question.subject
                })
        
        time_taken = time.time() - self.start_time
        score = (correct / len(self.questions)) * 100 if self.questions else 0
        
        # Create result
        self.result = QuizResult(
            quiz_id=f"{self.subject}_{int(time.time())}",
            subject=self.subject,
            total_questions=len(self.questions),
            correct_answers=correct,
            wrong_answers=wrong,
            score_percentage=score,
            time_taken=time_taken,
            date=datetime.now().isoformat(),
            mistakes=mistakes
        )
        
        # Save mistakes for learning
        self._save_mistakes(mistakes)
        
        # Show results
        self._show_results()
    
    def _show_results(self):
        """Show quiz results."""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.configure(bg='#1e1e1e')
        
        # Results header
        result_frame = tk.Frame(self.window, bg='#1e1e1e')
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Score
        score = self.result.score_percentage
        if score >= 90:
            grade = "A"
            color = "#4CAF50"
            message = "Excellent! [*]"
        elif score >= 80:
            grade = "B"
            color = "#8BC34A"
            message = "Great job! [*]"
        elif score >= 70:
            grade = "C"
            color = "#FFC107"
            message = "Good effort! [*]"
        elif score >= 60:
            grade = "D"
            color = "#FF9800"
            message = "Keep practicing! [*]"
        else:
            grade = "F"
            color = "#F44336"
            message = "Let's review together! [*]"
        
        tk.Label(result_frame, text="[Stats] Results", font=('Segoe UI', 24, 'bold'),
                bg='#1e1e1e', fg='white').pack(pady=10)
        
        tk.Label(result_frame, text=f"{score:.0f}%", font=('Segoe UI', 48, 'bold'),
                bg='#1e1e1e', fg=color).pack(pady=10)
        
        tk.Label(result_frame, text=f"Grade: {grade}", font=('Segoe UI', 20),
                bg='#1e1e1e', fg=color).pack()
        
        tk.Label(result_frame, text=message, font=('Segoe UI', 16),
                bg='#1e1e1e', fg='white').pack(pady=10)
        
        # Stats
        stats_frame = tk.Frame(result_frame, bg='#2d2d2d')
        stats_frame.pack(fill=tk.X, pady=20, padx=50)
        
        tk.Label(stats_frame, text=f"[*] Correct: {self.result.correct_answers}",
                font=('Segoe UI', 14), bg='#2d2d2d', fg='#4CAF50').pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(stats_frame, text=f"[*] Wrong: {self.result.wrong_answers}",
                font=('Segoe UI', 14), bg='#2d2d2d', fg='#F44336').pack(side=tk.LEFT, padx=20, pady=10)
        
        minutes = int(self.result.time_taken // 60)
        seconds = int(self.result.time_taken % 60)
        tk.Label(stats_frame, text=f"⏱[*] Time: {minutes}:{seconds:02d}",
                font=('Segoe UI', 14), bg='#2d2d2d', fg='white').pack(side=tk.LEFT, padx=20, pady=10)
        
        # Mistakes review
        if self.result.mistakes:
            tk.Label(result_frame, text="[Note] Review Mistakes", font=('Segoe UI', 16, 'bold'),
                    bg='#1e1e1e', fg='white').pack(pady=(20, 10))
            
            mistakes_frame = tk.Frame(result_frame, bg='#2d2d2d')
            mistakes_frame.pack(fill=tk.BOTH, expand=True, padx=20)
            
            # Scrollable mistakes list
            canvas = tk.Canvas(mistakes_frame, bg='#2d2d2d', highlightthickness=0)
            scrollbar = ttk.Scrollbar(mistakes_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#2d2d2d')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for i, mistake in enumerate(self.result.mistakes[:5]):  # Show first 5
                mistake_frame = tk.Frame(scrollable_frame, bg='#3c3c3c', padx=10, pady=10)
                mistake_frame.pack(fill=tk.X, pady=5, padx=10)
                
                tk.Label(mistake_frame, text=f"Q: {mistake['question'][:80]}...",
                        font=('Segoe UI', 11), bg='#3c3c3c', fg='white',
                        anchor=tk.W, wraplength=600).pack(anchor=tk.W)
                tk.Label(mistake_frame, text=f"Your answer: {mistake['your_answer']}",
                        font=('Segoe UI', 10), bg='#3c3c3c', fg='#F44336',
                        anchor=tk.W).pack(anchor=tk.W)
                tk.Label(mistake_frame, text=f"Correct: {mistake['correct_answer']}",
                        font=('Segoe UI', 10), bg='#3c3c3c', fg='#4CAF50',
                        anchor=tk.W).pack(anchor=tk.W)
                tk.Label(mistake_frame, text=f"[Idea] {mistake['explanation']}",
                        font=('Segoe UI', 10, 'italic'), bg='#3c3c3c', fg='#888',
                        anchor=tk.W, wraplength=600).pack(anchor=tk.W)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = tk.Frame(result_frame, bg='#1e1e1e')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Try Again", command=self._retry,
                 bg='#4CAF50', fg='white', font=('Segoe UI', 12),
                 padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="Close", command=self.window.destroy,
                 bg='#3c3c3c', fg='white', font=('Segoe UI', 12),
                 padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    
    def _retry(self):
        """Retry the quiz."""
        self.window.destroy()
        QuizWindow(self.parent, self.ai_manager, self.subject, self.num_questions, self.is_test)
    
    def _load_mistakes(self) -> Dict[str, List]:
        """Load mistake history."""
        if self.mistakes_file.exists():
            try:
                return json.loads(self.mistakes_file.read_text())
            except:
                pass
        return {}
    
    def _save_mistakes(self, new_mistakes: List[Dict]):
        """Save mistakes for future learning."""
        for mistake in new_mistakes:
            subject = mistake.get('subject', 'general')
            if subject not in self.mistakes_history:
                self.mistakes_history[subject] = []
            
            # Check if this mistake was made before
            existing = [m for m in self.mistakes_history[subject] 
                       if m.get('question') == mistake['question']]
            
            if existing:
                # Increment count
                existing[0]['count'] = existing[0].get('count', 1) + 1
                existing[0]['last_seen'] = datetime.now().isoformat()
            else:
                mistake['count'] = 1
                mistake['first_seen'] = datetime.now().isoformat()
                mistake['last_seen'] = datetime.now().isoformat()
                self.mistakes_history[subject].append(mistake)
        
        try:
            self.mistakes_file.write_text(json.dumps(self.mistakes_history, indent=2))
        except Exception as e:
            print(f"Error saving mistakes: {e}")
    
    def run(self):
        """Run the quiz window."""
        if self.parent is None and self.window:
            self.window.mainloop()


def open_quiz(parent=None, ai_manager=None, subject: str = "mathematics",
              num_questions: int = 10, is_test: bool = False) -> QuizWindow:
    """Open a quiz window."""
    return QuizWindow(parent, ai_manager, subject, num_questions, is_test)


def get_available_subjects() -> List[str]:
    """Get list of available quiz subjects."""
    generator = QuizGenerator()
    return generator.get_available_subjects()


# Test
if __name__ == "__main__":
    print("Available subjects:", get_available_subjects())
    quiz = QuizWindow(subject="python", num_questions=5)
    quiz.run()

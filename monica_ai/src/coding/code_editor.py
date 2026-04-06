"""
Monica Code Editor - Integrated Development Environment
A full-featured code editor with terminal, preview, debug, and AI assistance.
Supports all programming languages including Blender and Unity.

Author: Monica AI
Date: December 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime

# Language configurations
LANGUAGE_CONFIG = {
    'python': {
        'extension': '.py',
        'run_cmd': 'python',
        'comment': '#',
        'keywords': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 
                    'try', 'except', 'finally', 'with', 'return', 'yield', 'lambda', 'and', 
                    'or', 'not', 'in', 'is', 'True', 'False', 'None', 'async', 'await'],
        'color': '#3572A5',
    },
    'javascript': {
        'extension': '.js',
        'run_cmd': 'node',
        'comment': '//',
        'keywords': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do',
                    'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally',
                    'class', 'extends', 'import', 'export', 'async', 'await', 'new', 'this'],
        'color': '#F7DF1E',
    },
    'typescript': {
        'extension': '.ts',
        'run_cmd': 'npx ts-node',
        'comment': '//',
        'keywords': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'interface',
                    'type', 'class', 'extends', 'implements', 'import', 'export', 'async', 'await'],
        'color': '#3178C6',
    },
    'csharp': {
        'extension': '.cs',
        'run_cmd': 'dotnet run',
        'comment': '//',
        'keywords': ['using', 'namespace', 'class', 'public', 'private', 'protected', 'static',
                    'void', 'int', 'string', 'bool', 'if', 'else', 'for', 'foreach', 'while',
                    'return', 'new', 'this', 'base', 'virtual', 'override', 'async', 'await'],
        'color': '#178600',
        'unity': True,
    },
    'cpp': {
        'extension': '.cpp',
        'run_cmd': 'g++ -o output && ./output',
        'comment': '//',
        'keywords': ['include', 'using', 'namespace', 'class', 'public', 'private', 'protected',
                    'virtual', 'void', 'int', 'float', 'double', 'char', 'bool', 'if', 'else',
                    'for', 'while', 'return', 'new', 'delete', 'template', 'typename'],
        'color': '#00599C',
    },
    'java': {
        'extension': '.java',
        'run_cmd': 'javac && java',
        'comment': '//',
        'keywords': ['package', 'import', 'class', 'interface', 'extends', 'implements', 'public',
                    'private', 'protected', 'static', 'final', 'void', 'int', 'String', 'boolean',
                    'if', 'else', 'for', 'while', 'return', 'new', 'this', 'super', 'try', 'catch'],
        'color': '#B07219',
    },
    'html': {
        'extension': '.html',
        'run_cmd': None,  # Opens in browser
        'comment': '<!--',
        'keywords': ['html', 'head', 'body', 'div', 'span', 'p', 'a', 'img', 'script', 'style',
                    'link', 'meta', 'title', 'form', 'input', 'button', 'table', 'tr', 'td'],
        'color': '#E34C26',
    },
    'css': {
        'extension': '.css',
        'run_cmd': None,
        'comment': '/*',
        'keywords': ['color', 'background', 'margin', 'padding', 'border', 'font', 'display',
                    'position', 'width', 'height', 'flex', 'grid', 'animation', 'transform'],
        'color': '#563D7C',
    },
    'rust': {
        'extension': '.rs',
        'run_cmd': 'cargo run',
        'comment': '//',
        'keywords': ['fn', 'let', 'mut', 'const', 'if', 'else', 'match', 'for', 'while', 'loop',
                    'return', 'struct', 'enum', 'impl', 'trait', 'pub', 'use', 'mod', 'async'],
        'color': '#DEA584',
    },
    'go': {
        'extension': '.go',
        'run_cmd': 'go run',
        'comment': '//',
        'keywords': ['package', 'import', 'func', 'var', 'const', 'type', 'struct', 'interface',
                    'if', 'else', 'for', 'range', 'switch', 'case', 'return', 'go', 'defer', 'chan'],
        'color': '#00ADD8',
    },
    'swift': {
        'extension': '.swift',
        'run_cmd': 'swift',
        'comment': '//',
        'keywords': ['import', 'class', 'struct', 'enum', 'func', 'var', 'let', 'if', 'else',
                    'for', 'while', 'switch', 'case', 'return', 'guard', 'async', 'await'],
        'color': '#FA7343',
    },
    'kotlin': {
        'extension': '.kt',
        'run_cmd': 'kotlinc -script',
        'comment': '//',
        'keywords': ['package', 'import', 'class', 'interface', 'fun', 'val', 'var', 'if', 'else',
                    'when', 'for', 'while', 'return', 'object', 'companion', 'suspend', 'coroutine'],
        'color': '#A97BFF',
    },
    'blender_python': {
        'extension': '.py',
        'run_cmd': 'blender --python',
        'comment': '#',
        'keywords': ['bpy', 'bmesh', 'mathutils', 'Vector', 'Matrix', 'Quaternion', 'context',
                    'data', 'ops', 'types', 'props', 'scene', 'object', 'mesh', 'material'],
        'color': '#F5792A',
        'blender': True,
    },
    'gdscript': {
        'extension': '.gd',
        'run_cmd': None,  # Runs in Godot
        'comment': '#',
        'keywords': ['extends', 'class_name', 'func', 'var', 'const', 'signal', 'export', 'onready',
                    'if', 'else', 'elif', 'for', 'while', 'match', 'return', 'yield', 'await'],
        'color': '#478CBF',
        'godot': True,
    },
    'sql': {
        'extension': '.sql',
        'run_cmd': None,
        'comment': '--',
        'keywords': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                    'TABLE', 'INDEX', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'GROUP', 'ORDER'],
        'color': '#E38C00',
    },
    'bash': {
        'extension': '.sh',
        'run_cmd': 'bash',
        'comment': '#',
        'keywords': ['if', 'then', 'else', 'elif', 'fi', 'for', 'do', 'done', 'while', 'case',
                    'esac', 'function', 'return', 'exit', 'echo', 'read', 'export', 'source'],
        'color': '#4EAA25',
    },
    'powershell': {
        'extension': '.ps1',
        'run_cmd': 'powershell -File',
        'comment': '#',
        'keywords': ['function', 'param', 'if', 'else', 'elseif', 'foreach', 'for', 'while',
                    'switch', 'return', 'try', 'catch', 'finally', 'throw', 'Write-Host'],
        'color': '#012456',
    },
}

# Code templates
CODE_TEMPLATES = {
    'python': '''# Python Script
# Created with Monica Code Editor

def main():
    """Main function"""
    print("Hello, World!")

if __name__ == "__main__":
    main()
''',
    'javascript': '''// JavaScript
// Created with Monica Code Editor

function main() {
    console.log("Hello, World!");
}

main();
''',
    'csharp': '''// C# - Unity Ready
// Created with Monica Code Editor

using System;
using UnityEngine;

public class MyScript : MonoBehaviour
{
    void Start()
    {
        Debug.Log("Hello, World!");
    }
    
    void Update()
    {
        // Update logic here
    }
}
''',
    'blender_python': '''# Blender Python Script
# Created with Monica Code Editor

import bpy
import bmesh
from mathutils import Vector

def main():
    """Main function for Blender script"""
    # Get the active object
    obj = bpy.context.active_object
    
    if obj and obj.type == 'MESH':
        print(f"Selected object: {obj.name}")
    else:
        print("Please select a mesh object")

if __name__ == "__main__":
    main()
''',
    'html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Page</title>
    <style>
        body { font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <h1>Hello, World!</h1>
    <script>
        console.log("Page loaded!");
    </script>
</body>
</html>
''',
}


class MonicaCodeEditor:
    """
    Full-featured code editor with AI assistance.
    """
    
    def __init__(self, parent=None, ai_manager=None, onedrive_path: str = None):
        self.parent = parent
        self.ai_manager = ai_manager
        self.onedrive_path = onedrive_path or str(Path(r"D:\Monica_Datasets\code"))
        
        # Ensure code folder exists
        Path(self.onedrive_path).mkdir(parents=True, exist_ok=True)
        
        # Current file state
        self.current_file: Optional[Path] = None
        self.current_language = 'python'
        self.is_modified = False
        
        # Process for running code
        self.running_process: Optional[subprocess.Popen] = None
        
        # Create window
        self.window = None
        self.create_window()
    
    def create_window(self):
        """Create the code editor window."""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()
        
        self.window.title("Monica Code Editor")
        self.window.geometry("1400x900")
        self.window.configure(bg='#1e1e1e')
        
        # Configure styles
        self._setup_styles()
        
        # Create main layout
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # Bind shortcuts
        self._bind_shortcuts()
        
        # Load default template
        self._new_file()
    
    def _setup_styles(self):
        """Setup ttk styles for dark theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        style.configure('Dark.TFrame', background='#1e1e1e')
        style.configure('Dark.TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('Dark.TButton', background='#3c3c3c', foreground='#ffffff')
        style.configure('Toolbar.TButton', padding=5)
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.window, bg='#2d2d2d', fg='white')
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H")
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Code", command=self._run_code, accelerator="F5")
        run_menu.add_command(label="Stop", command=self._stop_code, accelerator="Shift+F5")
        run_menu.add_separator()
        run_menu.add_command(label="Debug", command=self._debug_code, accelerator="F9")
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="AI Assistant", menu=ai_menu)
        ai_menu.add_command(label="Explain Code", command=self._ai_explain)
        ai_menu.add_command(label="Fix Errors", command=self._ai_fix_errors)
        ai_menu.add_command(label="Optimize Code", command=self._ai_optimize)
        ai_menu.add_command(label="Generate Code", command=self._ai_generate)
        ai_menu.add_separator()
        ai_menu.add_command(label="Search Online", command=self._search_online)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = ttk.Frame(self.window, style='Dark.TFrame')
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Language selector
        ttk.Label(toolbar, text="Language:", style='Dark.TLabel').pack(side=tk.LEFT, padx=5)
        
        self.lang_var = tk.StringVar(value='python')
        lang_combo = ttk.Combobox(toolbar, textvariable=self.lang_var, 
                                  values=list(LANGUAGE_CONFIG.keys()), width=15)
        lang_combo.pack(side=tk.LEFT, padx=5)
        lang_combo.bind('<<ComboboxSelected>>', self._on_language_change)
        
        # Buttons
        ttk.Button(toolbar, text="[*] Run", command=self._run_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="[*] Stop", command=self._stop_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="[*] Debug", command=self._debug_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="[*] Ask Monica", command=self._ask_monica, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="[Tool] Fix Errors", command=self._ai_fix_errors, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="[Search] Search", command=self._search_online, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        
        # Local storage status
        ttk.Label(toolbar, text="[*] Local", style='Dark.TLabel').pack(side=tk.RIGHT, padx=10)
    
    def _create_main_area(self):
        """Create main editing area with panels."""
        # Main paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - File explorer
        left_frame = ttk.Frame(main_paned, width=200)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="[Folder] Files", style='Dark.TLabel').pack(anchor=tk.W, padx=5, pady=5)
        
        self.file_tree = ttk.Treeview(left_frame, show='tree')
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._populate_file_tree()
        
        # Center panel - Code editor
        center_frame = ttk.Frame(main_paned)
        main_paned.add(center_frame, weight=4)
        
        # Code editor with line numbers
        editor_frame = ttk.Frame(center_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers
        self.line_numbers = tk.Text(editor_frame, width=4, bg='#2d2d2d', fg='#858585',
                                    state=tk.DISABLED, font=('Consolas', 11))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Code editor
        self.code_editor = scrolledtext.ScrolledText(
            editor_frame,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            font=('Consolas', 11),
            wrap=tk.NONE,
            undo=True
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        self.code_editor.bind('<KeyRelease>', self._on_code_change)
        self.code_editor.bind('<Return>', self._auto_indent)
        
        # Right panel - AI Assistant
        right_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="[*] Monica AI Assistant", style='Dark.TLabel').pack(anchor=tk.W, padx=5, pady=5)
        
        self.ai_output = scrolledtext.ScrolledText(
            right_frame,
            bg='#252526',
            fg='#d4d4d4',
            font=('Segoe UI', 10),
            wrap=tk.WORD,
            height=20
        )
        self.ai_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # AI input
        ai_input_frame = ttk.Frame(right_frame)
        ai_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.ai_input = ttk.Entry(ai_input_frame)
        self.ai_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ai_input.bind('<Return>', lambda e: self._ask_monica())
        
        ttk.Button(ai_input_frame, text="Ask", command=self._ask_monica).pack(side=tk.RIGHT, padx=5)
        
        # Bottom panel - Terminal/Output
        bottom_paned = ttk.PanedWindow(self.window, orient=tk.VERTICAL)
        bottom_paned.pack(fill=tk.X, padx=5, pady=5)
        
        terminal_frame = ttk.Frame(self.window)
        terminal_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(terminal_frame, text="[*] Terminal", style='Dark.TLabel').pack(anchor=tk.W)
        
        self.terminal = scrolledtext.ScrolledText(
            terminal_frame,
            bg='#0c0c0c',
            fg='#cccccc',
            font=('Consolas', 10),
            height=8
        )
        self.terminal.pack(fill=tk.X, expand=False)
        
        # Terminal input
        self.terminal_input = ttk.Entry(terminal_frame)
        self.terminal_input.pack(fill=tk.X, pady=2)
        self.terminal_input.bind('<Return>', self._terminal_command)
    
    def _create_status_bar(self):
        """Create status bar."""
        status_frame = ttk.Frame(self.window, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Ready", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.position_label = ttk.Label(status_frame, text="Ln 1, Col 1", style='Dark.TLabel')
        self.position_label.pack(side=tk.RIGHT, padx=10)
        
        self.language_label = ttk.Label(status_frame, text="Python", style='Dark.TLabel')
        self.language_label.pack(side=tk.RIGHT, padx=10)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.window.bind('<Control-n>', lambda e: self._new_file())
        self.window.bind('<Control-o>', lambda e: self._open_file())
        self.window.bind('<Control-s>', lambda e: self._save_file())
        self.window.bind('<F5>', lambda e: self._run_code())
        self.window.bind('<Shift-F5>', lambda e: self._stop_code())
        self.window.bind('<F9>', lambda e: self._debug_code())
    
    def _populate_file_tree(self):
        """Populate file tree with local code folder."""
        self.file_tree.delete(*self.file_tree.get_children())
        
        root_node = self.file_tree.insert('', 'end', text='[Folder] MonicaCode', open=True)
        
        try:
            for item in Path(self.onedrive_path).iterdir():
                if item.is_file():
                    icon = '[*]'
                    self.file_tree.insert(root_node, 'end', text=f'{icon} {item.name}', 
                                         values=(str(item),))
                elif item.is_dir():
                    self.file_tree.insert(root_node, 'end', text=f'[Folder] {item.name}',
                                         values=(str(item),))
        except Exception as e:
            print(f"Error populating file tree: {e}")
    
    def _new_file(self):
        """Create new file."""
        template = CODE_TEMPLATES.get(self.current_language, '')
        self.code_editor.delete('1.0', tk.END)
        self.code_editor.insert('1.0', template)
        self.current_file = None
        self.is_modified = False
        self._update_title()
        self._update_line_numbers()
    
    def _open_file(self):
        """Open file dialog."""
        filetypes = [
            ('All Files', '*.*'),
            ('Python', '*.py'),
            ('JavaScript', '*.js'),
            ('C#', '*.cs'),
            ('HTML', '*.html'),
        ]
        
        filepath = filedialog.askopenfilename(
            initialdir=self.onedrive_path,
            filetypes=filetypes
        )
        
        if filepath:
            self._load_file(Path(filepath))
    
    def _load_file(self, filepath: Path):
        """Load file into editor."""
        try:
            content = filepath.read_text(encoding='utf-8')
            self.code_editor.delete('1.0', tk.END)
            self.code_editor.insert('1.0', content)
            self.current_file = filepath
            self.is_modified = False
            
            # Detect language from extension
            ext = filepath.suffix.lower()
            for lang, config in LANGUAGE_CONFIG.items():
                if config['extension'] == ext:
                    self.current_language = lang
                    self.lang_var.set(lang)
                    break
            
            self._update_title()
            self._update_line_numbers()
            self._highlight_syntax()
            self.status_label.config(text=f"Opened: {filepath.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def _save_file(self):
        """Save current file."""
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_file_as()
    
    def _save_file_as(self):
        """Save file with new name."""
        ext = LANGUAGE_CONFIG.get(self.current_language, {}).get('extension', '.txt')
        
        filepath = filedialog.asksaveasfilename(
            initialdir=self.onedrive_path,
            defaultextension=ext,
            filetypes=[('All Files', '*.*')]
        )
        
        if filepath:
            self._write_file(Path(filepath))
    
    def _write_file(self, filepath: Path):
        """Write content to file."""
        try:
            content = self.code_editor.get('1.0', tk.END)
            filepath.write_text(content, encoding='utf-8')
            self.current_file = filepath
            self.is_modified = False
            self._update_title()
            self._populate_file_tree()
            self.status_label.config(text=f"Saved: {filepath.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")
    
    def _run_code(self):
        """Run the current code."""
        self._save_file()
        
        if not self.current_file:
            self._add_terminal_output("Please save the file first.\n")
            return
        
        config = LANGUAGE_CONFIG.get(self.current_language, {})
        run_cmd = config.get('run_cmd')
        
        if not run_cmd:
            # For HTML, open in browser
            if self.current_language == 'html':
                import webbrowser
                webbrowser.open(str(self.current_file))
                self._add_terminal_output(f"Opened {self.current_file.name} in browser\n")
            else:
                self._add_terminal_output(f"No run command for {self.current_language}\n")
            return
        
        self._add_terminal_output(f"Running {self.current_file.name}...\n")
        
        def run_thread():
            try:
                cmd = f'{run_cmd} "{self.current_file}"'
                self.running_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(self.current_file.parent)
                )
                
                stdout, stderr = self.running_process.communicate()
                
                if stdout:
                    self._add_terminal_output(stdout)
                if stderr:
                    self._add_terminal_output(f"Error:\n{stderr}", error=True)
                
                self._add_terminal_output("\nProcess finished.\n")
                self.running_process = None
                
            except Exception as e:
                self._add_terminal_output(f"Error running code: {e}\n", error=True)
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def _stop_code(self):
        """Stop running code."""
        if self.running_process:
            self.running_process.terminate()
            self._add_terminal_output("\nProcess terminated.\n")
            self.running_process = None
    
    def _debug_code(self):
        """Debug the current code."""
        self._add_terminal_output("Debug mode not yet implemented. Use print statements for now.\n")
        self._ai_explain()
    
    def _add_terminal_output(self, text: str, error: bool = False):
        """Add text to terminal."""
        self.terminal.config(state=tk.NORMAL)
        if error:
            self.terminal.insert(tk.END, text, 'error')
            self.terminal.tag_config('error', foreground='#ff6b6b')
        else:
            self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)
    
    def _terminal_command(self, event=None):
        """Execute terminal command."""
        cmd = self.terminal_input.get()
        self.terminal_input.delete(0, tk.END)
        
        if not cmd:
            return
        
        self._add_terminal_output(f"> {cmd}\n")
        
        def run_cmd():
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.onedrive_path
                )
                if result.stdout:
                    self._add_terminal_output(result.stdout)
                if result.stderr:
                    self._add_terminal_output(result.stderr, error=True)
            except Exception as e:
                self._add_terminal_output(f"Error: {e}\n", error=True)
        
        threading.Thread(target=run_cmd, daemon=True).start()
    
    def _ask_monica(self):
        """Ask Monica AI for help."""
        question = self.ai_input.get()
        if not question:
            question = "Help me with this code"
        
        self.ai_input.delete(0, tk.END)
        
        code = self.code_editor.get('1.0', tk.END)
        
        self._add_ai_output(f"You: {question}\n\n")
        
        if self.ai_manager:
            prompt = f"""You are Monica, an expert programming assistant. Help with this {self.current_language} code.

CODE:
```{self.current_language}
{code[:3000]}
```

USER QUESTION: {question}

Provide a helpful, concise response. If there are errors, explain them and provide fixes."""
            
            def get_response():
                try:
                    response = self.ai_manager.get_response(prompt)
                    self._add_ai_output(f"Monica: {response}\n\n")
                except Exception as e:
                    self._add_ai_output(f"Error: {e}\n\n")
            
            threading.Thread(target=get_response, daemon=True).start()
        else:
            self._add_ai_output("Monica: AI assistant not connected.\n\n")
    
    def _ai_explain(self):
        """Explain the current code."""
        self.ai_input.delete(0, tk.END)
        self.ai_input.insert(0, "Explain this code step by step")
        self._ask_monica()
    
    def _ai_fix_errors(self):
        """Fix errors in code."""
        self.ai_input.delete(0, tk.END)
        self.ai_input.insert(0, "Find and fix any errors in this code")
        self._ask_monica()
    
    def _ai_optimize(self):
        """Optimize code."""
        self.ai_input.delete(0, tk.END)
        self.ai_input.insert(0, "Optimize this code for better performance")
        self._ask_monica()
    
    def _ai_generate(self):
        """Generate code from description."""
        self.ai_input.delete(0, tk.END)
        self.ai_input.insert(0, "Generate code that ")
        self.ai_input.focus()
    
    def _search_online(self):
        """Search online for help."""
        import webbrowser
        
        # Get selected text or current line
        try:
            query = self.code_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            # Get current line
            line = self.code_editor.get("insert linestart", "insert lineend")
            query = f"{self.current_language} {line}"
        
        # Search on Stack Overflow
        url = f"https://stackoverflow.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        
        self._add_ai_output(f"Searching: {query}\n\n")
    
    def _add_ai_output(self, text: str):
        """Add text to AI output panel."""
        self.ai_output.insert(tk.END, text)
        self.ai_output.see(tk.END)
    
    def _on_code_change(self, event=None):
        """Handle code changes."""
        self.is_modified = True
        self._update_title()
        self._update_line_numbers()
        self._update_position()
    
    def _on_language_change(self, event=None):
        """Handle language change."""
        self.current_language = self.lang_var.get()
        self.language_label.config(text=self.current_language.title())
        self._highlight_syntax()
    
    def _update_title(self):
        """Update window title."""
        filename = self.current_file.name if self.current_file else "Untitled"
        modified = " *" if self.is_modified else ""
        self.window.title(f"Monica Code Editor - {filename}{modified}")
    
    def _update_line_numbers(self):
        """Update line numbers."""
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete('1.0', tk.END)
        
        lines = self.code_editor.get('1.0', tk.END).count('\n')
        line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_numbers.insert('1.0', line_numbers)
        
        self.line_numbers.config(state=tk.DISABLED)
    
    def _update_position(self):
        """Update cursor position in status bar."""
        pos = self.code_editor.index(tk.INSERT)
        line, col = pos.split('.')
        self.position_label.config(text=f"Ln {line}, Col {int(col) + 1}")
    
    def _highlight_syntax(self):
        """Basic syntax highlighting."""
        # Remove existing tags
        for tag in self.code_editor.tag_names():
            self.code_editor.tag_delete(tag)
        
        config = LANGUAGE_CONFIG.get(self.current_language, {})
        keywords = config.get('keywords', [])
        
        # Configure tags
        self.code_editor.tag_config('keyword', foreground='#569CD6')
        self.code_editor.tag_config('string', foreground='#CE9178')
        self.code_editor.tag_config('comment', foreground='#6A9955')
        self.code_editor.tag_config('number', foreground='#B5CEA8')
        
        content = self.code_editor.get('1.0', tk.END)
        
        # Highlight keywords
        for keyword in keywords:
            start = '1.0'
            while True:
                pos = self.code_editor.search(r'\m' + keyword + r'\M', start, 
                                              stopindex=tk.END, regexp=True)
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.code_editor.tag_add('keyword', pos, end)
                start = end
    
    def _auto_indent(self, event=None):
        """Auto-indent on Enter."""
        # Get current line
        line = self.code_editor.get("insert linestart", "insert")
        
        # Count leading spaces
        indent = len(line) - len(line.lstrip())
        
        # Check if line ends with colon (Python) or brace
        if line.rstrip().endswith(':') or line.rstrip().endswith('{'):
            indent += 4
        
        # Insert newline with indent
        self.code_editor.insert("insert", "\n" + " " * indent)
        return "break"
    
    def run(self):
        """Run the editor."""
        if self.parent is None:
            self.window.mainloop()


def open_code_editor(parent=None, ai_manager=None):
    """Open the Monica Code Editor."""
    editor = MonicaCodeEditor(parent, ai_manager)
    return editor


# Test
if __name__ == "__main__":
    editor = MonicaCodeEditor()
    editor.run()

"""
MONICA AI - KNOWLEDGE DATASET MANAGER

Interactive sci-fi UI for feeding Monica datasets and reviewing her knowledge.

Features:
- Upload text, PDF, JSON, CSV datasets
- Monica automatically processes and stores knowledge
- Review what Monica learned
- See how Monica interprets data
- Correct Monica's understanding
- Refine knowledge entries
- Sci-fi holographic interface

Author: Monica AI System
Date: December 2, 2025
"""

import sys
import os
from pathlib import Path
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

# Add Monica's directory to path
MONICA_DIR = Path(__file__).parent.parent.parent  # Points to monica_project root
sys.path.insert(0, str(MONICA_DIR))

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    HAS_QT = True
except:
    HAS_QT = False
    print("[!] PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)


class DatasetEntry:
    """Represents a single dataset entry."""

    def __init__(self, dataset_id: str, name: str, content: str,
                 interpretation: str, category: str, timestamp: str):
        self.dataset_id = dataset_id
        self.name = name
        self.content = content
        self.interpretation = interpretation
        self.category = category
        self.timestamp = timestamp


class KnowledgeDatabase:
    """Manages Monica's knowledge database."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(MONICA_DIR / "data" / "monica_knowledge.db")

        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True, parents=True)

        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """Create knowledge tables."""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_corrected INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        self.conn.commit()

    def add_dataset(self, name: str, content: str, category: str) -> str:
        """Add a new dataset entry."""
        # Generate unique ID
        dataset_id = hashlib.md5(
            f"{name}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Monica's interpretation (simple analysis for now)
        interpretation = self._interpret_content(content, category)

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO datasets (id, name, content, interpretation, category, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (dataset_id, name, content, interpretation, category,
              datetime.now().isoformat()))

        self.conn.commit()
        return dataset_id

    def _interpret_content(self, content: str, category: str) -> str:
        """Monica interprets the content."""
        interpretation = f"Dataset Analysis:\n"
        interpretation += f"- Category: {category}\n"

        # Check if it's a media file
        if content.startswith('[VIDEO FILE]'):
            interpretation += f"- Type: Video Media\n"
            # Extract info
            if 'Size:' in content:
                size_line = [l for l in content.split('\n') if 'Size:' in l][0]
                interpretation += f"- {size_line.strip()}\n"
            if 'Format:' in content:
                format_line = [l for l in content.split('\n') if 'Format:' in l][0]
                interpretation += f"- {format_line.strip()}\n"
            interpretation += f"\nMonica's Understanding:\n"
            interpretation += f"I've stored a reference to this video file. "
            interpretation += f"I can access the full video content at the original location. "
            interpretation += f"This is categorized as {category}. I can retrieve this video whenever you need it."

        elif content.startswith('[IMAGE FILE]'):
            interpretation += f"- Type: Image Media\n"
            if 'Size:' in content and 'pixels' in content:
                size_line = [l for l in content.split('\n') if 'pixels' in l][0]
                interpretation += f"- {size_line.strip()}\n"
            interpretation += f"\nMonica's Understanding:\n"
            interpretation += f"I've stored a reference to this image. "
            interpretation += f"The full image is accessible at the original path. "
            interpretation += f"This is {category}. I can display or retrieve this image when you ask."

        elif content.startswith('[AUDIO FILE]'):
            interpretation += f"- Type: Audio Media\n"
            if 'Size:' in content:
                size_line = [l for l in content.split('\n') if 'Size:' in l][0]
                interpretation += f"- {size_line.strip()}\n"
            interpretation += f"\nMonica's Understanding:\n"
            interpretation += f"I've stored a reference to this audio file. "
            interpretation += f"I can access the audio content at the original location. "
            interpretation += f"Categorized as {category}."

        elif content.startswith('[PDF DOCUMENT]'):
            interpretation += f"- Type: PDF Document\n"
            interpretation += f"\nMonica's Understanding:\n"
            interpretation += f"I've stored a reference to this PDF document. "
            interpretation += f"I can extract and analyze the text content when needed. "
            interpretation += f"Document categorized as {category}."

        else:
            # Text content
            word_count = len(content.split())
            line_count = len(content.split('\n'))
            interpretation += f"- Type: Text Data\n"
            interpretation += f"- Word Count: {word_count}\n"
            interpretation += f"- Line Count: {line_count}\n"

            # Check for keywords
            if "function" in content or "def " in content or "class " in content:
                interpretation += "- Contains: Code/Programming\n"
            if any(word in content.lower() for word in ["patient", "medical", "diagnosis"]):
                interpretation += "- Contains: Medical Information\n"
            if any(word in content.lower() for word in ["legal", "law", "court"]):
                interpretation += "- Contains: Legal Information\n"

            interpretation += f"\nMonica's Understanding:\n"
            interpretation += f"This appears to be {category} data. "
            interpretation += f"I can use this information to enhance my knowledge in this area."

        return interpretation

    def get_all_datasets(self) -> List[DatasetEntry]:
        """Get all datasets."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, content, interpretation, category, timestamp FROM datasets ORDER BY timestamp DESC')

        datasets = []
        for row in cursor.fetchall():
            datasets.append(DatasetEntry(*row))

        return datasets

    def update_interpretation(self, dataset_id: str, new_interpretation: str):
        """Update Monica's interpretation (user correction)."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE datasets
            SET interpretation = ?, user_corrected = 1
            WHERE id = ?
        ''', (new_interpretation, dataset_id))
        self.conn.commit()

    def update_content(self, dataset_id: str, new_content: str):
        """Update dataset content."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE datasets
            SET content = ?
            WHERE id = ?
        ''', (new_content, dataset_id))
        self.conn.commit()

    def delete_dataset(self, dataset_id: str):
        """Delete a dataset."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM datasets WHERE id = ?', (dataset_id,))
        self.conn.commit()


class MonicaKnowledgeManager(QMainWindow):
    """Main Knowledge Manager UI."""

    def __init__(self):
        super().__init__()

        self.db = KnowledgeDatabase()
        self.current_dataset = None

        self.init_ui()
        self.load_datasets()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Monica AI - Knowledge Dataset Manager")
        self.setGeometry(100, 100, 1400, 900)

        # Sci-fi dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a1a, stop:1 #1a1a3a);
            }
            QWidget {
                background: transparent;
                color: #00ffff;
                font-family: 'Consolas', monospace;
                font-size: 12pt;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff00ff, stop:1 #8800ff);
                color: white;
                border: 2px solid #00ffff;
                border-radius: 10px;
                padding: 15px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff33ff, stop:1 #aa00ff);
                border: 2px solid #ff00ff;
            }
            QPushButton:pressed {
                background: #6600aa;
            }
            QTextEdit, QPlainTextEdit {
                background: rgba(10, 10, 30, 0.8);
                color: #00ffff;
                border: 2px solid #00ffff;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
            QListWidget {
                background: rgba(10, 10, 30, 0.8);
                color: #00ffff;
                border: 2px solid #ff00ff;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #00ffff;
            }
            QListWidget::item:selected {
                background: rgba(255, 0, 255, 0.3);
                border: 2px solid #ff00ff;
            }
            QLabel {
                color: #00ffff;
                font-size: 14pt;
                font-weight: bold;
            }
            QComboBox {
                background: rgba(10, 10, 30, 0.8);
                color: #00ffff;
                border: 2px solid #00ffff;
                border-radius: 5px;
                padding: 8px;
                font-size: 12pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #00ffff;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel("MONICA AI - KNOWLEDGE DATASET MANAGER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24pt; color: #ff00ff; text-shadow: 0px 0px 10px #ff00ff;")
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Feed Monica datasets and review her knowledge")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14pt; color: #00ffff;")
        main_layout.addWidget(subtitle)

        # Content area (split)
        content_splitter = QSplitter(Qt.Horizontal)

        # LEFT: Dataset list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        list_label = QLabel("DATASETS")
        list_label.setStyleSheet("font-size: 16pt; color: #ff00ff;")
        left_layout.addWidget(list_label)

        self.dataset_list = QListWidget()
        self.dataset_list.itemClicked.connect(self.on_dataset_selected)
        left_layout.addWidget(self.dataset_list)

        # Upload buttons
        btn_layout = QVBoxLayout()

        upload_text_btn = QPushButton("UPLOAD ANY FILE\n(Video/Image/Audio/Text)")
        upload_text_btn.clicked.connect(self.upload_text_file)
        btn_layout.addWidget(upload_text_btn)

        upload_json_btn = QPushButton("UPLOAD JSON DATA")
        upload_json_btn.clicked.connect(self.upload_json_file)
        btn_layout.addWidget(upload_json_btn)

        manual_entry_btn = QPushButton("MANUAL ENTRY")
        manual_entry_btn.clicked.connect(self.manual_entry)
        btn_layout.addWidget(manual_entry_btn)

        left_layout.addLayout(btn_layout)

        content_splitter.addWidget(left_panel)

        # RIGHT: Dataset viewer/editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        viewer_label = QLabel("DATASET VIEWER & EDITOR")
        viewer_label.setStyleSheet("font-size: 16pt; color: #ff00ff;")
        right_layout.addWidget(viewer_label)

        # Dataset info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Name:"))
        self.name_field = QLineEdit()
        self.name_field.setStyleSheet("""
            background: rgba(10, 10, 30, 0.8);
            color: #00ffff;
            border: 2px solid #00ffff;
            border-radius: 5px;
            padding: 8px;
            font-size: 12pt;
        """)
        info_layout.addWidget(self.name_field)

        info_layout.addWidget(QLabel("Category:"))
        self.category_field = QComboBox()
        self.category_field.addItems([
            "General Knowledge",
            "Code/Programming",
            "Medical",
            "Legal",
            "Science",
            "History",
            "Language",
            "Personal Notes",
            "Research",
            "Documentation",
            "Video - Tutorial",
            "Video - Entertainment",
            "Video - Educational",
            "Image - Photo",
            "Image - Artwork",
            "Image - Diagram/Chart",
            "Audio - Music",
            "Audio - Podcast",
            "Audio - Recording",
            "Book/Document - PDF",
            "Book/Document - Text",
            "Web Article/Blog",
            "Social Media Post",
            "Conversation/Chat Log",
            "Recipe/Cooking",
            "Fitness/Health Data",
            "Financial/Budget Data"
        ])
        info_layout.addWidget(self.category_field)

        right_layout.addLayout(info_layout)

        # Content editor
        right_layout.addWidget(QLabel("CONTENT:"))
        self.content_editor = QPlainTextEdit()
        right_layout.addWidget(self.content_editor)

        # Monica's interpretation
        right_layout.addWidget(QLabel("MONICA'S INTERPRETATION:"))
        self.interpretation_editor = QTextEdit()
        right_layout.addWidget(self.interpretation_editor)

        # Action buttons
        action_layout = QHBoxLayout()

        save_btn = QPushButton("SAVE CHANGES")
        save_btn.clicked.connect(self.save_changes)
        action_layout.addWidget(save_btn)

        delete_btn = QPushButton("DELETE DATASET")
        delete_btn.clicked.connect(self.delete_dataset)
        delete_btn.setStyleSheet(delete_btn.styleSheet() + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #880000);
            }
        """)
        action_layout.addWidget(delete_btn)

        right_layout.addLayout(action_layout)

        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([400, 1000])

        main_layout.addWidget(content_splitter)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 11pt; color: #00ff00;")
        main_layout.addWidget(self.status_label)

    def load_datasets(self):
        """Load all datasets into list."""
        self.dataset_list.clear()
        datasets = self.db.get_all_datasets()

        for dataset in datasets:
            item = QListWidgetItem(f"{dataset.name} ({dataset.category})")
            item.setData(Qt.UserRole, dataset)
            self.dataset_list.addItem(item)

        self.status_label.setText(f"Loaded {len(datasets)} datasets")

    def on_dataset_selected(self, item):
        """Handle dataset selection."""
        dataset = item.data(Qt.UserRole)
        self.current_dataset = dataset

        self.name_field.setText(dataset.name)
        self.category_field.setCurrentText(dataset.category)
        self.content_editor.setPlainText(dataset.content)
        self.interpretation_editor.setPlainText(dataset.interpretation)

        self.status_label.setText(f"Viewing: {dataset.name}")

    def upload_text_file(self):
        """Upload any file (text, video, image, audio, etc.)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*);;Text Files (*.txt *.md);;Code (*.py *.js *.java *.cpp);;Videos (*.mp4 *.avi *.mov *.mkv);;Images (*.jpg *.png *.gif *.bmp);;Audio (*.mp3 *.wav *.ogg);;Documents (*.pdf *.docx)"
        )

        if file_path:
            try:
                file_ext = Path(file_path).suffix.lower()
                name = Path(file_path).name

                # Handle different file types
                if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']:
                    # Video file
                    import os
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    content = f"[VIDEO FILE]\nPath: {file_path}\nSize: {file_size:.2f} MB\nFormat: {file_ext[1:].upper()}\n\nNote: Video content stored by reference. Full video accessible at original path."
                    category = "Video - Educational"

                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
                    # Image file
                    try:
                        from PIL import Image
                        img = Image.open(file_path)
                        content = f"[IMAGE FILE]\nPath: {file_path}\nSize: {img.size[0]}x{img.size[1]} pixels\nFormat: {img.format}\nMode: {img.mode}\n\nNote: Image stored by reference. Full image accessible at original path."
                        category = "Image - Photo"
                    except:
                        content = f"[IMAGE FILE]\nPath: {file_path}\nFormat: {file_ext[1:].upper()}"
                        category = "Image - Photo"

                elif file_ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma']:
                    # Audio file
                    import os
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    content = f"[AUDIO FILE]\nPath: {file_path}\nSize: {file_size:.2f} MB\nFormat: {file_ext[1:].upper()}\n\nNote: Audio content stored by reference. Full audio accessible at original path."
                    category = "Audio - Recording"

                elif file_ext == '.pdf':
                    # PDF file
                    content = f"[PDF DOCUMENT]\nPath: {file_path}\n\nNote: PDF content can be extracted and analyzed. Document accessible at original path."
                    category = "Book/Document - PDF"

                else:
                    # Text/Code file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    category = self._detect_category(file_path, content)

                dataset_id = self.db.add_dataset(name, content, category)
                self.load_datasets()

                self.status_label.setText(f"Uploaded: {name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"Dataset '{name}' uploaded successfully!\n\nCategory: {category}\nMonica is processing the data..."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload file: {e}")

    def upload_json_file(self):
        """Upload a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Validate JSON
                json.loads(content)

                name = Path(file_path).stem
                category = "JSON Data"

                dataset_id = self.db.add_dataset(name, content, category)
                self.load_datasets()

                self.status_label.setText(f"Uploaded: {name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"JSON dataset '{name}' uploaded successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload JSON: {e}")

    def manual_entry(self):
        """Manual dataset entry."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manual Dataset Entry")
        dialog.setStyleSheet(self.styleSheet())
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Dataset Name:"))
        name_input = QLineEdit()
        name_input.setStyleSheet(self.name_field.styleSheet())
        layout.addWidget(name_input)

        layout.addWidget(QLabel("Category:"))
        category_input = QComboBox()
        category_input.addItems(["General Knowledge", "Code/Programming", "Medical", "Legal",
                                "Science", "History", "Language", "Personal Notes", "Research", "Documentation"])
        layout.addWidget(category_input)

        layout.addWidget(QLabel("Content:"))
        content_input = QPlainTextEdit()
        content_input.setStyleSheet(self.content_editor.styleSheet())
        layout.addWidget(content_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("SAVE")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text()
            category = category_input.currentText()
            content = content_input.toPlainText()

            if name and content:
                dataset_id = self.db.add_dataset(name, content, category)
                self.load_datasets()
                self.status_label.setText(f"Created: {name}")

    def save_changes(self):
        """Save changes to current dataset."""
        if not self.current_dataset:
            QMessageBox.warning(self, "Warning", "No dataset selected")
            return

        new_content = self.content_editor.toPlainText()
        new_interpretation = self.interpretation_editor.toPlainText()

        self.db.update_content(self.current_dataset.dataset_id, new_content)
        self.db.update_interpretation(self.current_dataset.dataset_id, new_interpretation)

        self.load_datasets()
        self.status_label.setText("Changes saved!")
        QMessageBox.information(self, "Success", "Dataset updated successfully!")

    def delete_dataset(self):
        """Delete current dataset."""
        if not self.current_dataset:
            QMessageBox.warning(self, "Warning", "No dataset selected")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_dataset.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.delete_dataset(self.current_dataset.dataset_id)
            self.current_dataset = None
            self.load_datasets()

            self.name_field.clear()
            self.content_editor.clear()
            self.interpretation_editor.clear()

            self.status_label.setText("Dataset deleted")

    def _detect_category(self, file_path: str, content: str) -> str:
        """Auto-detect category from file extension and content."""
        ext = Path(file_path).suffix.lower()

        if ext in ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.rb']:
            return "Code/Programming"
        elif ext in ['.md', '.txt']:
            if any(word in content.lower() for word in ["patient", "medical", "diagnosis"]):
                return "Medical"
            elif any(word in content.lower() for word in ["legal", "law", "court"]):
                return "Legal"
            else:
                return "General Knowledge"
        else:
            return "General Knowledge"


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set app style
    app.setStyle('Fusion')

    # Create and show main window
    window = MonicaKnowledgeManager()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

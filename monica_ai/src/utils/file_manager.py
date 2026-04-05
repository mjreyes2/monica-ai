"""
Monica File Manager - Download and manage files.
Shared workspace for Monica and user collaboration.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import shutil


class MonicaFileManager:
    """
    Manages file downloads and shared workspace.
    """
    
    def __init__(self):
        # Shared workspace folder
        self.workspace = Path(__file__).parent.parent.parent.parent / "monica_workspace"
        self.downloads_folder = self.workspace / "downloads"
        self.sounds_folder = self.workspace / "sounds"
        self.images_folder = self.workspace / "images"
        self.documents_folder = self.workspace / "documents"
        
        # Create folders
        for folder in [self.workspace, self.downloads_folder, self.sounds_folder, 
                       self.images_folder, self.documents_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        print(f"[Folder] Monica workspace: {self.workspace}")
    
    def download_file(self, url: str, filename: Optional[str] = None, 
                      folder: Optional[str] = None) -> Optional[Path]:
        """
        Download a file from URL.
        
        Args:
            url: URL to download from
            filename: Optional custom filename
            folder: Optional subfolder (downloads, sounds, images, documents)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Determine target folder
            if folder == "sounds":
                target_folder = self.sounds_folder
            elif folder == "images":
                target_folder = self.images_folder
            elif folder == "documents":
                target_folder = self.documents_folder
            else:
                target_folder = self.downloads_folder
            
            # Get filename from URL if not provided
            if not filename:
                filename = url.split("/")[-1].split("?")[0]
                if not filename:
                    filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Download
            print(f"[*] Downloading: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save file
            filepath = target_folder / filename
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[OK] Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return None
    
    def list_files(self, folder: Optional[str] = None) -> List[Dict]:
        """List files in workspace."""
        if folder == "sounds":
            target = self.sounds_folder
        elif folder == "images":
            target = self.images_folder
        elif folder == "documents":
            target = self.documents_folder
        elif folder == "downloads":
            target = self.downloads_folder
        else:
            target = self.workspace
        
        files = []
        for f in target.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        return files
    
    def get_workspace_path(self) -> Path:
        """Get the workspace path."""
        return self.workspace
    
    def save_text(self, content: str, filename: str, folder: str = "documents") -> Optional[Path]:
        """Save text content to a file."""
        try:
            if folder == "documents":
                target = self.documents_folder
            else:
                target = self.workspace / folder
                target.mkdir(exist_ok=True)
            
            filepath = target / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[OK] Saved: {filepath}")
            return filepath
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")
            return None


# Singleton
_file_manager = None

def get_file_manager() -> MonicaFileManager:
    """Get the file manager instance."""
    global _file_manager
    if _file_manager is None:
        _file_manager = MonicaFileManager()
    return _file_manager

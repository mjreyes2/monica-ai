"""
AR Teaching Coordinator - Main controller for AR/Holographic teaching system
Coordinates animations, 3D visualizations, AR projections, and sound effects
"""

import os
import sys
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import visualization libraries
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False

try:
    import cv2
    import cv2.aruco as aruco
    import numpy as np
    ARUCO_AVAILABLE = True
except ImportError:
    ARUCO_AVAILABLE = False

from .sound_manager import get_sound_manager


class VisualizationType(Enum):
    """Types of visualizations available."""
    MANIM_2D = "manim_2d"           # 2D animated explanation
    MANIM_3D = "manim_3d"           # 3D animated explanation
    PYVISTA = "pyvista"             # Interactive 3D visualization
    OPEN3D = "open3d"               # Advanced 3D visualization
    AR_MARKER = "ar_marker"         # AR projection on physical marker
    INTERACTIVE = "interactive"     # Interactive game-like visualization


@dataclass
class TeachingRequest:
    """Request for teaching visualization."""
    topic: str                      # Topic to teach (e.g., "binary search")
    user_query: str                 # Original user query
    visualization_type: VisualizationType
    step_by_step: bool = True       # Show step-by-step progression
    interactive: bool = False       # Allow user interaction
    sound_effects: bool = True      # Play sci-fi sound effects
    narration: str = ""             # Text narration for each step


class ARTeachingCoordinator:
    """
    Main coordinator for AR/Holographic teaching system.
    
    Responsibilities:
    - Parse user teaching requests
    - Determine appropriate visualization type
    - Generate step-by-step teaching plans
    - Coordinate animations and sound effects
    - Manage AR marker tracking
    - Handle user interaction (voice commands, gestures)
    """
    
    def __init__(self):
        """Initialize AR teaching coordinator."""
        self.sound_manager = get_sound_manager()
        
        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.visualizations_dir = project_root / "ar_teaching" / "visualizations"
        self.visualizations_dir.mkdir(parents=True, exist_ok=True)
        
        # Current teaching session
        self.current_session: Optional[TeachingRequest] = None
        self.current_step = 0
        self.total_steps = 0
        
        # AR tracking (if available)
        self.ar_enabled = False
        self.aruco_dict = None
        self.aruco_params = None
        if ARUCO_AVAILABLE:
            self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
            self.aruco_params = aruco.DetectorParameters()
        
        print("[ARTeachingCoordinator] Initialized")
        print(f"  - PyVista available: {PYVISTA_AVAILABLE}")
        print(f"  - Open3D available: {OPEN3D_AVAILABLE}")
        print(f"  - ArUco available: {ARUCO_AVAILABLE}")
    
    def parse_teaching_request(self, user_query: str) -> Optional[TeachingRequest]:
        """
        Parse user query to determine teaching request.
        
        Args:
            user_query: User's question/request
            
        Returns:
            TeachingRequest if valid teaching query, None otherwise
        """
        query_lower = user_query.lower()
        
        # Teaching keywords
        teaching_keywords = [
            "teach me", "show me", "explain", "visualize", "demonstrate",
            "how does", "what is", "animate", "illustrate"
        ]
        
        # Check if this is a teaching request
        is_teaching = any(keyword in query_lower for keyword in teaching_keywords)
        if not is_teaching:
            return None
        
        # Determine topic
        topic = self._extract_topic(user_query)
        if not topic:
            return None
        
        # Determine visualization type
        viz_type = self._determine_visualization_type(topic, query_lower)
        
        # Create request
        request = TeachingRequest(
            topic=topic,
            user_query=user_query,
            visualization_type=viz_type,
            step_by_step=True,
            interactive="interactive" in query_lower or "play with" in query_lower,
            sound_effects=True
        )
        
        return request
    
    def _extract_topic(self, query: str) -> Optional[str]:
        """Extract topic from user query."""
        # Common patterns
        patterns = [
            "teach me about ",
            "teach me ",
            "show me ",
            "explain ",
            "visualize ",
            "demonstrate ",
            "how does ",
            "what is ",
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            if pattern in query_lower:
                # Extract everything after the pattern
                idx = query_lower.index(pattern) + len(pattern)
                topic = query[idx:].strip()
                # Remove trailing punctuation
                topic = topic.rstrip("?.!")
                return topic
        
        return None
    
    def _determine_visualization_type(self, topic: str, query_lower: str) -> VisualizationType:
        """Determine best visualization type for topic."""
        # Algorithm/data structure topics → Manim 2D animation
        algorithm_keywords = ["sort", "search", "tree", "graph", "algorithm", "array", "list"]
        if any(kw in topic.lower() for kw in algorithm_keywords):
            return VisualizationType.MANIM_2D
        
        # 3D/spatial topics → PyVista or Open3D
        spatial_keywords = ["3d", "rotation", "matrix", "vector", "geometry", "mesh", "model"]
        if any(kw in topic.lower() for kw in spatial_keywords):
            return VisualizationType.PYVISTA if PYVISTA_AVAILABLE else VisualizationType.MANIM_3D
        
        # AR request → AR marker projection
        if "hologram" in query_lower or "ar" in query_lower or "project" in query_lower:
            return VisualizationType.AR_MARKER if ARUCO_AVAILABLE else VisualizationType.PYVISTA
        
        # Default to Manim 2D
        return VisualizationType.MANIM_2D
    
    def start_teaching_session(self, request: TeachingRequest) -> bool:
        """
        Start a teaching session.
        
        Args:
            request: Teaching request
            
        Returns:
            True if session started successfully
        """
        self.current_session = request
        self.current_step = 0
        
        # Play activation sound
        if request.sound_effects:
            self.sound_manager.play("hologram_activate")
        
        print(f"[ARTeaching] Starting session: {request.topic}")
        print(f"  - Visualization: {request.visualization_type.value}")
        print(f"  - Step-by-step: {request.step_by_step}")
        print(f"  - Interactive: {request.interactive}")
        
        # Generate teaching content based on visualization type
        if request.visualization_type == VisualizationType.MANIM_2D:
            return self._start_manim_2d_session(request)
        elif request.visualization_type == VisualizationType.MANIM_3D:
            return self._start_manim_3d_session(request)
        elif request.visualization_type == VisualizationType.PYVISTA:
            return self._start_pyvista_session(request)
        elif request.visualization_type == VisualizationType.OPEN3D:
            return self._start_open3d_session(request)
        elif request.visualization_type == VisualizationType.AR_MARKER:
            return self._start_ar_marker_session(request)
        else:
            print(f"[ARTeaching] Unknown visualization type: {request.visualization_type}")
            return False
    
    def _start_manim_2d_session(self, request: TeachingRequest) -> bool:
        """Start Manim 2D animation session."""
        # Check if visualization exists
        viz_file = self.visualizations_dir / f"{request.topic.lower().replace(' ', '_')}.py"
        
        if not viz_file.exists():
            print(f"[ARTeaching] Visualization not found: {viz_file}")
            print(f"[ARTeaching] Topic '{request.topic}' needs to be created in Phase 3")
            return False
        
        # Render animation (this will be implemented in Phase 3)
        print(f"[ARTeaching] Would render Manim animation: {viz_file}")
        return True
    
    def _start_manim_3d_session(self, request: TeachingRequest) -> bool:
        """Start Manim 3D animation session."""
        print(f"[ARTeaching] Manim 3D session for: {request.topic}")
        return True
    
    def _start_pyvista_session(self, request: TeachingRequest) -> bool:
        """Start PyVista interactive 3D session."""
        if not PYVISTA_AVAILABLE:
            print("[ARTeaching] PyVista not available")
            return False
        
        print(f"[ARTeaching] PyVista session for: {request.topic}")
        
        # Example: Show a simple 3D object
        # This will be expanded in Phase 3 with actual teaching content
        try:
            plotter = pv.Plotter()
            mesh = pv.Sphere(radius=1.0)
            plotter.add_mesh(mesh, color='cyan', show_edges=True)
            plotter.add_text(f"Teaching: {request.topic}", position='upper_left', font_size=12)
            
            # Non-blocking show (returns immediately)
            plotter.show(auto_close=False, interactive_update=True)
            return True
        except Exception as e:
            print(f"[ARTeaching] PyVista error: {e}")
            return False
    
    def _start_open3d_session(self, request: TeachingRequest) -> bool:
        """Start Open3D advanced 3D session."""
        if not OPEN3D_AVAILABLE:
            print("[ARTeaching] Open3D not available")
            return False
        
        print(f"[ARTeaching] Open3D session for: {request.topic}")
        return True
    
    def _start_ar_marker_session(self, request: TeachingRequest) -> bool:
        """Start AR marker projection session."""
        if not ARUCO_AVAILABLE:
            print("[ARTeaching] ArUco not available")
            return False
        
        self.ar_enabled = True
        print(f"[ARTeaching] AR marker session for: {request.topic}")
        print("[ARTeaching] Place ArUco marker (ID 0-249) in camera view")
        return True
    
    def next_step(self):
        """Move to next teaching step."""
        if not self.current_session:
            return
        
        self.current_step += 1
        if self.current_session.sound_effects:
            self.sound_manager.play("step_next")
        
        print(f"[ARTeaching] Step {self.current_step}/{self.total_steps}")
    
    def previous_step(self):
        """Move to previous teaching step."""
        if not self.current_session:
            return
        
        self.current_step = max(0, self.current_step - 1)
        if self.current_session.sound_effects:
            self.sound_manager.play("step_previous")
        
        print(f"[ARTeaching] Step {self.current_step}/{self.total_steps}")
    
    def pause(self):
        """Pause current teaching session."""
        if self.current_session and self.current_session.sound_effects:
            self.sound_manager.play("interface_beep_01")
        print("[ARTeaching] Paused")
    
    def resume(self):
        """Resume teaching session."""
        if self.current_session and self.current_session.sound_effects:
            self.sound_manager.play("interface_beep_02")
        print("[ARTeaching] Resumed")
    
    def stop_session(self):
        """Stop current teaching session."""
        if self.current_session:
            if self.current_session.sound_effects:
                self.sound_manager.play("hologram_deactivate")
            
            print(f"[ARTeaching] Stopped session: {self.current_session.topic}")
            self.current_session = None
            self.current_step = 0
            self.ar_enabled = False
    
    def handle_voice_command(self, command: str) -> bool:
        """
        Handle voice command during teaching session.
        
        Args:
            command: Voice command from user
            
        Returns:
            True if command was handled
        """
        command_lower = command.lower()
        
        # Step navigation
        if "next step" in command_lower or "next" in command_lower:
            self.next_step()
            return True
        elif "previous step" in command_lower or "back" in command_lower or "previous" in command_lower:
            self.previous_step()
            return True
        elif "repeat" in command_lower or "again" in command_lower:
            # Replay current step
            if self.current_session and self.current_session.sound_effects:
                self.sound_manager.play("interface_beep_03")
            return True
        
        # Playback control
        elif "pause" in command_lower:
            self.pause()
            return True
        elif "resume" in command_lower or "continue" in command_lower:
            self.resume()
            return True
        elif "stop" in command_lower or "end" in command_lower or "exit" in command_lower:
            self.stop_session()
            return True
        
        # Interaction
        elif "rotate" in command_lower:
            # Handle rotation commands for 3D views
            return True
        elif "zoom" in command_lower:
            # Handle zoom commands
            return True
        
        return False


# Global coordinator instance
_coordinator: Optional[ARTeachingCoordinator] = None

def get_ar_coordinator() -> ARTeachingCoordinator:
    """Get global AR teaching coordinator instance (singleton)."""
    global _coordinator
    if _coordinator is None:
        _coordinator = ARTeachingCoordinator()
    return _coordinator

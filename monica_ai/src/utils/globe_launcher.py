"""
Monica Globe Launcher
Opens the NASA WorldWind globe in a web browser.
Integrates with Monica's voice commands and Rest Countries API.
"""

import webbrowser
import os
import http.server
import socketserver
import threading
from pathlib import Path
from typing import Optional
import urllib.parse

# Globe HTML file location
GLOBE_DIR = Path(__file__).parent.parent.parent / "resources" / "globe"
GLOBE_FILE = GLOBE_DIR / "worldwind_globe.html"

# Local server for serving the globe
_server = None
_server_thread = None
_server_port = 8765


class GlobeLauncher:
    """
    Launches and controls the NASA WorldWind globe for Monica.
    """
    
    def __init__(self):
        self.server_running = False
        self.server_port = _server_port
        self.globe_url = None
        
    def start_server(self) -> bool:
        """Start a local HTTP server to serve the globe HTML."""
        global _server, _server_thread
        
        if self.server_running:
            return True
        
        try:
            # Change to globe directory
            os.chdir(GLOBE_DIR)
            
            # Create handler
            handler = http.server.SimpleHTTPRequestHandler
            
            # Try to find an available port
            for port in range(_server_port, _server_port + 10):
                try:
                    _server = socketserver.TCPServer(("", port), handler)
                    self.server_port = port
                    break
                except OSError:
                    continue
            
            if _server is None:
                print("[GLOBE] Could not find available port")
                return False
            
            # Start server in background thread
            _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
            _server_thread.start()
            
            self.server_running = True
            self.globe_url = f"http://localhost:{self.server_port}/worldwind_globe.html"
            print(f"[GLOBE] Server started at {self.globe_url}")
            return True
            
        except Exception as e:
            print(f"[GLOBE] Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the local HTTP server."""
        global _server
        
        if _server:
            _server.shutdown()
            _server = None
            self.server_running = False
            print("[GLOBE] Server stopped")
    
    def open_globe(self, lat: float = None, lon: float = None, country: str = None) -> bool:
        """
        Open the globe in the default web browser.
        
        Args:
            lat: Latitude to center on
            lon: Longitude to center on
            country: Country name to search for
            
        Returns:
            True if successful
        """
        # Start server if not running
        if not self.server_running:
            if not self.start_server():
                # Fallback: open file directly
                if GLOBE_FILE.exists():
                    url = f"file:///{GLOBE_FILE.as_posix()}"
                else:
                    print("[GLOBE] Globe file not found")
                    return False
            else:
                url = self.globe_url
        else:
            url = self.globe_url
        
        # Add parameters if provided
        params = []
        if lat is not None and lon is not None:
            params.append(f"lat={lat}")
            params.append(f"lon={lon}")
        if country:
            params.append(f"country={urllib.parse.quote(country)}")
        
        if params:
            url += "?" + "&".join(params)
        
        # Open in browser
        try:
            webbrowser.open(url)
            print(f"[GLOBE] Opened globe: {url}")
            return True
        except Exception as e:
            print(f"[GLOBE] Error opening browser: {e}")
            return False
    
    def show_country(self, country_name: str) -> bool:
        """
        Open the globe and navigate to a specific country.
        
        Args:
            country_name: Name of the country
            
        Returns:
            True if successful
        """
        # Try to get country coordinates from Rest Countries API
        try:
            from .free_apis import get_free_apis
            apis = get_free_apis()
            country = apis.get_country_info(country_name)
            
            if country.get("success"):
                lat = country.get("lat", 0)
                lon = country.get("lon", 0)
                return self.open_globe(lat=lat, lon=lon, country=country_name)
        except Exception as e:
            print(f"[GLOBE] Error getting country info: {e}")
        
        # Fallback: just search by name
        return self.open_globe(country=country_name)
    
    def show_region(self, region: str) -> bool:
        """
        Open the globe and show a region.
        
        Args:
            region: Region name (Africa, Americas, Asia, Europe, Oceania)
        """
        # Region center coordinates
        region_centers = {
            "africa": (0, 20),
            "americas": (15, -80),
            "asia": (35, 100),
            "europe": (50, 10),
            "oceania": (-25, 140),
            "north america": (45, -100),
            "south america": (-15, -60),
            "middle east": (30, 45),
            "southeast asia": (10, 110),
        }
        
        region_lower = region.lower()
        if region_lower in region_centers:
            lat, lon = region_centers[region_lower]
            return self.open_globe(lat=lat, lon=lon)
        
        return self.open_globe()


# Singleton instance
_globe_launcher = None

def get_globe_launcher() -> GlobeLauncher:
    """Get the singleton globe launcher instance."""
    global _globe_launcher
    if _globe_launcher is None:
        _globe_launcher = GlobeLauncher()
    return _globe_launcher


def open_globe(lat: float = None, lon: float = None, country: str = None) -> bool:
    """Quick function to open the globe."""
    return get_globe_launcher().open_globe(lat, lon, country)


def show_country(country_name: str) -> bool:
    """Quick function to show a country on the globe."""
    return get_globe_launcher().show_country(country_name)


def show_region(region: str) -> bool:
    """Quick function to show a region on the globe."""
    return get_globe_launcher().show_region(region)


# Test
if __name__ == "__main__":
    print("Testing Monica Globe Launcher...")
    launcher = get_globe_launcher()
    
    # Open globe
    print("\n1. Opening globe...")
    launcher.open_globe()
    
    input("\nPress Enter to show Japan...")
    launcher.show_country("Japan")
    
    input("\nPress Enter to show Europe...")
    launcher.show_region("Europe")
    
    print("\nDone!")

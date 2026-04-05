"""Utility module for Monica AI"""
from .debug import generate_debug_report

# World info utilities
try:
    from .world_info import get_current_time, get_weather, get_world_context, get_timezone_info
except ImportError:
    pass

__all__ = ['generate_debug_report', 'get_current_time', 'get_weather', 'get_world_context']

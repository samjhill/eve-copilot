"""
EVE Copilot - Log-driven voice assistant for EVE Online
"""

__version__ = "0.1.0"
__author__ = "EVE Copilot Team"
__description__ = "Real-time EVE Online log monitoring with voice notifications"
__url__ = "https://github.com/eve-copilot/eve-copilot"
__license__ = "MIT"

# Version info
VERSION = __version__
VERSION_INFO = tuple(int(x) for x in __version__.split('.'))

# Package exports
__all__ = [
    'Config',
    'RulesEngine', 
    'LogWatcher',
    'SpeechNotifier',
    'TrayUI',
    'GameEvent',
    'EventType'
]

"""
Python 3.13 Compatibility Patch
imghdr module was removed in Python 3.13 (PEP 594)
This provides a minimal replacement for python-telegram-bot 13.15
"""
import sys

# Create a minimal imghdr module
class ImghdrModule:
    """Minimal imghdr replacement for python-telegram-bot compatibility"""
    
    @staticmethod
    def what(file, h=None):
        """
        Minimal implementation - just return None
        python-telegram-bot uses this but has fallbacks
        """
        return None

# Inject the fake module
sys.modules['imghdr'] = ImghdrModule()

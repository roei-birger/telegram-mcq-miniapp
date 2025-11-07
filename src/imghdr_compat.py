"""
Python 3.13 Compatibility Patch
imghdr module was removed in Python 3.13 (PEP 594)
This provides a minimal replacement for python-telegram-bot 13.15
"""
import sys

# Create a minimal imghdr module that satisfies python-telegram-bot requirements
class ImghdrModule:
    """Minimal imghdr replacement for python-telegram-bot compatibility"""
    
    @staticmethod
    def what(file, h=None):
        """
        Minimal implementation - just return None
        python-telegram-bot uses this but has fallbacks for file type detection
        """
        return None
    
    # Add any other attributes that might be accessed
    def __getattr__(self, name):
        return None

# Create the module instance
imghdr_module = ImghdrModule()

# Inject the fake module into sys.modules
sys.modules['imghdr'] = imghdr_module

# Suppress the deprecation warning by patching warnings
import warnings
warnings.filterwarnings("ignore", message="'imghdr' is deprecated", category=DeprecationWarning)

# encoding_fix.py
"""
Add this to the TOP of brontobox_api.py to fix Windows encoding issues
"""

import os
import sys

# Fix Windows console encoding for emojis
def fix_console_encoding():
    """Fix Windows console encoding to support Unicode/emojis"""
    if sys.platform.startswith('win'):
        try:
            # Set environment variables for UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['PYTHONUTF8'] = '1'
            
            # Try to set console to UTF-8
            import subprocess
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
            
            # Reconfigure stdout/stderr for UTF-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            
            print("✅ Console encoding fixed for Windows")
            return True
        except Exception as e:
            print(f"⚠️ Could not fix encoding: {e}")
            print("💡 Try running: set PYTHONIOENCODING=utf-8")
            return False
    return True

# Alternative: Safe print function that handles encoding errors
def safe_print(*args, **kwargs):
    """Print function that handles Unicode errors gracefully"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: remove emojis and special characters
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common emojis with text equivalents
                safe_arg = (arg.replace('🦕', '[DINO]')
                             .replace('🔐', '[LOCK]')
                             .replace('📦', '[BOX]')
                             .replace('✅', '[OK]')
                             .replace('❌', '[ERROR]')
                             .replace('⚠️', '[WARNING]')
                             .replace('📧', '[EMAIL]')
                             .replace('💾', '[STORAGE]')
                             .replace('🚀', '[ROCKET]'))
                # Remove any remaining non-ASCII characters
                safe_arg = safe_arg.encode('ascii', 'ignore').decode('ascii')
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)

# Call the fix function at import
if __name__ == "__main__":
    fix_console_encoding()
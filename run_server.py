#!/usr/bin/env python
"""Run the Flask server with better error handling."""

import os
import sys
import traceback

# Set environment variables
os.environ.setdefault('FLASK_SECRET_KEY', 'dev-secret-key-for-development')

try:
    from app import app
    print("[INFO] App imported successfully")
    
    # Test basic functionality
    from utils.grammar_checker import check_grammar
    result = check_grammar("hello")
    print(f"[INFO] Grammar checker test passed: {result.error_count} errors")
    
except Exception as e:
    print(f"[ERROR] Failed to import: {e}")
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    try:
        print("[INFO] Starting server on http://127.0.0.1:5000")
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"[ERROR] Server failed to start: {e}")
        traceback.print_exc()
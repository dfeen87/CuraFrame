"""
CuraFrame Console — Module Entry Point

Launch with: python -m apps.console_streamlit
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        print("Error: streamlit not installed. Run: pip install streamlit")
        sys.exit(1)
    
    app_path = Path(__file__).parent / "app.py"
    sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    sys.exit(stcli.main())

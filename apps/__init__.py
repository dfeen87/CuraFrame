"""
CuraFrame Console — Streamlit Interface

This package contains the interactive, human-facing interface
for CuraFrame constraint evaluation.

Purpose:
    - Visualize constraint reasoning results
    - Explore design space safely and transparently
    - Support documentation and educational use
    - Enable reproducible constraint auditing

This interface:
    - Does NOT generate molecules
    - Does NOT optimize candidates
    - Does NOT provide clinical recommendations
    - Does NOT replace medicinal chemistry expertise

Core logic lives in the `cura_frame` package.
This package is strictly a presentation layer.

Usage:
    Run the console from the command line:
    
        streamlit run apps/console_streamlit/app.py
    
    Or from the package root:
    
        python -m streamlit run apps/console_streamlit/app.py

Philosophy:
    The console makes constraint reasoning *visible* and *auditable*.
    It does not make reasoning *automatic* or *autonomous*.
    
    Human judgment remains central.
"""

__version__ = "1.0.0"
__all__ = []  # This is a Streamlit app, not an importable module

# No imports needed - this is an application package, not a library
# All functionality is in app.py, invoked via streamlit CLI

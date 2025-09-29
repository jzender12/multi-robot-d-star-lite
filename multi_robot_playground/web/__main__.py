"""
Web application entry point for Multi-Robot D* Lite.
"""

import uvicorn
from .main import app

def main():
    """Run the web application."""
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
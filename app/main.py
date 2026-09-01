"""Entry point."""
import tkinter as tk
import sys
from pathlib import Path

# Ensure project root on sys.path when run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.app import MainWindow
from app.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        logger.exception("Failed to create Tk root: %s", e)
        print(f"Erro ao iniciar interface: {e}", file=sys.stderr)
        sys.exit(1)
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

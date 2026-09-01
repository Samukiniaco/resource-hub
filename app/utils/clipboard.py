import tkinter as tk

from app.utils.logger import get_logger

logger = get_logger(__name__)

def copy_to_clipboard(root: tk.Tk | tk.Misc, text: str) -> bool:
    """Copy exact text to system clipboard via Tk."""
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # keep clipboard after window closes on some platforms
        logger.info("Copied to clipboard: %s", text[:120])
        return True
    except Exception as e:
        logger.exception("Clipboard copy failed: %s", e)
        return False

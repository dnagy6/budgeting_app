"""
File: source/gui/dialogs/base_dialog.py
Purpose: Reusable base class for all modal dialog pop-ups in the application.

What this file does:
- Handles standard modal window setup (centering on parent, focus grabbing).
- Establishes uniform padding and spacing constants across all pop-ups.
- Configures default grid column stretching for forms.
- Provides helper methods to easily add form rows (label + entry field).
"""

import tkinter as tk
from tkinter import ttk


class BaseDialog(tk.Toplevel):
    """Base class providing consistent layout, centering, and styling for dialog windows."""

    # Uniform layout styling constants
    OUTER_PADDING = 20
    LABEL_PADX = (0, 10)
    ROW_PADY = 6

    def __init__(self, parent, title: str, width: int = 450, height: int = 280):
        super().__init__(parent)

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)

        # Modal window configuration
        self.transient(parent)
        self.grab_set()

        # Center the dialog window over the main parent window
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        pos_x = parent_x + (parent_w // 2) - (width // 2)
        pos_y = parent_y + (parent_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Outer container frame with standard padding
        self.main_frame = ttk.Frame(self, padding=self.OUTER_PADDING)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure columns: Col 0 = Fixed Labels, Col 1 = Expanding Inputs
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)

    def add_form_row(self, row_idx: int, label_text: str, widget: ttk.Widget) -> ttk.Widget:
        """Utility helper to add a labeled input field with standardized grid placement."""
        ttk.Label(self.main_frame, text=label_text).grid(
            row=row_idx, column=0, sticky=tk.W, pady=self.ROW_PADY, padx=self.LABEL_PADX
        )
        widget.grid(row=row_idx, column=1, sticky=tk.EW, pady=self.ROW_PADY)
        return widget
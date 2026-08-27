"""
File: source/gui/widgets/summary_card.py
Purpose: Top summary card displaying Income Received and Left to Budget metrics.
"""

import tkinter as tk
from source.settings import Theme

class SummaryCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            padx=16,
            pady=14,
            **kwargs
        )

        self._create_ui()

    def _create_ui(self):
        # Column 1: Income Received
        col1 = tk.Frame(self, bg=Theme.BG_CARD)
        col1.pack(side=tk.LEFT, expand=True, anchor="w")
        
        tk.Label(
            col1,
            text="INCOME RECEIVED",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")
        
        self.income_val_label = tk.Label(
            col1,
            text="$0.00",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        self.income_val_label.pack(anchor="w")

        # Column 2: Left to Budget
        col2 = tk.Frame(self, bg=Theme.BG_CARD)
        col2.pack(side=tk.LEFT, expand=True, anchor="w")
        
        tk.Label(
            col2,
            text="LEFT TO BUDGET",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")
        
        self.unallocated_val_label = tk.Label(
            col2,
            text="$0.00",
            font=Theme.FONT_TITLE,
            fg=Theme.SUCCESS,
            bg=Theme.BG_CARD
        )
        self.unallocated_val_label.pack(anchor="w")

    def update_values(self, income: float, unallocated: float):
        """Updates the financial figures and colors the unallocated amount dynamically."""
        self.income_val_label.config(text=f"${income:,.2f}")
        
        if unallocated < 0:
            self.unallocated_val_label.config(
                text=f"${unallocated:,.2f}",
                fg=Theme.DANGER
            )
        else:
            self.unallocated_val_label.config(
                text=f"${unallocated:,.2f}",
                fg=Theme.SUCCESS
            )
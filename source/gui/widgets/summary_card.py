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
            pady=16,
            **kwargs
        )
        self._create_ui()

    def _create_ui(self):
        # Row 1: Left to Budget (Hero Metric)
        tk.Label(
            self,
            text="LEFT TO BUDGET",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        self.unallocated_val_label = tk.Label(
            self,
            text="$0.00",
            font=Theme.FONT_LARGE_TITLE,
            fg=Theme.SUCCESS,
            bg=Theme.BG_CARD
        )
        self.unallocated_val_label.pack(anchor="w", pady=(0, 16))

        # Row 2: Income Received
        tk.Label(
            self,
            text="INCOME RECEIVED",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        self.income_val_label = tk.Label(
            self,
            text="$0.00",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        self.income_val_label.pack(anchor="w", pady=(0, 24))

    def update_values(self, income: float, unallocated: float):
        self.income_val_label.config(text=f"${income:,.2f}")
        
        if unallocated < 0:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", fg=Theme.DANGER)
        else:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", fg=Theme.SUCCESS)
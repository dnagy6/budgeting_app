"""
File: source/gui/widgets/header_view.py
Purpose: Top header bar containing the active month/year selector and reset triggers.
"""

import tkinter as tk
from tkinter import ttk
import calendar
from source.settings import Theme

class HeaderView(tk.Frame):
    def __init__(
        self,
        parent,
        current_month: int,
        current_year: int,
        on_month_click=None,
        on_reset_click=None,
        **kwargs
    ):
        super().__init__(parent, bg=Theme.BG_CARD, padx=20, pady=16, **kwargs)
        
        self.current_month = current_month
        self.current_year = current_year
        self.on_month_click = on_month_click
        self.on_reset_click = on_reset_click

        self._create_ui()

    def _create_ui(self):
        month_name = calendar.month_name[self.current_month]
        
        # 1. Month Selector Dropdown Button
        self.btn_month_selector = tk.Button(
            self,
            text=f"{month_name} {self.current_year} ▾",
            font=Theme.FONT_TITLE,
            relief=tk.FLAT,
            bd=0,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.HOVER_BG,
            activeforeground=Theme.TEXT_PRIMARY,
            cursor="hand2",
            takefocus=0,
            command=self.on_month_click
        )
        self.btn_month_selector.pack(side=tk.LEFT)

        # 2. Reset Budget Options Button
        self.btn_reset_budget = ttk.Button(
            self,
            text="Reset Budget ▾",
            command=self.on_reset_click
        )
        self.btn_reset_budget.pack(side=tk.RIGHT, padx=6)

    def update_header(self, month: int, year: int):
        """Updates the displayed month and year on the selector button."""
        self.current_month = month
        self.current_year = year
        month_name = calendar.month_name[month]
        self.btn_month_selector.config(text=f"{month_name} {year} ▾")
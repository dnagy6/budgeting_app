"""
File: source/gui/widgets/header_view.py
Purpose: Top header bar with month navigation steppers, transaction logging, and budget resets.
"""

import calendar
import tkinter as tk
from source.settings import Theme


class HeaderView(tk.Frame):
    def __init__(
        self,
        parent,
        current_month: int,
        current_year: int,
        on_month_click=None,
        on_prev_month=None,
        on_next_month=None,
        on_today_click=None,
        on_log_transaction=None,
        on_reset_click=None,
        **kwargs
    ):
        super().__init__(parent, bg=Theme.BG_CARD, padx=20, pady=12, **kwargs)

        self.current_month = current_month
        self.current_year = current_year
        self.on_month_click = on_month_click
        self.on_prev_month = on_prev_month
        self.on_next_month = on_next_month
        self.on_today_click = on_today_click
        self.on_log_transaction = on_log_transaction
        self.on_reset_click = on_reset_click

        self._create_ui()

    def _create_ui(self):
        # 1. Left Cluster: Month Navigation Controls
        controls_left = tk.Frame(self, bg=Theme.BG_CARD)
        controls_left.pack(side=tk.LEFT)

        # Previous Month Arrow
        btn_prev = tk.Label(
            controls_left,
            text="‹",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=4,
            pady=2
        )
        btn_prev.pack(side=tk.LEFT)
        if self.on_prev_month:
            btn_prev.bind("<Button-1>", lambda e: self.on_prev_month())
        btn_prev.bind("<Enter>", lambda e: btn_prev.config(fg=Theme.TEXT_PRIMARY))
        btn_prev.bind("<Leave>", lambda e: btn_prev.config(fg=Theme.TEXT_MUTED))

        # Active Month & Year Selector Trigger
        month_name = calendar.month_name[self.current_month]
        self.btn_month_selector = tk.Label(
            controls_left,
            text=f"{month_name} {self.current_year} ▾",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=8,
            pady=2
        )
        self.btn_month_selector.pack(side=tk.LEFT)
        if self.on_month_click:
            self.btn_month_selector.bind("<Button-1>", lambda e: self.on_month_click())
        self.btn_month_selector.bind("<Enter>", lambda e: self.btn_month_selector.config(fg=Theme.ACCENT_PRIMARY))
        self.btn_month_selector.bind("<Leave>", lambda e: self.btn_month_selector.config(fg=Theme.TEXT_PRIMARY))

        # Next Month Arrow
        btn_next = tk.Label(
            controls_left,
            text="›",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=4,
            pady=2
        )
        btn_next.pack(side=tk.LEFT)
        if self.on_next_month:
            btn_next.bind("<Button-1>", lambda e: self.on_next_month())
        btn_next.bind("<Enter>", lambda e: btn_next.config(fg=Theme.TEXT_PRIMARY))
        btn_next.bind("<Leave>", lambda e: btn_next.config(fg=Theme.TEXT_MUTED))

        # Today Quick-Jump Pill
        btn_today = tk.Label(
            controls_left,
            text="Today",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.HOVER_BG,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            cursor="hand2",
            padx=10,
            pady=3
        )
        btn_today.pack(side=tk.LEFT, padx=(12, 0))
        if self.on_today_click:
            btn_today.bind("<Button-1>", lambda e: self.on_today_click())
        btn_today.bind("<Enter>", lambda e: btn_today.config(bg=Theme.BORDER_HAIRLINE))
        btn_today.bind("<Leave>", lambda e: btn_today.config(bg=Theme.HOVER_BG))

        # 2. Right Cluster: Global Actions
        controls_right = tk.Frame(self, bg=Theme.BG_CARD)
        controls_right.pack(side=tk.RIGHT)

        # Primary Action: + Log Transaction
        if self.on_log_transaction:
            btn_log_tx = tk.Label(
                controls_right,
                text="+ Log Transaction",
                font=Theme.FONT_LABEL,
                fg="#ffffff",
                bg=Theme.ACCENT_PRIMARY,
                cursor="hand2",
                padx=14,
                pady=6
            )
            btn_log_tx.pack(side=tk.RIGHT, padx=(12, 0))
            btn_log_tx.bind("<Button-1>", lambda e: self.on_log_transaction())
            btn_log_tx.bind("<Enter>", lambda e: btn_log_tx.config(bg=Theme.BRAND_HIGHLIGHT))
            btn_log_tx.bind("<Leave>", lambda e: btn_log_tx.config(bg=Theme.ACCENT_PRIMARY))

        # Secondary Action: Reset Budget Options
        if self.on_reset_click:
            btn_reset = tk.Label(
                controls_right,
                text="Reset Budget",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                highlightthickness=1,
                highlightbackground=Theme.BORDER_SUBTLE,
                cursor="hand2",
                padx=12,
                pady=5
            )
            btn_reset.pack(side=tk.RIGHT)
            btn_reset.bind("<Button-1>", lambda e: self.on_reset_click())
            btn_reset.bind("<Enter>", lambda e: btn_reset.config(fg=Theme.DANGER, highlightbackground=Theme.DANGER))
            btn_reset.bind("<Leave>", lambda e: btn_reset.config(fg=Theme.TEXT_MUTED, highlightbackground=Theme.BORDER_SUBTLE))

    def update_header(self, month: int, year: int):
        """Updates the month and year label text on change."""
        self.current_month = month
        self.current_year = year
        month_name = calendar.month_name[month]
        self.btn_month_selector.config(text=f"{month_name} {year} ▾")
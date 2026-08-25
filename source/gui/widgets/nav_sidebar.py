"""
File: source/gui/widgets/nav_sidebar.py
Purpose: Left-rail navigation sidebar with view tabs and workspace/profile trigger.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class NavSidebar(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_tab_change: Optional[Callable[[str], None]] = None,
        on_profile_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, bg="#0f172a", width=170, **kwargs)
        self.pack_propagate(False)
        self.on_tab_change = on_tab_change
        self.on_profile_click = on_profile_click
        self.active_tab = "budget"

        self._create_ui()

    def _create_ui(self):
        # 1. Branding Header
        brand_frame = tk.Frame(self, bg="#0f172a")
        brand_frame.pack(fill=tk.X, padx=16, pady=(20, 24))

        lbl_app = tk.Label(
            brand_frame,
            text="EXPENSE",
            font=("Helvetica", 14, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            anchor="w"
        )
        lbl_app.pack(fill=tk.X)

        lbl_sub = tk.Label(
            brand_frame,
            text="TRACKER",
            font=("Helvetica", 10, "bold"),
            fg="#94a3b8",
            bg="#0f172a",
            anchor="w"
        )
        lbl_sub.pack(fill=tk.X)

        # 2. Navigation Tabs
        self.tabs_frame = tk.Frame(self, bg="#0f172a")
        self.tabs_frame.pack(fill=tk.X, padx=10, expand=True, anchor="n")

        self.buttons = {}
        nav_items = [
            ("budget", "Budget"),
            ("accounts", "Accounts"),
            ("insights", "Insights"),
        ]

        for tab_id, label in nav_items:
            btn = tk.Button(
                self.tabs_frame,
                text=label,
                font=("Helvetica", 12, "bold" if tab_id == self.active_tab else "normal"),
                fg="#ffffff" if tab_id == self.active_tab else "#94a3b8",
                bg="#1e293b" if tab_id == self.active_tab else "#0f172a",
                activebackground="#1e293b",
                activeforeground="#ffffff",
                relief=tk.FLAT,
                bd=0,
                anchor="w",
                padx=14,
                pady=10,
                cursor="hand2",
                command=lambda t=tab_id: self.select_tab(t)
            )
            btn.pack(fill=tk.X, pady=3)
            self.buttons[tab_id] = btn

        # 3. Bottom Profile Selector Slot
        bottom_frame = tk.Frame(self, bg="#0f172a")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=16)

        self.btn_profile = tk.Button(
            bottom_frame,
            text="👤 Personal ▾",
            font=("Helvetica", 11),
            fg="#e2e8f0",
            bg="#1e293b",
            activebackground="#334155",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            anchor="w",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._handle_profile_click
        )
        self.btn_profile.pack(fill=tk.X)

    def select_tab(self, tab_id: str):
        self.active_tab = tab_id
        for tid, btn in self.buttons.items():
            if tid == tab_id:
                btn.config(bg="#1e293b", fg="#ffffff", font=("Helvetica", 12, "bold"))
            else:
                btn.config(bg="#0f172a", fg="#94a3b8", font=("Helvetica", 12, "normal"))

        if self.on_tab_change:
            self.on_tab_change(tab_id)

    def _handle_profile_click(self):
        if self.on_profile_click:
            self.on_profile_click()
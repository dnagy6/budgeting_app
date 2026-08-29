"""
File: source/gui/widgets/nav_sidebar.py
Purpose: Left-rail navigation sidebar with view tabs and workspace/profile trigger.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from source.settings import Theme

class NavSidebar(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_tab_change: Optional[Callable[[str], None]] = None,
        on_profile_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, bg=Theme.BG_SIDEBAR, width=170, **kwargs)
        self.pack_propagate(False)
        self.on_tab_change = on_tab_change
        self.on_profile_click = on_profile_click
        self.active_tab = "budget"

        self._create_ui()

    def _create_ui(self):
        # 1. Branding Header
        brand_frame = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        brand_frame.pack(fill=tk.X, padx=16, pady=(20, 24))

        lbl_app = tk.Label(
            brand_frame,
            text="EXPENSE",
            font=("Avenir", 14, "bold"),
            fg=Theme.BRAND_HIGHLIGHT,
            bg=Theme.SIDEBAR_BG,
            anchor="w"
        )
        lbl_app.pack(fill=tk.X)

        lbl_sub = tk.Label(
            brand_frame,
            text="TRACKER",
            font=("Avenir", 10, "bold"),
            fg=Theme.SIDEBAR_TEXT_INACTIVE,
            bg=Theme.SIDEBAR_BG,
            anchor="w"
        )
        lbl_sub.pack(fill=tk.X)

        # 2. Navigation Tabs (Using Frames & Labels to bypass macOS button bugs)
        self.tabs_frame = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        self.tabs_frame.pack(fill=tk.X, padx=10, expand=True, anchor="n")

        self.tab_containers = {}
        self.nav_items = [
            ("budget", "Budget"),
            ("transactions", "Transactions"),
            ("accounts", "Accounts"),
            ("insights", "Insights"),
        ]

        for tab_id, label in self.nav_items:
            is_active = (tab_id == self.active_tab)
            
            # Container Frame for the tab
            container = tk.Frame(
                self.tabs_frame,
                bg=Theme.SIDEBAR_ACTIVE_BG if is_active else Theme.SIDEBAR_BG,
                cursor="hand2"
            )
            container.pack(fill=tk.X, pady=4)

            # Text Label inside container
            lbl = tk.Label(
                container,
                text=label,
                font=("Avenir", 12, "bold" if is_active else "normal"),
                fg=Theme.SIDEBAR_TEXT_ACTIVE if is_active else Theme.SIDEBAR_TEXT_INACTIVE,
                bg=Theme.SIDEBAR_ACTIVE_BG if is_active else Theme.SIDEBAR_BG,
                anchor="w",
                padx=14,
                pady=10
            )
            lbl.pack(fill=tk.BOTH, expand=True)

            # Bind clicks to both container and label for seamless interaction
            for widget in (container, lbl):
                widget.bind("<Button-1>", lambda e, t=tab_id: self.select_tab(t))

            self.tab_containers[tab_id] = (container, lbl)

        # 3. Bottom Profile Selector Slot
        bottom_frame = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=16)

        self.profile_container = tk.Frame(bottom_frame, bg=Theme.SIDEBAR_ACTIVE_BG, cursor="hand2")
        self.profile_container.pack(fill=tk.X)

        lbl_profile = tk.Label(
            self.profile_container,
            text="👤 Personal ▾",
            font=("Avenir", 11),
            fg=Theme.SIDEBAR_TEXT_ACTIVE,
            bg=Theme.SIDEBAR_ACTIVE_BG,
            anchor="w",
            padx=12,
            pady=8
        )
        lbl_profile.pack(fill=tk.BOTH, expand=True)

        for widget in (self.profile_container, lbl_profile):
            widget.bind("<Button-1>", lambda e: self._handle_profile_click())

    def select_tab(self, tab_id: str):
        self.active_tab = tab_id
        for tid, (container, lbl) in self.tab_containers.items():
            if tid == tab_id:
                container.config(bg=Theme.SIDEBAR_ACTIVE_BG)
                lbl.config(bg=Theme.SIDEBAR_ACTIVE_BG, fg=Theme.SIDEBAR_TEXT_ACTIVE, font=("Avenir", 12, "bold"))
            else:
                container.config(bg=Theme.SIDEBAR_BG)
                lbl.config(bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT_INACTIVE, font=("Avenir", 12, "normal"))

        if self.on_tab_change:
            self.on_tab_change(tab_id)

    def _handle_profile_click(self):
        if self.on_profile_click:
            self.on_profile_click()
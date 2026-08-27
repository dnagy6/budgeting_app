"""
File: source/gui/widgets/footer_actions.py
Purpose: Bottom action bar for adding groups, logging transactions, and month rollover.
"""

import tkinter as tk
from tkinter import ttk
from source.settings import Theme

class FooterActions(tk.Frame):
    def __init__(
        self,
        parent,
        on_add_group=None,
        on_log_transaction=None,
        on_rollover=None,
        **kwargs
    ):
        super().__init__(parent, bg=Theme.BG_CARD, padx=20, pady=10, **kwargs)
        
        # Action callbacks
        self.on_add_group = on_add_group
        self.on_log_transaction = on_log_transaction
        self.on_rollover = on_rollover

        self._create_ui()

    def _create_ui(self):
        # 1. Add Group Button
        btn_add_group = ttk.Button(
            self,
            text="+ Add Category Group",
            command=self.on_add_group
        )
        btn_add_group.pack(side=tk.LEFT, padx=(0, 6))

        # 2. Log Transaction Button
        btn_log_tx = ttk.Button(
            self,
            text="Log Transaction",
            command=self.on_log_transaction
        )
        btn_log_tx.pack(side=tk.LEFT, padx=6)

        # 3. Close Month & Roll Over Button
        btn_rollover = ttk.Button(
            self,
            text="Close Month & Roll Over",
            command=self.on_rollover
        )
        btn_rollover.pack(side=tk.RIGHT)
"""
File: source/gui/widgets/transaction_card.py
Purpose: A high-density, single-line row for processing transactions.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional
from source.settings import Theme

class TransactionCard(tk.Frame):
    def __init__(
        self,
        parent,
        tx,
        current_tab: str,
        cat_id_to_name: Dict[int, str],
        cat_name_to_id: Dict[str, int],
        on_track: Callable[[int, str], None],
        on_delete: Callable[[int], None],
        on_restore: Callable[[int], None],
        on_hard_delete: Callable[[int], None],
        **kwargs
    ):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            **kwargs
        )
        self.tx = tx
        self.current_tab = current_tab
        self.cat_id_to_name = cat_id_to_name
        self.cat_name_to_id = cat_name_to_id
        
        self.on_track = on_track
        self.on_delete = on_delete
        self.on_restore = on_restore
        self.on_hard_delete = on_hard_delete

        self._create_ui()
        self._bind_hover_events()

    def _create_ui(self):
        # Enforce strict pixel widths for perfect cross-card alignment
        self.columnconfigure(0, minsize=240, weight=0) # Merchant
        self.columnconfigure(1, weight=0) # Category Dropdown
        self.columnconfigure(2, minsize=140, weight=1)              # Amount (Pushes actions right)
        self.columnconfigure(3, minsize=140, weight=0) # Actions

        # Column 0: Merchant Name & Date
        merchant_frame = tk.Frame(self, bg=Theme.BG_CARD)
        merchant_frame.grid(row=0, column=0, sticky="w", padx=(16, 8), pady=8)
        
        tk.Label(
            merchant_frame,
            text=self.tx.note or "Unnamed Transaction",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        tk.Label(
            merchant_frame,
            text=self.tx.trans_date,
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        # Column 1: Category Selector (Disabled if not in 'new' tab)
        self.cat_var = tk.StringVar()
        if self.tx.category_id and self.tx.category_id in self.cat_id_to_name:
            self.cat_var.set(self.cat_id_to_name[self.tx.category_id])

        # Sort categories alphabetically, but pin Ready to Assign/Income to the top
        cat_names = sorted(list(self.cat_name_to_id.keys()))
        if "Ready to Assign" in cat_names:
            cat_names.insert(0, cat_names.pop(cat_names.index("Ready to Assign")))

        self.cb_category = ttk.Combobox(
            self,
            textvariable=self.cat_var,
            values=cat_names,
            state="readonly" if self.current_tab == "new" else "disabled",
            width=20
        )
        self.cb_category.grid(row=0, column=1, sticky="w", padx=8, pady=8)

        # Column 2: Amount (Flipped logic: expenses are > 0, income/refunds are < 0)
        tx_amount = float(self.tx.amount)
        is_positive_cashflow = tx_amount < 0 
        display_amount = abs(tx_amount)
        
        amount_text = f"+${display_amount:,.2f}" if is_positive_cashflow else f"-${display_amount:,.2f}"
        amount_color = Theme.SUCCESS if is_positive_cashflow else Theme.TEXT_PRIMARY
        amount_font = Theme.FONT_HEADER if is_positive_cashflow else Theme.FONT_BODY

        tk.Label(
            self,
            text=amount_text,
            font=amount_font,
            fg=amount_color,
            bg=Theme.BG_CARD
        ).grid(row=0, column=2, sticky="e", padx=16, pady=8)

        # Column 3: Action Buttons (Dynamic based on tab)
        action_frame = tk.Frame(self, bg=Theme.BG_CARD)
        action_frame.grid(row=0, column=3, sticky="e", padx=(8, 16), pady=8)
        self._build_action_buttons(action_frame)

    def _build_action_buttons(self, parent_frame):
        if self.current_tab == "new":
            self._make_btn(parent_frame, "Track", Theme.SUCCESS, lambda: self.on_track(self.tx.id, self.cat_var.get())).pack(side=tk.LEFT, padx=4)
            self._make_btn(parent_frame, "Delete", Theme.DANGER, lambda: self.on_delete(self.tx.id)).pack(side=tk.LEFT, padx=4)
        
        elif self.current_tab == "deleted":
            self._make_btn(parent_frame, "Restore", Theme.TEXT_PRIMARY, lambda: self.on_restore(self.tx.id)).pack(side=tk.LEFT, padx=4)
            self._make_btn(parent_frame, "Perm Delete", Theme.DANGER, lambda: self.on_hard_delete(self.tx.id)).pack(side=tk.LEFT, padx=4)
        
        else: # tracked
            self._make_btn(parent_frame, "Delete", Theme.DANGER, lambda: self.on_delete(self.tx.id)).pack(side=tk.LEFT, padx=4)

    def _make_btn(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            font=Theme.FONT_BODY,
            fg=color,
            bg=Theme.BG_CARD,
            activeforeground=color,
            activebackground=Theme.HOVER_BG,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=command
        )

    def _bind_hover_events(self):
        """Changes the background color of the entire row on hover."""
        widgets_to_bind = [self] + [w for w in self.winfo_children() if not isinstance(w, ttk.Combobox)]
        
        def on_enter(e):
            for w in widgets_to_bind:
                try: w.config(bg=Theme.HOVER_BG)
                except: pass

        def on_leave(e):
            for w in widgets_to_bind:
                try: w.config(bg=Theme.BG_CARD)
                except: pass

        for w in widgets_to_bind:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
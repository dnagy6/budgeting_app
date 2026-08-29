"""
File: source/gui/widgets/transaction_card.py
Purpose: Isolated card widget for rendering transactions across different stream tabs using Theme tokens.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from source.settings import Theme

class TransactionCard(tk.Frame):
    def __init__(
        self,
        parent,
        tx,
        current_tab: str,
        cat_id_to_name: Dict[int, str],
        cat_name_to_id: Dict[str, int],
        on_track: Callable,
        on_ignore: Callable,
        on_delete: Callable,
        on_restore: Callable,
        on_hard_delete: Callable,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            bd=0,
            **kwargs
        )
        self.tx = tx
        self.current_tab = current_tab
        self.cat_id_to_name = cat_id_to_name
        self.cat_name_to_id = cat_name_to_id
        self.on_track = on_track
        self.on_ignore = on_ignore
        self.on_delete = on_delete
        self.on_restore = on_restore
        self.on_hard_delete = on_hard_delete

        self._create_ui()

    def _create_ui(self):
        self.pack(fill=tk.X, pady=(0, 8), padx=2)

        # Top Row: Date Badge & Amount
        top_row = tk.Frame(self, bg=Theme.BG_CARD)
        top_row.pack(fill=tk.X, padx=10, pady=(8, 4))

        date_str = self.tx.trans_date.strftime("%b %d") if self.tx.trans_date else "No Date"
        lbl_date = tk.Label(
            top_row,
            text=date_str,
            font=Theme.FONT_LABEL,
            bg=Theme.HOVER_BG,
            fg=Theme.TEXT_MUTED,
            padx=6,
            pady=2
        )
        lbl_date.pack(side=tk.LEFT)

        amt = float(self.tx.amount)
        lbl_amt = tk.Label(
            top_row,
            text=f"${amt:,.2f}",
            font=Theme.FONT_HEADER,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY
        )
        lbl_amt.pack(side=tk.RIGHT)

        # Middle Row: Note / Merchant
        lbl_note = tk.Label(
            self,
            text=self.tx.note or "Bank Transaction",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        lbl_note.pack(fill=tk.X, padx=10, pady=(0, 6))

        # Bottom Row: Category and Action Controls
        bottom_row = tk.Frame(self, bg=Theme.BG_CARD)
        bottom_row.pack(fill=tk.X, padx=10, pady=(0, 8))

        # TAB 1: NEW (Staged settlements awaiting envelope assignment)
        if self.current_tab == "new":
            selected_cat_var = tk.StringVar()
            current_cat_name = self.cat_id_to_name.get(self.tx.category_id, "")
            selected_cat_var.set(current_cat_name)

            cat_options = sorted(list(self.cat_name_to_id.keys()))
            cmb_category = ttk.Combobox(
                bottom_row,
                textvariable=selected_cat_var,
                values=cat_options,
                state="readonly",
                font=Theme.FONT_LABEL,
                width=14
            )
            cmb_category.pack(side=tk.LEFT, padx=(0, 6))

            actions = tk.Frame(bottom_row, bg=Theme.BG_CARD)
            actions.pack(side=tk.RIGHT)

            btn_track = tk.Button(
                actions,
                text="Track",
                font=Theme.FONT_LABEL,
                fg=Theme.SUCCESS,
                bg=Theme.BG_CARD,
                activeforeground=Theme.SUCCESS,
                activebackground=Theme.BG_CARD,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self.on_track(self.tx.id, selected_cat_var.get(), self.cat_name_to_id)
            )
            btn_track.pack(side=tk.LEFT, padx=(0, 4))

            btn_ignore = tk.Button(
                actions,
                text="✕",
                font=Theme.FONT_HEADER,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                activeforeground=Theme.DANGER,
                activebackground=Theme.BG_CARD,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self.on_ignore(self.tx.id)
            )
            btn_ignore.pack(side=tk.LEFT)

        # TAB 2: PENDING (Read-Only: Holds awaiting bank clearance)
        elif self.current_tab == "pending":
            lbl_pending_badge = tk.Label(
                bottom_row,
                text="⏳ Pending Clearance",
                font=Theme.FONT_LABEL,
                fg="#d97706",
                bg="#fef3c7",
                padx=6,
                pady=2
            )
            lbl_pending_badge.pack(side=tk.LEFT)

            lbl_pending_hint = tk.Label(
                bottom_row,
                text="Auto-settles when posted",
                font=Theme.FONT_ITALIC_MUTED,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_pending_hint.pack(side=tk.RIGHT)

        # TAB 3: TRACKED (Confirmed and active in budget)
        elif self.current_tab == "tracked":
            cat_display = self.cat_id_to_name.get(self.tx.category_id, "Uncategorized")
            lbl_cat = tk.Label(
                bottom_row,
                text=f"📁 {cat_display}",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_cat.pack(side=tk.LEFT)

            btn_del = tk.Button(
                bottom_row,
                text="Delete",
                font=Theme.FONT_LABEL,
                fg=Theme.DANGER,
                bg=Theme.BG_CARD,
                activeforeground=Theme.DANGER,
                activebackground=Theme.BG_CARD,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self.on_delete(self.tx.id)
            )
            btn_del.pack(side=tk.RIGHT)

        # TAB 4: DELETED (Soft-deleted transactions)
        elif self.current_tab == "deleted":
            cat_display = self.cat_id_to_name.get(self.tx.category_id, "Uncategorized")
            lbl_cat = tk.Label(
                bottom_row,
                text=f"📁 {cat_display}",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_cat.pack(side=tk.LEFT)

            actions = tk.Frame(bottom_row, bg=Theme.BG_CARD)
            actions.pack(side=tk.RIGHT)

            btn_restore = tk.Button(
                actions,
                text="Restore",
                font=Theme.FONT_LABEL,
                fg=Theme.ACCENT_PRIMARY,
                bg=Theme.BG_CARD,
                activeforeground=Theme.ACCENT_PRIMARY,
                activebackground=Theme.BG_CARD,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self.on_restore(self.tx.id)
            )
            btn_restore.pack(side=tk.LEFT, padx=(0, 6))

            btn_hard_del = tk.Button(
                actions,
                text="✕",
                font=Theme.FONT_LABEL,
                fg=Theme.DANGER,
                bg=Theme.BG_CARD,
                activeforeground=Theme.DANGER,
                activebackground=Theme.BG_CARD,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self.on_hard_delete(self.tx.id)
            )
            btn_hard_del.pack(side=tk.LEFT)
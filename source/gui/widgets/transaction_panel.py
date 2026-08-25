"""
File: source/gui/widgets/transaction_panel.py
Purpose: Right-rail transaction stream with subtabs, status queues, and inline actions.
"""

import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from source.services.budget_service import BudgetService


class TransactionPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: BudgetService,
        on_data_changed: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.service = service
        self.on_data_changed = on_data_changed
        self.current_tab = "tracked"  # "new", "tracked", "deleted", "pending"
        self.current_year = 2026
        self.current_month = 8

        self._create_header_ui()
        self._create_tabs_ui()
        self._create_scrollable_stream()
        self._create_footer_ui()

    def set_period(self, year: int, month: int):
        self.current_year = year
        self.current_month = month
        self.refresh()

    def _create_header_ui(self):
        self.header_frame = tk.Frame(self, bg="#ffffff", padx=16, pady=14)
        self.header_frame.pack(fill=tk.X)

        self.lbl_title = tk.Label(
            self.header_frame,
            text="Transactions",
            font=("Helvetica", 14, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        self.lbl_title.pack(side=tk.LEFT)

        self.lbl_month_tag = tk.Label(
            self.header_frame,
            text="",
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#64748b"
        )
        self.lbl_month_tag.pack(side=tk.RIGHT)

    def _create_tabs_ui(self):
        # Container with subtle background pill wrapper
        self.tabs_bar = tk.Frame(self, bg="#f1f5f9", padx=3, pady=3)
        self.tabs_bar.pack(fill=tk.X, padx=12, pady=(0, 8))

        # 4 equal-width grid columns
        for col in range(4):
            self.tabs_bar.columnconfigure(col, weight=1, uniform="tab_group")

        self.tab_buttons = {}
        tabs = [
            ("new", "New"),
            ("tracked", "Tracked"),
            ("deleted", "Deleted"),
            ("pending", "Pending"),
        ]

        for col_idx, (tab_id, label) in enumerate(tabs):
            btn = tk.Button(
                self.tabs_bar,
                text=label,
                font=("Helvetica", 9),
                fg="#64748b",
                bg="#f1f5f9",
                activebackground="#ffffff",
                relief=tk.FLAT,
                bd=0,
                padx=2,
                pady=4,
                cursor="hand2",
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.grid(row=0, column=col_idx, sticky="nsew", padx=1)
            self.tab_buttons[tab_id] = btn

    def _create_scrollable_stream(self):
        container = tk.Frame(self, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.canvas = tk.Canvas(container, bg="#ffffff", bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.stream_inner_frame = tk.Frame(self.canvas, bg="#ffffff")

        self.stream_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.stream_inner_frame, anchor="nw")

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_footer_ui(self):
        footer = tk.Frame(self, bg="#ffffff", padx=12, pady=10, highlightthickness=1, highlightbackground="#f1f5f9")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_sync = tk.Label(
            footer,
            text="⚡ Plaid Stream Ready",
            font=("Helvetica", 9, "italic"),
            fg="#94a3b8",
            bg="#ffffff"
        )
        lbl_sync.pack(side=tk.LEFT)

    def switch_tab(self, tab_id: str):
        self.current_tab = tab_id
        self.refresh()

    def refresh(self):
        month_name = calendar.month_name[self.current_month]
        self.lbl_month_tag.config(text=f"{month_name} {self.current_year}")

        # 1. Update tab badge counts and active tab styling
        counts = self.service.get_transaction_status_counts(self.current_year, self.current_month)
        for tid, btn in self.tab_buttons.items():
            cnt = counts.get(tid, 0)
            btn_text = f"{tid.capitalize()} ({cnt})" if cnt > 0 else tid.capitalize()

            if tid == self.current_tab:
                btn.config(
                    text=btn_text,
                    bg="#ffffff",
                    fg="#0f172a",
                    font=("Helvetica", 9, "bold"),
                    relief=tk.SOLID,
                    bd=1,
                    highlightbackground="#e2e8f0"
                )
            else:
                btn.config(
                    text=btn_text,
                    bg="#f1f5f9",
                    fg="#64748b",
                    font=("Helvetica", 9, "normal"),
                    relief=tk.FLAT,
                    bd=0
                )

        # 2. Clear items
        for child in self.stream_inner_frame.winfo_children():
            child.destroy()

        # 3. Load transactions for active tab
        transactions = self.service.get_transactions_by_status(
            self.current_year,
            self.current_month,
            status=self.current_tab
        )

        if not transactions:
            lbl_empty = tk.Label(
                self.stream_inner_frame,
                text=f"No {self.current_tab} transactions for {month_name}.",
                font=("Helvetica", 9, "italic"),
                fg="#94a3b8",
                bg="#ffffff",
                pady=30
            )
            lbl_empty.pack(fill=tk.BOTH, expand=True)
            return

        # Fetch category map for labeling
        all_cats = {c.id: c.name for c in self.service.repository.get_all_categories(include_archived=True)}

        # 4. Render transaction cards
        for tx in transactions:
            self._create_transaction_card(tx, all_cats.get(tx.category_id, "Uncategorized"))

    def _create_transaction_card(self, tx, cat_name: str):
        card = tk.Frame(self.stream_inner_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#f1f5f9", padx=8, pady=8)
        card.pack(fill=tk.X, pady=(0, 6))

        # Top Row: Date Badge & Amount
        top_row = tk.Frame(card, bg="#ffffff")
        top_row.pack(fill=tk.X)

        date_str = tx.trans_date.strftime("%b %d") if tx.trans_date else "No Date"
        lbl_date = tk.Label(
            top_row,
            text=date_str,
            font=("Helvetica", 9, "bold"),
            bg="#f1f5f9",
            fg="#475569",
            padx=5,
            pady=1
        )
        lbl_date.pack(side=tk.LEFT)

        # Amount styling
        amt = float(tx.amount)
        amt_str = f"+${amt:,.2f}" if self.current_tab == "new" else f"${amt:,.2f}"
        lbl_amt = tk.Label(
            top_row,
            text=amt_str,
            font=("Helvetica", 10, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        lbl_amt.pack(side=tk.RIGHT)

        # Middle Row: Note / Description
        note_text = tx.note if tx.note else "Transaction"
        lbl_note = tk.Label(
            card,
            text=note_text,
            font=("Helvetica", 10),
            fg="#1e293b",
            bg="#ffffff",
            anchor="w"
        )
        lbl_note.pack(fill=tk.X, pady=(4, 2))

        # Bottom Row: Category Tag & Action Triggers
        bottom_row = tk.Frame(card, bg="#ffffff")
        bottom_row.pack(fill=tk.X, pady=(2, 0))

        lbl_cat = tk.Label(
            bottom_row,
            text=f"📁 {cat_name}",
            font=("Helvetica", 8),
            fg="#64748b",
            bg="#ffffff"
        )
        lbl_cat.pack(side=tk.LEFT)

        # Context Actions per Tab
        actions_frame = tk.Frame(bottom_row, bg="#ffffff")
        actions_frame.pack(side=tk.RIGHT)

        if self.current_tab == "tracked":
            btn_del = tk.Button(
                actions_frame,
                text="Delete",
                font=("Helvetica", 8),
                fg="#ef4444",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_soft_delete(tx.id)
            )
            btn_del.pack(side=tk.LEFT)

        elif self.current_tab == "deleted":
            btn_restore = tk.Button(
                actions_frame,
                text="Restore",
                font=("Helvetica", 8),
                fg="#0284c7",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_restore(tx.id)
            )
            btn_restore.pack(side=tk.LEFT, padx=(0, 6))

            btn_hard_del = tk.Button(
                actions_frame,
                text="✕",
                font=("Helvetica", 8),
                fg="#ef4444",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_hard_delete(tx.id)
            )
            btn_hard_del.pack(side=tk.LEFT)

        elif self.current_tab in ("new", "pending"):
            btn_track = tk.Button(
                actions_frame,
                text="Track",
                font=("Helvetica", 8, "bold"),
                fg="#16a34a",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_track_incoming(tx.id)
            )
            btn_track.pack(side=tk.LEFT, padx=(0, 6))

            btn_del = tk.Button(
                actions_frame,
                text="Ignore",
                font=("Helvetica", 8),
                fg="#ef4444",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_soft_delete(tx.id)
            )
            btn_del.pack(side=tk.LEFT)

    def _handle_soft_delete(self, tx_id: int):
        self.service.update_transaction_status(tx_id, "deleted")
        self.on_data_changed()

    def _handle_restore(self, tx_id: int):
        self.service.update_transaction_status(tx_id, "tracked")
        self.on_data_changed()

    def _handle_track_incoming(self, tx_id: int):
        self.service.update_transaction_status(tx_id, "tracked")
        self.on_data_changed()

    def _handle_hard_delete(self, tx_id: int):
            """Prompts confirmation on root toplevel and permanently deletes transaction."""
            top = self.winfo_toplevel()
            if messagebox.askyesno("Confirm Permanent Delete", "Are you sure you want to permanently delete this transaction?\n\nThis cannot be undone.", parent=top):
                self.service.hard_delete_transaction(tx_id)
                self.on_data_changed()
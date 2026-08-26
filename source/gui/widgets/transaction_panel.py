"""
File: source/gui/widgets/transaction_panel.py
Purpose: Right-rail transaction stream with bank sync trigger, status queues, 
         read-only pending status, and active mousewheel scrolling.
"""

import calendar
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional
from source.services.budget_service import BudgetService
from source.services.transaction_stream_service import TransactionStreamService
from source.services.mock_stream_generator import MockStreamGenerator


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
        self.stream_service = TransactionStreamService(self.service.repository)
        self.on_data_changed = on_data_changed
        self.current_tab = "new"
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
        self.tabs_bar = tk.Frame(self, bg="#f1f5f9", padx=3, pady=3)
        self.tabs_bar.pack(fill=tk.X, padx=12, pady=(0, 8))

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
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.canvas = tk.Canvas(self.container, bg="#ffffff", bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.stream_inner_frame = tk.Frame(self.canvas, bg="#ffffff")

        self.stream_inner_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.stream_inner_frame, anchor="nw")

        self.canvas.bind(
            "<Configure>",
            lambda e: (
                self.canvas.itemconfig(self.canvas_window, width=e.width),
                self._update_scroll_region()
            )
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel & Trackpad Scroll Bindings
        self.container.bind("<Enter>", self._bind_mousewheel)
        self.container.bind("<Leave>", self._unbind_mousewheel)

    def _update_scroll_region(self, event=None):
        """Ensures the scroll region anchors cleanly to the top."""
        self.canvas.update_idletasks()
        content_height = self.stream_inner_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()

        if content_height <= canvas_height:
            self.canvas.yview_moveto(0.0)
            self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), canvas_height))
        else:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self._on_scroll_step(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self._on_scroll_step(1))

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        content_height = self.stream_inner_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        if content_height <= canvas_height:
            return

        if platform.system() == "Darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_scroll_step(self, step: int):
        content_height = self.stream_inner_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        if content_height > canvas_height:
            self.canvas.yview_scroll(step, "units")

    def _create_footer_ui(self):
        footer = tk.Frame(self, bg="#ffffff", padx=12, pady=10, highlightthickness=1, highlightbackground="#f1f5f9")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_sync = tk.Button(
            footer,
            text="⚡ Sync Bank Feed",
            font=("Helvetica", 10, "bold"),
            fg="#0284c7",
            bg="#f0f9ff",
            activeforeground="#0369a1",
            activebackground="#e0f2fe",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=7,
            cursor="hand2",
            command=self._handle_simulate_sync
        )
        btn_sync.pack(fill=tk.X)

    def switch_tab(self, tab_id: str):
        self.current_tab = tab_id
        self.refresh()

    def refresh(self):
        month_name = calendar.month_name[self.current_month]
        self.lbl_month_tag.config(text=f"{month_name} {self.current_year}")

        # 1. Update tab badge counts and active tab style
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

        # 2. Clear items and reset scroll to top
        for child in self.stream_inner_frame.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0.0)

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
                pady=40
            )
            lbl_empty.pack(fill=tk.BOTH, expand=True)
            return

        # Fetch category map
        all_categories = self.service.repository.get_all_categories(include_archived=False)
        cat_id_to_name = {c.id: c.name for c in all_categories}
        cat_name_to_id = {c.name: c.id for c in all_categories}

        # 4. Render transaction cards
        for tx in transactions:
            self._create_transaction_card(tx, cat_id_to_name, cat_name_to_id)

    def _create_transaction_card(
        self,
        tx,
        cat_id_to_name: Dict[int, str],
        cat_name_to_id: Dict[str, int]
    ):
        card = tk.Frame(
            self.stream_inner_frame,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#e2e8f0",
            padx=10,
            pady=8
        )
        card.pack(fill=tk.X, pady=(0, 8))

        # Top Row: Date Badge & Amount
        top_row = tk.Frame(card, bg="#ffffff")
        top_row.pack(fill=tk.X)

        date_str = tx.trans_date.strftime("%b %d") if tx.trans_date else "No Date"
        lbl_date = tk.Label(
            top_row,
            text=date_str,
            font=("Helvetica", 8, "bold"),
            bg="#f1f5f9",
            fg="#475569",
            padx=5,
            pady=1
        )
        lbl_date.pack(side=tk.LEFT)

        amt = float(tx.amount)
        lbl_amt = tk.Label(
            top_row,
            text=f"${amt:,.2f}",
            font=("Helvetica", 10, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        lbl_amt.pack(side=tk.RIGHT)

        # Middle Row: Note / Merchant
        lbl_note = tk.Label(
            card,
            text=tx.note or "Bank Transaction",
            font=("Helvetica", 10, "bold"),
            fg="#1e293b",
            bg="#ffffff",
            anchor="w"
        )
        lbl_note.pack(fill=tk.X, pady=(4, 6))

        # Bottom Row: Category and Action Controls
        bottom_row = tk.Frame(card, bg="#ffffff")
        bottom_row.pack(fill=tk.X)

        # TAB 1: NEW (Staged settlements awaiting envelope assignment)
        if self.current_tab == "new":
            selected_cat_var = tk.StringVar()
            current_cat_name = cat_id_to_name.get(tx.category_id, "")
            selected_cat_var.set(current_cat_name)

            cat_options = sorted(list(cat_name_to_id.keys()))
            cmb_category = ttk.Combobox(
                bottom_row,
                textvariable=selected_cat_var,
                values=cat_options,
                state="readonly",
                font=("Helvetica", 9),
                width=14
            )
            cmb_category.pack(side=tk.LEFT, padx=(0, 6))

            actions = tk.Frame(bottom_row, bg="#ffffff")
            actions.pack(side=tk.RIGHT)

            btn_track = tk.Button(
                actions,
                text="Track",
                font=("Helvetica", 9, "bold"),
                fg="#16a34a",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_assign_and_track(tx.id, selected_cat_var.get(), cat_name_to_id)
            )
            btn_track.pack(side=tk.LEFT, padx=(0, 4))

            btn_ignore = tk.Button(
                actions,
                text="✕",
                font=("Helvetica", 9),
                fg="#94a3b8",
                bg="#ffffff",
                activeforeground="#ef4444",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_soft_delete(tx.id)
            )
            btn_ignore.pack(side=tk.LEFT)

        # TAB 2: PENDING (Read-Only: Holds awaiting bank clearance)
        elif self.current_tab == "pending":
            lbl_pending_badge = tk.Label(
                bottom_row,
                text="⏳ Pending Clearance",
                font=("Helvetica", 8, "bold"),
                fg="#d97706",
                bg="#fef3c7",
                padx=6,
                pady=2
            )
            lbl_pending_badge.pack(side=tk.LEFT)

            lbl_pending_hint = tk.Label(
                bottom_row,
                text="Auto-settles when posted",
                font=("Helvetica", 8, "italic"),
                fg="#94a3b8",
                bg="#ffffff"
            )
            lbl_pending_hint.pack(side=tk.RIGHT)

        # TAB 3: TRACKED (Confirmed and active in budget)
        elif self.current_tab == "tracked":
            cat_display = cat_id_to_name.get(tx.category_id, "Uncategorized")
            lbl_cat = tk.Label(
                bottom_row,
                text=f"📁 {cat_display}",
                font=("Helvetica", 9),
                fg="#64748b",
                bg="#ffffff"
            )
            lbl_cat.pack(side=tk.LEFT)

            btn_del = tk.Button(
                bottom_row,
                text="Delete",
                font=("Helvetica", 8),
                fg="#ef4444",
                bg="#ffffff",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                command=lambda: self._handle_soft_delete(tx.id)
            )
            btn_del.pack(side=tk.RIGHT)

        # TAB 4: DELETED (Soft-deleted transactions)
        elif self.current_tab == "deleted":
            cat_display = cat_id_to_name.get(tx.category_id, "Uncategorized")
            lbl_cat = tk.Label(
                bottom_row,
                text=f"📁 {cat_display}",
                font=("Helvetica", 9),
                fg="#94a3b8",
                bg="#ffffff"
            )
            lbl_cat.pack(side=tk.LEFT)

            actions = tk.Frame(bottom_row, bg="#ffffff")
            actions.pack(side=tk.RIGHT)

            btn_restore = tk.Button(
                actions,
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
                actions,
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

    def _handle_simulate_sync(self):
        batch = MockStreamGenerator.generate_batch(
            count=4,
            year=self.current_year,
            month=self.current_month
        )
        self.stream_service.ingest_payload(batch)
        self.refresh()
        self.on_data_changed()

    def _handle_assign_and_track(
        self,
        tx_id: int,
        category_name: str,
        cat_name_to_id: Dict[str, int]
    ):
        top = self.winfo_toplevel()
        if not category_name or category_name not in cat_name_to_id:
            messagebox.showwarning(
                "Select Category",
                "Please select an envelope category before tracking this transaction.",
                parent=top
            )
            return

        cat_id = cat_name_to_id[category_name]
        self.service.repository.assign_transaction_category(tx_id, cat_id)
        self.refresh()
        self.on_data_changed()

    def _handle_soft_delete(self, tx_id: int):
        self.service.update_transaction_status(tx_id, "deleted")
        self.refresh()
        self.on_data_changed()

    def _handle_restore(self, tx_id: int):
        self.service.update_transaction_status(tx_id, "tracked")
        self.refresh()
        self.on_data_changed()

    def _handle_hard_delete(self, tx_id: int):
        top = self.winfo_toplevel()
        if messagebox.askyesno(
            "Confirm Permanent Delete",
            "Are you sure you want to permanently delete this transaction?\n\nThis cannot be undone.",
            parent=top
        ):
            self.service.hard_delete_transaction(tx_id)
            self.refresh()
            self.on_data_changed()
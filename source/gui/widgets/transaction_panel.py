"""
File: source/gui/widgets/transaction_panel.py
Purpose: Right-rail transaction stream container leveraging Theme tokens and the ScrollableCanvasMixin.
"""

import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional
from source.settings import Theme

# Widgets
from source.gui.widgets.transaction_card import TransactionCard
from source.gui.widgets.scrollable_canvas_mixin import ScrollableCanvasMixin

# Services
from source.services.budget_service import BudgetService
from source.services.transaction_stream_service import TransactionStreamService

class TransactionPanel(tk.Frame, ScrollableCanvasMixin):
    def __init__(
        self,
        parent: tk.Widget,
        service: BudgetService,
        on_data_changed: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)
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
        self.header_frame = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=14)
        self.header_frame.pack(fill=tk.X)

        self.lbl_title = tk.Label(
            self.header_frame,
            text="Transactions",
            font=Theme.FONT_LARGE_TITLE,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY
        )
        self.lbl_title.pack(side=tk.LEFT)

        self.lbl_month_tag = tk.Label(
            self.header_frame,
            text="",
            font=Theme.FONT_HEADER,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_MUTED
        )
        self.lbl_month_tag.pack(side=tk.RIGHT)

    def _create_tabs_ui(self):
        self.tabs_bar = tk.Frame(self, bg=Theme.HOVER_BG, padx=3, pady=3)
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
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.HOVER_BG,
                activebackground=Theme.BG_CARD,
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
        self.container = tk.Frame(self, bg=Theme.BG_CARD)
        self.container.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.canvas = tk.Canvas(self.container, bg=Theme.BG_CARD, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.stream_inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.stream_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Initialize mixin bindings
        self._init_scrollable_mixin(self.container, self.canvas, self.stream_inner_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_footer_ui(self):
        footer = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=10, highlightthickness=1, highlightbackground=Theme.HOVER_BG)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        btn_sync = tk.Button(
            footer,
            text="⚡ Sync Bank Feed",
            font=Theme.FONT_HEADER,
            fg=Theme.ACCENT_PRIMARY,
            bg=Theme.ACCENT_POWDER,
            activeforeground=Theme.BRAND_HIGHLIGHT,
            activebackground=Theme.ACCENT_POWDER,
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

        state = self.stream_service.get_stream_view_state(
            budget_service=self.service,
            year=self.current_year, 
            month=self.current_month, 
            active_tab=self.current_tab
        )

        for tid, btn in self.tab_buttons.items():
            cnt = state.counts.get(tid, 0)
            btn_text = f"{tid.capitalize()} ({cnt})" if cnt > 0 else tid.capitalize()

            if tid == self.current_tab:
                btn.config(
                    text=btn_text,
                    bg=Theme.BG_CARD,
                    fg=Theme.TEXT_PRIMARY,
                    font=Theme.FONT_HEADER,
                    relief=tk.SOLID,
                    bd=1,
                    highlightbackground=Theme.BORDER_SUBTLE
                )
            else:
                btn.config(
                    text=btn_text,
                    bg=Theme.HOVER_BG,
                    fg=Theme.TEXT_MUTED,
                    font=Theme.FONT_LABEL,
                    relief=tk.FLAT,
                    bd=0
                )

        for child in self.stream_inner_frame.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0.0)

        if not state.transactions:
            lbl_empty = tk.Label(
                self.stream_inner_frame,
                text=f"No {self.current_tab} transactions for {month_name}.",
                font=Theme.FONT_ITALIC_MUTED,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                pady=40
            )
            lbl_empty.pack(fill=tk.BOTH, expand=True)
            return

        for tx in state.transactions:
            card = TransactionCard(
                self.stream_inner_frame,
                tx=tx,
                current_tab=self.current_tab,
                cat_id_to_name=state.cat_id_to_name,
                cat_name_to_id=state.cat_name_to_id,
                on_track=self._handle_assign_and_track,
                # on_ignore=self._handle_soft_delete,
                on_delete=self._handle_soft_delete,
                on_restore=self._handle_restore,
                on_hard_delete=self._handle_hard_delete
            )
            card.pack(fill=tk.X, pady=2, ipady=4)

    def _handle_simulate_sync(self):
        self.stream_service.simulate_sync(
            year=self.current_year,
            month=self.current_month
        )
        self.refresh()
        self.on_data_changed()

    def _handle_assign_and_track(self, tx_id: int, category_name: str, cat_name_to_id: Dict[str, int]):
        top = self.winfo_toplevel()
        if not category_name or category_name not in cat_name_to_id:
            messagebox.showwarning(
                "Select Category",
                "Please select an envelope category before tracking this transaction.",
                parent=top
            )
            return

        cat_id = cat_name_to_id[category_name]
        self.stream_service.track_transaction(tx_id, cat_id)
        self.refresh()
        self.on_data_changed()

    def _handle_soft_delete(self, tx_id: int):
        self.stream_service.soft_delete_transaction(tx_id)
        self.refresh()
        self.on_data_changed()

    def _handle_restore(self, tx_id: int):
        self.stream_service.restore_transaction(tx_id)
        self.refresh()
        self.on_data_changed()

    def _handle_hard_delete(self, tx_id: int):
        top = self.winfo_toplevel()
        if messagebox.askyesno(
            "Confirm Permanent Delete",
            "Are you sure you want to permanently delete this transaction?\n\nThis cannot be undone.",
            parent=top
        ):
            self.stream_service.hard_delete_transaction(tx_id)
            self.refresh()
            self.on_data_changed()
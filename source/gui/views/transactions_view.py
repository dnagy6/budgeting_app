"""
File: source/gui/widgets/transaction_panel.py
Purpose: Right-rail transaction stream container leveraging Theme tokens and the ScrollableCanvasMixin.
"""

import calendar
import tkinter as tk
import threading

from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional
from source.settings import Theme

# Widgets
from source.gui.widgets.transaction_card import TransactionCard
from source.gui.mixins import ScrollableCanvasMixin

# Services
from source.services.budget_service import BudgetService
from source.services.transaction_stream_service import TransactionStreamService
from source.services.plaid_service import PlaidService

#persistence
from source.persistence.database import SessionLocal
from source.persistence.models import PlaidItemModel

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

        self.plaid_service = PlaidService()
        self.is_syncing = False

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
            btn = tk.Label(
                self.tabs_bar,
                text=label,
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.HOVER_BG,
                cursor="hand2",
                padx=8,
                pady=4
            )
            btn.grid(row=0, column=col_idx, sticky="nsew", padx=1)
            btn.bind("<Button-1>", lambda e, t=tab_id: self.switch_tab(t))
            self.tab_buttons[tab_id] = btn

    def _create_scrollable_stream(self):
        # 1. Stream Column Header Labels (Balances the table structure)
        self.stream_headers = tk.Frame(self, bg=Theme.BG_CARD, padx=12, pady=6)
        self.stream_headers.pack(fill=tk.X)

        self.stream_headers.columnconfigure(0, minsize=40, weight=0)
        self.stream_headers.columnconfigure(1, weight=1)
        self.stream_headers.columnconfigure(2, minsize=210, weight=0)
        self.stream_headers.columnconfigure(3, minsize=110, weight=0)
        self.stream_headers.columnconfigure(4, minsize=70, weight=0)

        tk.Label(self.stream_headers, text="", bg=Theme.BG_CARD).grid(row=0, column=0)
        tk.Label(self.stream_headers, text="MERCHANT / DATE", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=1, sticky="w", padx=(6, 0))
        tk.Label(self.stream_headers, text="CATEGORY", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=2, sticky="w")
        tk.Label(self.stream_headers, text="AMOUNT", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=3, sticky="e", padx=(0, 16))

        # Divider under headers
        hdr_div = tk.Frame(self.stream_headers, bg=Theme.BORDER_HAIRLINE, height=1)
        hdr_div.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(4, 0))

        # 2. Scrollable Canvas
        self.container = tk.Frame(self, bg=Theme.BG_CARD)
        self.container.pack(fill=tk.BOTH, expand=True, padx=12, pady=0)

        self.canvas = tk.Canvas(self.container, bg=Theme.BG_CARD, highlightthickness=0, bd=0)
        
        # Borderless scrollbar matching card background
        self.scrollbar = tk.Scrollbar(
            self.container,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=Theme.BORDER_SUBTLE,
            troughcolor=Theme.BG_CARD,
            activebackground=Theme.TEXT_MUTED,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            width=8
        )
        self.stream_inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.stream_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._init_scrollable_mixin(self.container, self.canvas, self.stream_inner_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_footer_ui(self):
        footer = tk.Frame(
            self,
            bg=Theme.BG_CARD,
            padx=16,
            pady=10,
            highlightthickness=1,
            highlightbackground=Theme.HOVER_BG
        )
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.footer = footer

        # 1. Primary Action: Track Selected
        self.btn_track_selected = tk.Label(
            footer,
            text="Track Selected",
            font=Theme.FONT_LABEL,
            fg="#ffffff",
            bg=Theme.ACCENT_PRIMARY,
            cursor="hand2",
            padx=14,
            pady=7
        )
        self.btn_track_selected.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_track_selected.bind("<Button-1>", lambda e: self._handle_bulk_track())
        self.btn_track_selected.bind("<Enter>", lambda e: self.btn_track_selected.config(bg=Theme.BRAND_HIGHLIGHT))
        self.btn_track_selected.bind("<Leave>", lambda e: self.btn_track_selected.config(bg=Theme.ACCENT_PRIMARY))

        # 2. Secondary Action: Sync Bank Feed
        self.btn_sync = tk.Label(
            footer,
            text="↻ Sync Bank Feed",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.HOVER_BG,
            cursor="hand2",
            padx=14,
            pady=7
        )
        self.btn_sync.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))
        self.btn_sync.bind("<Button-1>", lambda e: self._handle_simulate_sync())
        self.btn_sync.bind("<Enter>", lambda e: self.btn_sync.config(bg=Theme.BORDER_SUBTLE))
        self.btn_sync.bind("<Leave>", lambda e: self.btn_sync.config(bg=Theme.HOVER_BG))

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
                    highlightthickness=1,
                    highlightbackground=Theme.BORDER_SUBTLE
            )
            else:
                btn.config(
                    text=btn_text,
                    bg=Theme.HOVER_BG,
                    fg=Theme.TEXT_MUTED,
                    font=Theme.FONT_LABEL,
                    highlightthickness=0
            )

        if self.current_tab == "new":
            self.btn_track_selected.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
            self.btn_sync.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))
        else:
            self.btn_track_selected.pack_forget()
            self.btn_sync.pack(fill=tk.X, expand=True)

        for child in self.stream_inner_frame.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0.0)

        self.card_instances = []

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
            card.pack(fill=tk.X, pady=0)

    def _handle_simulate_sync(self):
        """Pulls latest transactions from all linked Plaid institutions."""
        if self.is_syncing:
            return

        self.is_syncing = True
        self.btn_sync.config(text="↻ Syncing...", fg=Theme.TEXT_MUTED)

        def worker():
            total_added = 0
            try:
                with SessionLocal() as session:
                    items = session.query(PlaidItemModel).all()
                    item_ids = [item.item_id for item in items]

                if not item_ids:
                    self.after(0, lambda: messagebox.showinfo("No Accounts", "No linked bank accounts found. Connect an account in the Accounts tab first."))
                    return

                for item_id in item_ids:
                    res = self.plaid_service.sync_transactions(item_id)
                    total_added += res.get("added_count", 0)

                self.after(0, lambda: self._on_sync_finished(total_added))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Sync Error", f"Failed to sync with bank: {err}"))
            finally:
                self.after(0, self._reset_sync_button)

        threading.Thread(target=worker, daemon=True).start()

    def _on_sync_finished(self, added_count: int):
        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()
        messagebox.showinfo("Bank Sync Complete", f"Successfully synced with bank! Imported {added_count} new transactions.")

    def _reset_sync_button(self):
        self.is_syncing = False
        self.btn_sync.config(text="↻ Sync Bank Feed", fg=Theme.TEXT_MUTED)

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

    def _handle_bulk_track(self):
        """Processes all checked cards in bulk with explicit user feedback."""
        top = self.winfo_toplevel()

        # 1. Directly collect all TransactionCard instances currently rendered
        cards = [
            child for child in self.stream_inner_frame.winfo_children()
            if isinstance(child, TransactionCard)
        ]

        # 2. Filter to checked cards
        checked_cards = [card for card in cards if card.is_checked()]

        if not checked_cards:
            messagebox.showwarning(
                "No Transactions Selected",
                "Please check the box next to at least one transaction before clicking 'Track Selected'.",
                parent=top
            )
            return

        # 3. Separate cards into trackable vs. unassigned
        to_track = []
        unassigned_count = 0

        for card in checked_cards:
            selected_cat = card.cat_var.get().strip()
            cat_id = card.cat_name_to_id.get(selected_cat)

            if not selected_cat or selected_cat == "Select Category" or cat_id is None:
                unassigned_count += 1
            else:
                to_track.append((card.tx.id, cat_id))

        # 4. If all selected cards lack categories, warn the user
        if not to_track:
            messagebox.showwarning(
                "Select Category",
                "Please choose an envelope category for the selected transactions before tracking.",
                parent=top
            )
            return

        # 5. Track all valid selections
        for tx_id, cat_id in to_track:
            self.stream_service.track_transaction(tx_id, cat_id)

        # 6. Refresh panel and broadcast data changes to the budget view
        self.refresh()
        self.on_data_changed()

        # If any selected items were skipped due to missing categories, alert the user
        if unassigned_count > 0:
            messagebox.showinfo(
                "Partial Track",
                f"Tracked {len(to_track)} transaction(s).\n{unassigned_count} transaction(s) were skipped because no category was assigned.",
                parent=top
            )

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
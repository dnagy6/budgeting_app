"""
File: source/gui/views/accounts_view.py
Purpose: Displays connected bank institutions, live balances, and provides Link and Sync triggers.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from source.settings import Theme
from source.persistence.database import SessionLocal
from source.persistence.models import PlaidItemModel, PlaidAccountModel
from source.services.plaid_service import PlaidService
from source.services.plaid_launcher import launch_plaid_link
from source.gui.widgets.scrollable_canvas_mixin import ScrollableCanvasMixin


class AccountsView(tk.Frame, ScrollableCanvasMixin):
    def __init__(self, parent, on_accounts_updated=None, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)
        self.on_accounts_updated = on_accounts_updated
        self.plaid_service = PlaidService()
        self.is_connecting = False
        self.is_syncing = False

        self._create_header_ui()
        self._create_metrics_ui()
        self._create_scrollable_area()
        self.refresh()

    def _create_header_ui(self):
        header_frame = tk.Frame(self, bg=Theme.BG_CARD, padx=24, pady=16)
        header_frame.pack(fill=tk.X)

        # Title & Subtitle
        title_group = tk.Frame(header_frame, bg=Theme.BG_CARD)
        title_group.pack(side=tk.LEFT)

        tk.Label(
            title_group,
            text="Accounts",
            font=Theme.FONT_LARGE_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        tk.Label(
            title_group,
            text="Manage connected bank feeds and view balances",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        # Right Action Buttons Container
        actions_group = tk.Frame(header_frame, bg=Theme.BG_CARD)
        actions_group.pack(side=tk.RIGHT)

        # 1. ↻ Sync All Feeds Button
        self.btn_sync = tk.Label(
            actions_group,
            text="↻ Sync Feeds",
            font=Theme.FONT_HEADER,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=14,
            pady=8,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        self.btn_sync.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_sync.bind("<Button-1>", lambda e: self._start_plaid_sync())
        self.btn_sync.bind("<Enter>", lambda e: self.btn_sync.config(bg=Theme.HOVER_BG) if not self.is_syncing else None)
        self.btn_sync.bind("<Leave>", lambda e: self.btn_sync.config(bg=Theme.BG_CARD) if not self.is_syncing else None)

        # 2. + Link Bank Account Button
        self.btn_link = tk.Label(
            actions_group,
            text="+ Link Bank Account",
            font=Theme.FONT_HEADER,
            fg="#ffffff",
            bg=Theme.ACCENT_PRIMARY,
            cursor="hand2",
            padx=16,
            pady=8
        )
        self.btn_link.pack(side=tk.LEFT)
        self.btn_link.bind("<Button-1>", lambda e: self._start_plaid_link())
        self.btn_link.bind("<Enter>", lambda e: self.btn_link.config(bg=Theme.BRAND_HIGHLIGHT) if not self.is_connecting else None)
        self.btn_link.bind("<Leave>", lambda e: self.btn_link.config(bg=Theme.ACCENT_PRIMARY) if not self.is_connecting else None)

    def _create_metrics_ui(self):
        metrics_container = tk.Frame(self, bg=Theme.BG_CARD, padx=24, pady=0)
        metrics_container.pack(fill=tk.X)

        self.cards_frame = tk.Frame(metrics_container, bg=Theme.BG_CARD)
        self.cards_frame.pack(fill=tk.X)
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)
        self.cards_frame.columnconfigure(2, weight=1)

        self.lbl_cash = self._make_metric_card(self.cards_frame, 0, "TOTAL LIQUID CASH", "$0.00", Theme.SUCCESS)
        self.lbl_debt = self._make_metric_card(self.cards_frame, 1, "TOTAL CREDIT DEBT", "$0.00", Theme.DANGER)
        self.lbl_net = self._make_metric_card(self.cards_frame, 2, "NET CASH BALANCE", "$0.00", Theme.TEXT_PRIMARY)

    def _make_metric_card(self, parent, col: int, title: str, initial_val: str, val_color: str):
        card = tk.Frame(
            parent,
            bg=Theme.BG_CARD,
            padx=16,
            pady=14,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        card.grid(row=0, column=col, sticky="ew", padx=6 if col == 1 else (0 if col == 0 else (6, 0)))

        tk.Label(card, text=title, font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).pack(anchor="w")
        lbl_val = tk.Label(card, text=initial_val, font=Theme.FONT_LARGE_TITLE, fg=val_color, bg=Theme.BG_CARD)
        lbl_val.pack(anchor="w", pady=(4, 0))
        return lbl_val

    def _create_scrollable_area(self):
        self.container = tk.Frame(self, bg=Theme.BG_CARD)
        self.container.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 24))

        self.canvas = tk.Canvas(self.container, bg=Theme.BG_CARD, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(
            self.container,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=Theme.BORDER_SUBTLE,
            troughcolor=Theme.BG_CARD,
            bd=0,
            highlightthickness=0,
            width=8
        )
        self.inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._init_scrollable_mixin(self.container, self.canvas, self.inner_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self):
        """Reloads all institutions and accounts from SQLite and resets scroll position."""
        for child in self.inner_frame.winfo_children():
            child.destroy()

        with SessionLocal() as session:
            items = session.query(PlaidItemModel).all()
            accounts = session.query(PlaidAccountModel).all()

            grouped_accounts = {}
            for acc in accounts:
                grouped_accounts.setdefault(acc.item_id, []).append(acc)

            liquid_cash = 0.0
            credit_debt = 0.0

            for acc in accounts:
                bal = float(acc.current_balance or 0.0)
                acc_type = (acc.type or "").lower()
                acc_subtype = (acc.subtype or "").lower()

                if acc_type == "depository":
                    liquid_cash += bal
                elif acc_type in ("credit", "loan") or acc_subtype == "credit card":
                    credit_debt += bal

            net_balance = liquid_cash - credit_debt

            self.lbl_cash.config(text=f"${liquid_cash:,.2f}")
            self.lbl_debt.config(text=f"${credit_debt:,.2f}")
            net_color = Theme.SUCCESS if net_balance >= 0 else Theme.DANGER
            self.lbl_net.config(text=f"${net_balance:,.2f}", fg=net_color)

            if not items:
                self._render_empty_state()
            else:
                for item in items:
                    item_accs = grouped_accounts.get(item.item_id, [])
                    self._render_institution_card(item, item_accs)

        # Reset canvas viewport to top
        self.canvas.yview_moveto(0.0)

    def _render_empty_state(self):
        empty_card = tk.Frame(
            self.inner_frame,
            bg=Theme.BG_CARD,
            padx=32,
            pady=48,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        empty_card.pack(fill=tk.X, pady=20)

        tk.Label(
            empty_card,
            text="No Connected Bank Accounts",
            font=Theme.FONT_HEADER,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack()

        tk.Label(
            empty_card,
            text="Click '+ Link Bank Account' above to connect your accounts through Plaid Sandbox.",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            pady=8
        ).pack()

    def _render_institution_card(self, item: PlaidItemModel, accounts: list):
        card = tk.Frame(
            self.inner_frame,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        card.pack(fill=tk.X, pady=(0, 16))

        # Institution Header Bar
        inst_header = tk.Frame(card, bg=Theme.BG_CARD, padx=16, pady=12)
        inst_header.pack(fill=tk.X)

        tk.Label(
            inst_header,
            text=item.institution_name or "Connected Bank",
            font=Theme.FONT_HEADER,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(side=tk.LEFT)

        # Right actions on institution card
        right_actions = tk.Frame(inst_header, bg=Theme.BG_CARD)
        right_actions.pack(side=tk.RIGHT)

        btn_item_sync = tk.Label(
            right_actions,
            text="↻ Sync",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=6
        )
        btn_item_sync.pack(side=tk.LEFT, padx=(0, 12))
        btn_item_sync.bind("<Button-1>", lambda e, i_id=item.item_id: self._start_single_sync(i_id))
        btn_item_sync.bind("<Enter>", lambda e, b=btn_item_sync: b.config(fg=Theme.TEXT_PRIMARY))
        btn_item_sync.bind("<Leave>", lambda e, b=btn_item_sync: b.config(fg=Theme.TEXT_MUTED))

        status_pill = tk.Label(
            right_actions,
            text="● Active",
            font=Theme.FONT_LABEL,
            fg=Theme.SUCCESS,
            bg=Theme.BG_CARD,
            padx=4
        )
        status_pill.pack(side=tk.LEFT)

        tk.Frame(card, bg=Theme.BORDER_HAIRLINE, height=1).pack(fill=tk.X)

        # Account Rows
        for acc in accounts:
            row = tk.Frame(card, bg=Theme.BG_CARD, padx=16, pady=10)
            row.pack(fill=tk.X)

            left_col = tk.Frame(row, bg=Theme.BG_CARD)
            left_col.pack(side=tk.LEFT)

            tk.Label(
                left_col,
                text=acc.name,
                font=Theme.FONT_BODY,
                fg=Theme.TEXT_PRIMARY,
                bg=Theme.BG_CARD
            ).pack(anchor="w")

            mask_str = f"•••• {acc.mask}" if acc.mask else "Account"
            tk.Label(
                left_col,
                text=mask_str,
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            ).pack(anchor="w")

            type_label = (acc.subtype or acc.type or "other").upper()
            badge = tk.Label(
                row,
                text=type_label,
                font=("Arial", 8, "bold"),
                fg=Theme.TEXT_MUTED,
                bg=Theme.HOVER_BG,
                padx=8,
                pady=3
            )
            badge.pack(side=tk.LEFT, padx=(24, 0))

            bal = float(acc.current_balance or 0.0)
            acc_type = (acc.type or "").lower()
            is_liability = acc_type in ("credit", "loan")

            bal_text = f"-${bal:,.2f}" if (is_liability and bal > 0) else f"${bal:,.2f}"
            bal_color = Theme.TEXT_PRIMARY if not is_liability else Theme.DANGER

            tk.Label(
                row,
                text=bal_text,
                font=Theme.FONT_HEADER,
                fg=bal_color,
                bg=Theme.BG_CARD
            ).pack(side=tk.RIGHT)

            tk.Frame(card, bg=Theme.BORDER_HAIRLINE, height=1).pack(fill=tk.X)

    def _start_plaid_sync(self):
        """Syncs all connected institutions in a background thread."""
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

                for item_id in item_ids:
                    res = self.plaid_service.sync_transactions(item_id)
                    total_added += len(res.get("added", []))

                self.after(0, lambda: self._on_sync_success(total_added))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Sync Error", f"Failed to sync with Plaid: {err}"))
            finally:
                self.after(0, self._reset_sync_button)

        threading.Thread(target=worker, daemon=True).start()

    def _start_single_sync(self, item_id: str):
        """Syncs a specific institution."""
        if self.is_syncing:
            return

        self.is_syncing = True
        self.btn_sync.config(text="↻ Syncing...", fg=Theme.TEXT_MUTED)

        def worker():
            try:
                res = self.plaid_service.sync_transactions(item_id)
                added = len(res.get("added", []))
                self.after(0, lambda: self._on_sync_success(added))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Sync Error", f"Failed to sync institution: {err}"))
            finally:
                self.after(0, self._reset_sync_button)

        threading.Thread(target=worker, daemon=True).start()

    def _on_sync_success(self, count: int):
        self.refresh()
        if self.on_accounts_updated:
            self.on_accounts_updated()
        messagebox.showinfo("Sync Complete", f"Successfully synced with bank! Fetched {count} transactions.")

    def _reset_sync_button(self):
        self.is_syncing = False
        self.btn_sync.config(text="↻ Sync Feeds", fg=Theme.TEXT_PRIMARY)

    def _start_plaid_link(self):
        if self.is_connecting:
            return

        self.is_connecting = True
        self.btn_link.config(text="Connecting...", bg=Theme.TEXT_MUTED)

        def run_thread():
            try:
                launch_plaid_link(self.plaid_service, on_success=self._on_link_success)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Link Error", f"Failed to initialize Plaid Link: {e}"))
            finally:
                self.after(0, self._reset_link_button)

        threading.Thread(target=run_thread, daemon=True).start()

    def _on_link_success(self, item_id: str, acc_count: int):
        self.after(0, lambda: self._handle_link_complete(acc_count))

    def _handle_link_complete(self, acc_count: int):
        self.refresh()
        if self.on_accounts_updated:
            self.on_accounts_updated()
        messagebox.showinfo("Bank Linked", f"Successfully linked institution with {acc_count} accounts!")

    def _reset_link_button(self):
        self.is_connecting = False
        self.btn_link.config(text="+ Link Bank Account", bg=Theme.ACCENT_PRIMARY)
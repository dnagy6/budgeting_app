"""
File: source/gui/widgets/transaction_card.py
Purpose: A high-density, single-line row for processing transactions.
"""
from typing import Callable, Dict, Optional
import tkinter as tk
from tkinter import ttk
from source.settings import Theme


class TransactionCard(tk.Frame):
    def __init__(
        self,
        parent,
        tx,
        current_tab: str,
        cat_id_to_name: Dict[int, str],
        cat_name_to_id: Dict[str, int],
        on_track: Optional[Callable[[int, str], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        on_restore: Optional[Callable[[int], None]] = None,
        on_hard_delete: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            bd=0,
            highlightthickness=0,
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

        self.is_selected = tk.IntVar(value=0)
        self.action_buttons = []

        # Sort categories alphabetically, pinning Ready to Assign to top
        self.cat_names = sorted(list(self.cat_name_to_id.keys()))
        if "Ready to Assign" in self.cat_names:
            self.cat_names.insert(0, self.cat_names.pop(self.cat_names.index("Ready to Assign")))

        self._create_ui()
        self._bind_hover_events()

    def is_checked(self) -> bool:
        return self.is_selected.get() == 1

    def toggle_check(self):
        new_val = 0 if self.is_selected.get() == 1 else 1
        self.is_selected.set(new_val)
        self._update_checkbox_ui()

    def _update_checkbox_ui(self):
        if not hasattr(self, "lbl_chk") or not self.lbl_chk.winfo_exists():
            return

        if self.is_selected.get() == 1:
            self.lbl_chk.config(
                text="✓",
                bg=Theme.ACCENT_PRIMARY,
                fg="#ffffff",
                highlightbackground=Theme.ACCENT_PRIMARY
            )
        else:
            self.lbl_chk.config(
                text="",
                bg="#ffffff",
                fg="#ffffff",
                highlightbackground="#cbd5e1"  # Crisp, visible border
            )

    def _create_ui(self):
        # Grid Configuration: Column 1 absorbs width so Category & Amount stay grouped
        self.columnconfigure(0, minsize=40, weight=0)   # Checkbox
        self.columnconfigure(1, weight=1)               # Merchant & Date (Flexible)
        self.columnconfigure(2, minsize=210, weight=0)  # Category Dropdown Box
        self.columnconfigure(3, minsize=110, weight=0)  # Amount (Anchored near Category)
        self.columnconfigure(4, minsize=70, weight=0)   # Action Buttons

        # Column 0: Crisp, Visible Checkbox
        if self.current_tab == "new":
            self.lbl_chk = tk.Label(
                self,
                text="",
                font=("Arial", 10, "bold"),
                fg="#ffffff",
                bg="#ffffff",
                highlightthickness=1,
                highlightbackground="#cbd5e1",
                width=2,
                height=1,
                cursor="hand2"
            )
            self.lbl_chk.grid(row=0, column=0, padx=(14, 6), pady=9, sticky="w")
            self.lbl_chk.bind("<Button-1>", lambda e: self.toggle_check())

        # Column 1: Merchant & Date
        self.merchant_frame = tk.Frame(self, bg=Theme.BG_CARD)
        self.merchant_frame.grid(row=0, column=1, sticky="w", padx=(6, 12), pady=8)

        self.lbl_note = tk.Label(
            self.merchant_frame,
            text=self.tx.note or "Unnamed Transaction",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        self.lbl_note.pack(anchor="w")

        self.lbl_date = tk.Label(
            self.merchant_frame,
            text=self.tx.trans_date,
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        self.lbl_date.pack(anchor="w")

        # Column 2: Category Selector Pill
        self.cat_var = tk.StringVar()
        if self.tx.category_id and self.tx.category_id in self.cat_id_to_name:
            self.cat_var.set(self.cat_id_to_name[self.tx.category_id])
        else:
            self.cat_var.set("Select Category")

        is_interactive = (self.current_tab == "new")
        self.lbl_category = tk.Label(
            self,
            font=Theme.FONT_BODY,
            bg=Theme.INPUT_BG if is_interactive else Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.INPUT_BORDER if is_interactive else Theme.BORDER_SUBTLE,
            cursor="hand2" if is_interactive else "arrow",
            padx=10,
            pady=4,
            anchor="w",
            width=18
        )
        self.lbl_category.grid(row=0, column=2, sticky="w", padx=(0, 12), pady=8)
        self._update_category_label()

        if is_interactive:
            self.lbl_category.bind("<Button-1>", self._open_category_menu)
            self.lbl_category.bind("<Enter>", lambda e: self.lbl_category.config(highlightbackground=Theme.ACCENT_PRIMARY))
            self.lbl_category.bind("<Leave>", lambda e: self.lbl_category.config(highlightbackground=Theme.INPUT_BORDER))

        # Column 3: Amount with Positive Cashflow Detection
        tx_amount = float(self.tx.amount)
        display_amount = abs(tx_amount)

        # Cashflow Detection: negative amount, income note keywords, or assigned to income category
        note_lower = (self.tx.note or "").lower()
        is_income_note = any(k in note_lower for k in ["payroll", "deposit", "salary", "refund", "credit", "interest"])
        is_income_cat = "income" in self.cat_var.get().lower() or "partner" in self.cat_var.get().lower()
        is_positive_cashflow = (tx_amount < 0) or is_income_note or is_income_cat

        amount_text = f"+${display_amount:,.2f}" if is_positive_cashflow else f"-${display_amount:,.2f}"
        amount_color = Theme.SUCCESS if is_positive_cashflow else Theme.TEXT_PRIMARY

        self.lbl_amount = tk.Label(
            self,
            text=amount_text,
            font=Theme.FONT_HEADER,
            fg=amount_color,
            bg=Theme.BG_CARD
        )
        self.lbl_amount.grid(row=0, column=3, sticky="e", padx=(0, 16), pady=8)

        # Column 4: Action Buttons
        self.action_frame = tk.Frame(self, bg=Theme.BG_CARD)
        self.action_frame.grid(row=0, column=4, sticky="e", padx=(0, 14), pady=8)
        self._build_action_buttons(self.action_frame)

        # Row 1: Hairline Separator
        self.divider = tk.Frame(self, bg=Theme.BORDER_HAIRLINE, height=1)
        self.divider.grid(row=1, column=0, columnspan=5, sticky="ew")

    def _update_category_label(self):
        val = self.cat_var.get()
        is_placeholder = (val == "Select Category")
        arrow = "  ▾" if self.current_tab == "new" else ""
        self.lbl_category.config(
            text=f"{val}{arrow}",
            fg=Theme.TEXT_MUTED if is_placeholder else Theme.TEXT_PRIMARY
        )

    def _open_category_menu(self, event=None):
        if self.current_tab != "new" or not self.cat_names:
            return

        menu = tk.Menu(self, tearoff=0)
        for cat in self.cat_names:
            menu.add_command(
                label=cat,
                command=lambda c=cat: self._select_category(c)
            )

        x = self.lbl_category.winfo_rootx()
        y = self.lbl_category.winfo_rooty() + self.lbl_category.winfo_height()
        menu.tk_popup(x, y)

    def _select_category(self, cat_name: str):
        self.cat_var.set(cat_name)
        self._update_category_label()

        # Dynamically re-evaluate cash flow styling if categorized as Income
        tx_amount = abs(float(self.tx.amount))
        if "partner" in cat_name.lower() or "income" in cat_name.lower():
            self.lbl_amount.config(text=f"+${tx_amount:,.2f}", fg=Theme.SUCCESS)
        elif not any(k in (self.tx.note or "").lower() for k in ["payroll", "deposit", "salary"]):
            self.lbl_amount.config(text=f"-${tx_amount:,.2f}", fg=Theme.TEXT_PRIMARY)

    def _build_action_buttons(self, parent_frame):
        self.action_buttons.clear()

        if self.current_tab in ("new", "tracked"):
            if self.on_delete:
                btn_del = self._make_btn(
                    parent_frame,
                    text="Delete",
                    color=Theme.BG_CARD,
                    hover_color=Theme.DANGER,
                    command=lambda: self.on_delete(self.tx.id)
                )
                btn_del.pack(side=tk.RIGHT)
                self.action_buttons.append(btn_del)

        elif self.current_tab == "deleted":
            if self.on_restore:
                btn_res = self._make_btn(
                    parent_frame,
                    text="Restore",
                    color=Theme.TEXT_PRIMARY,
                    hover_color=Theme.ACCENT_PRIMARY,
                    command=lambda: self.on_restore(self.tx.id)
                )
                btn_res.pack(side=tk.LEFT, padx=(0, 4))

            if self.on_hard_delete:
                btn_hard_del = self._make_btn(
                    parent_frame,
                    text="✕",
                    color=Theme.DANGER,
                    hover_color=Theme.DANGER,
                    command=lambda: self.on_hard_delete(self.tx.id)
                )
                btn_hard_del.pack(side=tk.LEFT)

    def _make_btn(self, parent, text: str, color: str, hover_color: str, command: Callable):
        lbl_btn = tk.Label(
            parent,
            text=text,
            font=Theme.FONT_LABEL,
            fg=color,
            bg=Theme.BG_CARD,
            cursor="hand2",
            padx=4,
            pady=2
        )
        lbl_btn.bind("<Button-1>", lambda e: command())
        lbl_btn.bind("<Enter>", lambda e: lbl_btn.config(fg=hover_color))
        lbl_btn.bind("<Leave>", lambda e: lbl_btn.config(
            fg=Theme.TEXT_MUTED if self.cget("bg") == Theme.HOVER_BG else color
        ))
        return lbl_btn

    def _bind_hover_events(self):
        bg_targets = [
            self,
            self.merchant_frame,
            self.lbl_note,
            self.lbl_date,
            self.lbl_amount,
            self.action_frame,
        ]

        def on_enter(e):
            for w in bg_targets:
                try:
                    w.config(bg=Theme.HOVER_BG)
                except Exception:
                    pass
            for btn in self.action_buttons:
                try:
                    btn.config(fg=Theme.TEXT_MUTED, bg=Theme.HOVER_BG)
                except Exception:
                    pass

        def on_leave(e):
            for w in bg_targets:
                try:
                    w.config(bg=Theme.BG_CARD)
                except Exception:
                    pass
            for btn in self.action_buttons:
                try:
                    btn.config(fg=Theme.BG_CARD, bg=Theme.BG_CARD)
                except Exception:
                    pass

        excluded = [
            getattr(self, "lbl_chk", None),
            getattr(self, "lbl_category", None),
            getattr(self, "divider", None)
        ]
        bind_targets = [
            w for w in self.winfo_children()
            if w not in excluded
        ] + [self, self.lbl_note, self.lbl_date, self.merchant_frame]

        for w in bind_targets:
            w.bind("<Enter>", on_enter, add="+")
            w.bind("<Leave>", on_leave, add="+")
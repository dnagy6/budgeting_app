"""
File: source/gui/widgets/transactions_minimap.py
Purpose: Read-only right rail for the Transactions tab to monitor envelope balances.
"""

import tkinter as tk
from source.settings import Theme
from source.gui.widgets.scrollable_canvas_mixin import ScrollableCanvasMixin

class TransactionsMinimap(tk.Frame, ScrollableCanvasMixin):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            width=280,
            **kwargs
        )
        self.pack_propagate(False)
        self.all_categories = []
        self._create_ui()

    def _create_ui(self):
        # Header & Search Bar
        header_frame = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=16)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(
            header_frame, 
            text="Left to Budget", 
            font=Theme.FONT_HEADER, 
            bg=Theme.BG_CARD, 
            fg=Theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self.lbl_left_to_budget = tk.Label(
            header_frame,
            text="$0.00 Unassigned",
            font=Theme.FONT_TITLE,
            fg=Theme.SUCCESS,
            bg=Theme.BG_CARD
        )
        self.lbl_left_to_budget.pack(anchor="w", pady=(0, 12))
        
        self.placeholder = "Search Budget..."
        self.search_var = tk.StringVar(value=self.placeholder)
        self.search_var.trace_add("write", self._on_search)

        search_entry = tk.Entry(
            header_frame,
            textvariable=self.search_var,
            font=Theme.FONT_BODY,
            bg=Theme.HOVER_BG,
            fg=Theme.TEXT_MUTED,
            relief=tk.FLAT,
            insertbackground=Theme.TEXT_PRIMARY
        )
        search_entry.pack(fill=tk.X, ipady=4)

        def on_focus_in(event):
            if self.search_var.get() == self.placeholder:
                self.search_var.set("")
                search_entry.config(fg=Theme.TEXT_PRIMARY)

        def on_focus_out(event):
            if not self.search_var.get():
                self.search_var.set(self.placeholder)
                search_entry.config(fg=Theme.TEXT_MUTED)

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)

        # Scrollable List Container
        self.list_container = tk.Frame(self, bg=Theme.BG_CARD)
        self.list_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.list_container, bg=Theme.BG_CARD, highlightthickness=0)
        self.inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD, padx=16, pady=8)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._init_scrollable_mixin(self.list_container, self.canvas, self.inner_frame)

    def refresh_data(self, budget_groups, unallocated: float):
        color = Theme.SUCCESS if unallocated >= 0 else Theme.DANGER
        self.lbl_left_to_budget.config(
            text=f"${unallocated:,.2f} Leftover",
            fg=color
        )
        self.all_categories = []
        for grp in budget_groups:
            for cat in grp.categories:
                actual = cat.get_actual_amount()
                remaining = actual if grp.group_type == "income" else (cat.planned_amount - actual)
                
                self.all_categories.append({
                    "name": cat.name,
                    "group": grp.name,
                    "remaining": remaining,
                    "type": grp.group_type
                })
        self._render_list()

    def _on_search(self, *args):
        query = self.search_var.get()
        if query == self.placeholder:
            self._render_list("")
        else:
            self._render_list(query.lower())

    def _render_list(self, filter_text=""):
        for child in self.inner_frame.winfo_children():
            child.destroy()
        
        self.canvas.yview_moveto(0.0)

        # Filter and Group Data
        grouped = {}
        for cat in self.all_categories:
            if filter_text in cat["name"].lower() or filter_text in cat["group"].lower():
                if cat["group"] not in grouped:
                    grouped[cat["group"]] = []
                grouped[cat["group"]].append(cat)

        if not grouped:
            tk.Label(
                self.inner_frame,
                text="No envelopes found.",
                font=Theme.FONT_ITALIC_MUTED,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                pady=20
            ).pack()
            return

        # Render Rows
        for group_name, cats in grouped.items():
            tk.Label(
                self.inner_frame,
                text=group_name.upper(),
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            ).pack(anchor="w", pady=(12, 4))

            for cat in cats:
                row = tk.Frame(self.inner_frame, bg=Theme.BG_CARD)
                row.pack(fill=tk.X, pady=2)
                
                tk.Label(
                    row,
                    text=cat["name"],
                    font=Theme.FONT_BODY,
                    fg=Theme.TEXT_PRIMARY,
                    bg=Theme.BG_CARD
                ).pack(side=tk.LEFT)

                rem = cat["remaining"]
                color = Theme.SUCCESS if rem > 0 else Theme.DANGER if rem < 0 else Theme.TEXT_MUTED

                tk.Label(
                    row,
                    text=f"${rem:,.2f}",
                    font=Theme.FONT_HEADER,
                    fg=color,
                    bg=Theme.BG_CARD
                ).pack(side=tk.RIGHT)
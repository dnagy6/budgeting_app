"""
File: source/gui/widgets/expense_card.py
Purpose: Container component managing the fixed income section, scrollable expense canvas, and group card rendering.
"""

import tkinter as tk
from tkinter import ttk
from source.settings import Theme
from source.gui.widgets.category_group_card import CategoryGroupCard

class ExpenseCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)
        self._create_ui()

    def _create_ui(self):
        # 1. Dedicated Fixed Income Container (Always at the top, never scrolls away)
        self.income_container = tk.Frame(self, bg=Theme.BG_CARD)
        self.income_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        # 2. Scrollable Container for Expense Groups Only
        expense_container = tk.Frame(self, bg=Theme.BG_CARD)
        expense_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(expense_container, bg=Theme.BG_CARD, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(expense_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.groups_inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self.groups_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Cross-platform mouse wheel scroll bindings
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_mouse_wheel(self, event):
        """Cross-platform mouse wheel scrolling handler."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            amount = int(-1 * (event.delta / 120)) if abs(event.delta) >= 120 else -1 * event.delta
            self.canvas.yview_scroll(amount, "units")

    def _bind_mouse_wheel_recursive(self, widget):
        """Recursively binds scroll events to child widgets so hovering anywhere works."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel, add="+")
        widget.bind("<Button-4>", self._on_mouse_wheel, add="+")
        widget.bind("<Button-5>", self._on_mouse_wheel, add="+")
        for child in widget.winfo_children():
            self._bind_mouse_wheel_recursive(child)

    def render_groups(self, groups: list, callbacks: dict):
        """Captures expansion states, clears old cards, separates income/expenses, and renders cards."""
        # 1. Capture current expansion states across all rendered cards
        card_states = {}
        for container in (self.income_container, self.groups_inner_frame):
            for card in container.winfo_children():
                if isinstance(card, CategoryGroupCard):
                    card_states[card.group.name] = card.is_expanded

        # 2. Clear existing cards from both containers
        for child in self.income_container.winfo_children():
            child.destroy()
        for child in self.groups_inner_frame.winfo_children():
            child.destroy()

        # 3. Separate Income groups from Expense groups
        income_groups = [g for g in groups if g.group_type == "income" or g.name.lower() == "income"]
        expense_groups = [g for g in groups if g.group_type != "income" and g.name.lower() != "income"]

        # 4. Render Income Card(s)
        for grp in income_groups:
            was_expanded = card_states.get(grp.name, True)
            card = CategoryGroupCard(
                self.income_container,
                group=grp,
                initial_expanded=was_expanded,
                **callbacks
            )
            card.pack(fill=tk.X, expand=True)

        # 5. Render Expense Cards or Empty State
        if not expense_groups:
            lbl_empty = tk.Label(
                self.groups_inner_frame,
                text="No expense category groups created yet.\nClick '+ Add Category Group' below to start organizing your budget.",
                font=Theme.FONT_BODY,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                pady=20
            )
            lbl_empty.pack(fill=tk.BOTH, expand=True)
        else:
            for grp in expense_groups:
                was_expanded = card_states.get(grp.name, True)
                card = CategoryGroupCard(
                    self.groups_inner_frame,
                    group=grp,
                    initial_expanded=was_expanded,
                    **callbacks
                )
                card.pack(fill=tk.X, padx=4, pady=6)

        # 6. Apply recursive mouse wheel binding to newly rendered elements
        self._bind_mouse_wheel_recursive(self.groups_inner_frame)
        self._bind_mouse_wheel_recursive(self.income_container)
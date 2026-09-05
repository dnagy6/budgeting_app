"""
File: source/gui/widgets/expense_card.py
Purpose: Container component managing fixed income, scrollable expense canvas, and smooth cross-platform scrolling via mixin.
"""

import tkinter as tk
from tkinter import ttk
from source.settings import Theme
from source.gui.widgets.category_group_card import CategoryGroupCard
from source.gui.widgets.scrollable_canvas_mixin import ScrollableCanvasMixin

class ExpenseCard(tk.Frame, ScrollableCanvasMixin):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)
        self._create_ui()

    def _create_ui(self):
        # Single Scrollable Container for ALL Groups (Income + Expenses)
        main_container = tk.Frame(self, bg=Theme.BG_CARD)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(main_container, bg=Theme.BG_CARD, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.groups_inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Initialize scrollable canvas mixin behaviors
        self._init_scrollable_mixin(main_container, self.canvas, self.groups_inner_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def render_groups(self, groups: list, callbacks: dict):
        """Captures expansion states, clears old cards, and renders all cards into the scroll space."""
        card_states = {}
        
        
        for card in self.groups_inner_frame.winfo_children():
            if isinstance(card, CategoryGroupCard):
                card_states[card.group.name] = card.is_expanded

        
        for child in self.groups_inner_frame.winfo_children():
            child.destroy()

        
        income_groups = [g for g in groups if g.group_type == "income" or g.name.lower() == "income"]
        expense_groups = [g for g in groups if g.group_type != "income" and g.name.lower() != "income"]

        
        for grp in income_groups:
            was_expanded = card_states.get(grp.name, True)
            card = CategoryGroupCard(
                self.groups_inner_frame,
                group=grp,
                initial_expanded=was_expanded,
                **callbacks
            )
            card.pack(fill=tk.X, padx=4, pady=6)

        
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
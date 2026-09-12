"""
File: source/gui/widgets/expense_card.py
Purpose: Container managing scrollable category groups and inline group creation.
"""

import tkinter as tk
from source.settings import Theme
from source.gui.widgets.category_group_card import CategoryGroupCard
from source.gui.mixins import ScrollableCanvasMixin


class ExpenseCard(tk.Frame, ScrollableCanvasMixin):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, **kwargs)
        self._create_ui()

    def _create_ui(self):
        main_container = tk.Frame(self, bg=Theme.BG_CARD)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(main_container, bg=Theme.BG_CARD, highlightthickness=0, bd=0)

        self.scrollbar = tk.Scrollbar(
            main_container,
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

        self.groups_inner_frame = tk.Frame(self.canvas, bg=Theme.BG_CARD)

        self._scroll_canvas_window = self.canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._init_scrollable_mixin(main_container, self.canvas, self.groups_inner_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def render_groups(self, groups: list, callbacks: dict):
        """Captures expansion states, clears old cards, and renders all cards into the scroll space."""
        card_states = {}

        # 1. Capture expansion state from existing inner cards
        for card in self.groups_inner_frame.winfo_children():
            if isinstance(card, CategoryGroupCard):
                card_states[card.group.name] = card.is_expanded

        # 2. Clear previous render
        for child in self.groups_inner_frame.winfo_children():
            child.destroy()

        # Isolate callbacks meant only for CategoryGroupCard to prevent TclError
        card_callbacks = {k: v for k, v in callbacks.items() if k != "on_add_group"}
        on_add_grp = callbacks.get("on_add_group")

        # 3. Separate groups so Income stays pinned to the top
        income_groups = [g for g in groups if g.group_type == "income" or g.name.lower() == "income"]
        expense_groups = [g for g in groups if g.group_type != "income" and g.name.lower() != "income"]

        # 4. Render Income Groups
        for grp in income_groups:
            was_expanded = card_states.get(grp.name, True)
            card = CategoryGroupCard(
                self.groups_inner_frame,
                group=grp,
                initial_expanded=was_expanded,
                **card_callbacks
            )
            card.pack(fill=tk.X, padx=0, pady=0)

        # 5. Render Expense Groups
        if not expense_groups:
            lbl_empty = tk.Label(
                self.groups_inner_frame,
                text="No expense category groups created yet.",
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
                    **card_callbacks
                )
                card.pack(fill=tk.X, padx=0, pady=0)

        # 6. Bottom "+ Add Category Group" Action Link
        if on_add_grp:
            btn_add_group = tk.Label(
                self.groups_inner_frame,
                text="+ Add Category Group",
                font=Theme.FONT_LABEL,
                fg=Theme.ACCENT_PRIMARY,
                bg=Theme.BG_CARD,
                highlightthickness=1,
                highlightbackground=Theme.INPUT_BORDER,
                cursor="hand2",
                pady=10
            )
            btn_add_group.pack(fill=tk.X, padx=4, pady=(16, 24))
            btn_add_group.bind("<Button-1>", lambda e: on_add_grp())
            btn_add_group.bind("<Enter>", lambda e: btn_add_group.config(
                bg=Theme.HOVER_BG, fg=Theme.BRAND_HIGHLIGHT
            ))
            btn_add_group.bind("<Leave>", lambda e: btn_add_group.config(
                bg=Theme.BG_CARD, fg=Theme.ACCENT_PRIMARY
            ))
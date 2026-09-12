"""
File: source/gui/widgets/category_group_card.py
Purpose: Main container for category groups combining layout, mixins, and grid rendering using central Theme tokens.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from source.settings import Theme
from source.domain.category import Category
from source.domain.category_group import CategoryGroup
from source.gui.mixins import CardDragMixin, CardInlineEditMixin

class CategoryGroupCard(tk.Frame, CardDragMixin, CardInlineEditMixin):
    def __init__(
        self,
        parent,
        group: CategoryGroup,
        on_add_category=None,
        on_inline_save_category=None,
        on_inline_edit=None,
        on_delete_category=None,
        on_delete_group=None,
        on_reorder_complete=None,
        on_rename_group=None,
        initial_expanded: bool = True,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            bd=0,
            **kwargs
        )
        self.group = group
        self.container_parent = parent
        self.on_add_category = on_add_category
        self.on_inline_save_category = on_inline_save_category
        self.on_inline_edit = on_inline_edit
        self.on_delete_category = on_delete_category
        self.on_delete_group = on_delete_group
        self.on_reorder_complete = on_reorder_complete
        self.on_rename_group = on_rename_group
        self.is_expanded = initial_expanded

        self._create_ui()

    def _create_ui(self):
        # 1. Group Header Bar
        header_bg = Theme.BG_HEADER
        self.header_frame = tk.Frame(self, bg=header_bg, padx=16, pady=6)
        self.header_frame.pack(fill=tk.X)

        controls_left = tk.Frame(self.header_frame, bg=header_bg)
        controls_left.pack(side=tk.LEFT)

        if self.group.group_type != "income":
            self.lbl_grip = tk.Label(
                controls_left,
                text="⠇⠇",
                font=Theme.FONT_TITLE,
                bg=header_bg,
                fg=Theme.TEXT_MUTED,
                cursor="fleur"
            )
            self.lbl_grip.pack(side=tk.LEFT, padx=(0, 8))
            self._bind_drag_events(self.lbl_grip)

        self.lbl_arrow = tk.Label(
            controls_left,
            text="v",
            font=Theme.FONT_HEADER,
            bg=header_bg,
            fg=Theme.TEXT_MUTED,
            cursor="hand2"
        )
        self.lbl_arrow.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_arrow.bind("<Button-1>", lambda e: self.toggle_expand())

        self.lbl_title = tk.Label(
            controls_left,
            text=self.group.name,
            font=Theme.FONT_HEADER,
            bg=header_bg,
            fg=Theme.TEXT_PRIMARY,
            cursor="xterm"
        )
        self.lbl_title.pack(side=tk.LEFT)
        self.lbl_title.bind("<Button-1>", lambda e: self._start_inline_group_name_edit())

        # Summary Math
        total_planned = self.group.get_total_planned()
        total_actual = self.group.get_total_actual()
        actual_label = "Received" if self.group.group_type == "income" else "Spent"
        summary_text = f"Planned: ${total_planned:,.2f}  |  {actual_label}: ${total_actual:,.2f}"

        # Right-Hand Header Elements
        self.header_right_container = tk.Frame(self.header_frame, bg=header_bg)
        self.header_right_container.pack(side=tk.RIGHT)

        self.lbl_summary = tk.Label(
            self.header_right_container,
            text=summary_text,
            font=Theme.FONT_LABEL,
            bg=header_bg,
            fg=Theme.TEXT_MUTED
        )

        self.header_labels_frame = tk.Frame(self.header_right_container, bg=header_bg)
        self.header_labels_frame.columnconfigure(0, minsize=120)
        self.header_labels_frame.columnconfigure(1, minsize=120)
        self.header_labels_frame.columnconfigure(2, minsize=120)
        self.header_labels_frame.columnconfigure(3, minsize=40)

        is_income = self.group.group_type == "income"
        tk.Label(self.header_labels_frame, text="PLANNED" if is_income else "BUDGET", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=header_bg).grid(row=0, column=0, sticky="e", padx=(0, 10))
        tk.Label(self.header_labels_frame, text="RECEIVED" if is_income else "SPENT", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=header_bg).grid(row=0, column=1, sticky="e", padx=(0, 18))
        tk.Label(self.header_labels_frame, text="LEFTOVER", font=Theme.FONT_LABEL, fg=Theme.TEXT_MUTED, bg=header_bg).grid(row=0, column=2, sticky="e", padx=(0, 18))

        # 2. Body Container
        self.body_frame = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=4)

        self._render_category_grid()

        if self.is_expanded:
            self.lbl_arrow.config(text="v")
            self.header_labels_frame.pack(side=tk.RIGHT)
            self.body_frame.pack(fill=tk.X)
        else:
            self.lbl_arrow.config(text=">")
            self.lbl_summary.pack(side=tk.RIGHT)
            self.body_frame.pack_forget()

    def _render_category_grid(self):
        for child in self.body_frame.winfo_children():
            child.destroy()

        grid_table = tk.Frame(self.body_frame, bg=Theme.BG_CARD)
        grid_table.pack(fill=tk.X)
        self.grid_table = grid_table

        grid_table.columnconfigure(0, weight=1)
        grid_table.columnconfigure(1, minsize=120)
        grid_table.columnconfigure(2, minsize=120)
        grid_table.columnconfigure(3, minsize=120)
        grid_table.columnconfigure(4, minsize=40)

        if not self.group.categories:
            lbl_empty = tk.Label(
                grid_table,
                text="No envelopes in this group yet.",
                font=Theme.FONT_ITALIC_MUTED,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_empty.grid(row=1, column=0, columnspan=5, sticky="w", pady=8)
            current_row = 2
        else:
            current_row = 1
            for cat in self.group.categories:
                # 1px Hairline Divider
                div = tk.Frame(grid_table, bg=Theme.BORDER_HAIRLINE, height=1)
                div.grid(row=current_row, column=0, columnspan=5, sticky="ew", pady=3)
                current_row += 1

                # Column 0: Category Name
                l_name = tk.Label(
                    grid_table,
                    text=cat.name,
                    font=Theme.FONT_LABEL,
                    fg=Theme.TEXT_PRIMARY,
                    bg=Theme.BG_CARD,
                    cursor="xterm"
                )
                l_name.grid(row=current_row, column=0, sticky="w", pady=3)
                l_name.bind("<Button-1>", lambda e, c=cat, l=l_name: self._start_inline_name_edit(c, l, grid_table))

                # Column 1: Planned (Input Bounding Box)
                l_planned = tk.Label(
                    grid_table,
                    text=f"${cat.planned_amount:,.2f}",
                    font=Theme.FONT_LABEL,
                    fg=Theme.TEXT_PRIMARY,
                    bg=Theme.INPUT_BG,
                    highlightthickness=1,
                    highlightbackground=Theme.INPUT_BORDER,
                    padx=8,
                    pady=2,
                    cursor="hand2"
                )
                l_planned.grid(row=current_row, column=1, sticky="e", padx=(0, 10), pady=3)
                l_planned.bind("<Button-1>", lambda e, c=cat, l=l_planned: self._start_inline_amount_edit(c, l, grid_table))

                # Column 2: Actual / Spent
                actual_val = cat.get_actual_amount()
                l_actual = tk.Label(
                    grid_table,
                    text=f"${actual_val:,.2f}",
                    font=Theme.FONT_LABEL,
                    fg=Theme.TEXT_PRIMARY,
                    bg=Theme.BG_CARD
                )
                l_actual.grid(row=current_row, column=2, sticky="e", padx=(0, 18), pady=3)

                # Column 3: Remaining / Leftover (Status Pill)
                rem_val = cat.get_remaining_amount()
                if self.group.group_type == "income":
                    if actual_val >= cat.planned_amount and cat.planned_amount > 0:
                        pill_bg, pill_fg = Theme.PILL_SUCCESS_BG, Theme.PILL_SUCCESS_TEXT
                    else:
                        pill_bg, pill_fg = Theme.PILL_NEUTRAL_BG, Theme.PILL_NEUTRAL_TEXT
                else:
                    if rem_val > 0:
                        pill_bg, pill_fg = Theme.PILL_SUCCESS_BG, Theme.PILL_SUCCESS_TEXT
                    elif rem_val == 0:
                        pill_bg, pill_fg = Theme.PILL_NEUTRAL_BG, Theme.PILL_NEUTRAL_TEXT
                    else:
                        pill_bg, pill_fg = Theme.PILL_DANGER_BG, Theme.PILL_DANGER_TEXT

                rem_text = f"-${abs(rem_val):,.2f}" if rem_val < 0 else f"${rem_val:,.2f}"

                lbl_pill = tk.Label(
                    grid_table,
                    text=rem_text,
                    font=Theme.FONT_LABEL,
                    fg=pill_fg,
                    bg=pill_bg,
                    padx=8,
                    pady=2
                )
                lbl_pill.grid(row=current_row, column=3, sticky="e", padx=(0, 18), pady=3)

                # Column 4: Delete Button (Clickable Label - no macOS native bezel)
                btn_del = tk.Label(
                    grid_table,
                    text="✕",
                    font=Theme.FONT_HEADER,
                    fg=Theme.BG_CARD,  # Starts invisible by matching card bg
                    bg=Theme.BG_CARD,
                    cursor="hand2"
                )
                btn_del.grid(row=current_row, column=4, sticky="e", padx=(4, 0))
                btn_del.bind("<Button-1>", lambda e, n=cat.name: self.on_delete_category(n))

                # Hover-to-Reveal Wiring
                def make_row_hover(b_del, widgets):
                    def _enter(e):
                        b_del.config(fg=Theme.DANGER)
                    def _leave(e):
                        b_del.config(fg=Theme.BG_CARD)

                    for w in widgets:
                        w.bind("<Enter>", _enter, add="+")
                        w.bind("<Leave>", _leave, add="+")

                make_row_hover(btn_del, [l_name, l_planned, l_actual, lbl_pill, btn_del])

                current_row += 1

        # Footer Action Bar: Flat Ghost Text Links (Clickable Labels)
        self.footer_frame = tk.Frame(self.body_frame, bg=Theme.BG_CARD)
        self.footer_frame.pack(fill=tk.X, pady=(6, 4))

        add_btn_text = "+ Add Income" if self.group.group_type == "income" else "+ Add Expense"
        btn_add = tk.Label(
            self.footer_frame,
            text=add_btn_text,
            font=Theme.FONT_LABEL,
            fg=Theme.ACCENT_PRIMARY,
            bg=Theme.BG_CARD,
            cursor="hand2"
        )
        btn_add.pack(side=tk.LEFT, padx=0, pady=2)
        btn_add.bind("<Button-1>", lambda e: self._toggle_inline_add_row())
        btn_add.bind("<Enter>", lambda e: btn_add.config(fg=Theme.BRAND_HIGHLIGHT))
        btn_add.bind("<Leave>", lambda e: btn_add.config(fg=Theme.ACCENT_PRIMARY))

        if self.group.group_type != "income":
            btn_del_grp = tk.Label(
                self.footer_frame,
                text="Delete Group",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                cursor="hand2"
            )
            btn_del_grp.pack(side=tk.RIGHT, padx=0, pady=2)
            btn_del_grp.bind("<Button-1>", lambda e: self.on_delete_group(self.group.name))
            btn_del_grp.bind("<Enter>", lambda e: btn_del_grp.config(fg=Theme.DANGER))
            btn_del_grp.bind("<Leave>", lambda e: btn_del_grp.config(fg=Theme.TEXT_MUTED))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.lbl_arrow.config(text="v")
            self.lbl_summary.pack_forget()
            self.header_labels_frame.pack(side=tk.RIGHT)
            self.body_frame.pack(fill=tk.X)
        else:
            self.lbl_arrow.config(text=">")
            self.header_labels_frame.pack_forget()
            self.lbl_summary.pack(side=tk.RIGHT)
            self.body_frame.pack_forget()
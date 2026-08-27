"""
File: source/gui/widgets/category_group_card.py
Purpose: Main container for category groups combining layout, mixins, and grid rendering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from source.domain.category import Category
from source.domain.category_group import CategoryGroup
from source.gui.widgets.card_drag_mixin import CardDragMixin
from source.gui.widgets.card_inline_edit_mixin import CardInlineEditMixin

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
        super().__init__(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0", bd=0, **kwargs)
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
        self.header_frame = tk.Frame(self, bg="#f8fafc", padx=12, pady=10)
        self.header_frame.pack(fill=tk.X)

        controls_left = tk.Frame(self.header_frame, bg="#f8fafc")
        controls_left.pack(side=tk.LEFT)

        if self.group.group_type != "income":
            self.lbl_grip = tk.Label(
                controls_left, text="⋮⋮", font=("Helvetica", 14, "bold"),
                bg="#f8fafc", fg="#94a3b8", cursor="fleur"
            )
            self.lbl_grip.pack(side=tk.LEFT, padx=(0, 8))
            self._bind_drag_events(self.lbl_grip)

        self.lbl_arrow = tk.Label(
            controls_left, text="▾", font=("Helvetica", 12, "bold"),
            bg="#f8fafc", fg="#475569", cursor="hand2"
        )
        self.lbl_arrow.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_arrow.bind("<Button-1>", lambda e: self.toggle_expand())

        self.lbl_title = tk.Label(
            controls_left, text=self.group.name, font=("Helvetica", 12, "bold"),
            bg="#f8fafc", fg="#0f172a", cursor="xterm"
        )
        self.lbl_title.pack(side=tk.LEFT)
        self.lbl_title.bind("<Button-1>", lambda e: self._start_inline_group_name_edit())

        total_planned = self.group.get_total_planned()
        total_actual = self.group.get_total_actual()
        actual_label = "Received" if self.group.group_type == "income" else "Spent"

        summary_text = f"Planned: ${total_planned:,.2f}  |  {actual_label}: ${total_actual:,.2f}"
        self.lbl_summary = tk.Label(
            self.header_frame, text=summary_text, font=("Helvetica", 10, "bold"),
            bg="#f8fafc", fg="#64748b"
        )
        self.lbl_summary.pack(side=tk.RIGHT)

        # 2. Body Container
        self.body_frame = tk.Frame(self, bg="#ffffff", padx=16, pady=6)
        self.body_frame.pack(fill=tk.X)

        self._render_category_grid()

        if not self.is_expanded:
            self.lbl_arrow.config(text="▸")
            self.body_frame.pack_forget()

    def _render_category_grid(self):
        for child in self.body_frame.winfo_children():
            child.destroy()

        if not self.group.categories:
            lbl_empty = tk.Label(
                self.body_frame, text="No envelopes in this group yet.",
                font=("Helvetica", 10, "italic"), fg="#94a3b8", bg="#ffffff", pady=8
            )
            lbl_empty.pack(anchor="w")
        else:
            grid_table = tk.Frame(self.body_frame, bg="#ffffff")
            grid_table.pack(fill=tk.X)

            grid_table.columnconfigure(0, weight=1)
            grid_table.columnconfigure(1, minsize=120)
            grid_table.columnconfigure(2, minsize=140)
            grid_table.columnconfigure(3, minsize=120)
            grid_table.columnconfigure(4, minsize=40)

            actual_header = "RECEIVED" if self.group.group_type == "income" else "SPENT"
            tk.Label(grid_table, text="CATEGORY", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=(0, 6))
            tk.Label(grid_table, text="PLANNED", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=1, sticky="e", padx=(0, 10), pady=(0, 6))
            tk.Label(grid_table, text=actual_header, font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=2, sticky="e", padx=(0, 10), pady=(0, 6))
            tk.Label(grid_table, text="REMAINING", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=3, sticky="e", padx=(0, 10), pady=(0, 6))

            current_row = 1
            for cat in self.group.categories:
                div = tk.Frame(grid_table, bg="#f1f5f9", height=1)
                div.grid(row=current_row, column=0, columnspan=5, sticky="ew", pady=2)
                current_row += 1

                l_name = tk.Label(grid_table, text=cat.name, font=("Helvetica", 11), fg="#1e293b", bg="#ffffff", cursor="xterm")
                l_name.grid(row=current_row, column=0, sticky="w", pady=4)
                l_name.bind("<Button-1>", lambda e, c=cat, l=l_name: self._start_inline_name_edit(c, l, grid_table))

                l_planned = tk.Label(grid_table, text=f"${cat.planned_amount:,.2f}", font=("Helvetica", 11), fg="#0284c7", bg="#ffffff", cursor="hand2")
                l_planned.grid(row=current_row, column=1, sticky="e", padx=(0, 10), pady=4)
                l_planned.bind("<Button-1>", lambda e, c=cat, l=l_planned: self._start_inline_amount_edit(c, l, grid_table))

                actual_val = cat.get_actual_amount()
                tk.Label(grid_table, text=f"${actual_val:,.2f}", font=("Helvetica", 11), fg="#334155", bg="#ffffff").grid(row=current_row, column=2, sticky="e", padx=(0, 10), pady=4)

                rem_val = cat.get_remaining_amount()
                if self.group.group_type == "income":
                    rem_color = "#16a34a" if actual_val >= cat.planned_amount else "#dc2626"
                else:
                    rem_color = "#dc2626" if rem_val < 0 else "#16a34a"

                tk.Label(grid_table, text=f"${rem_val:,.2f}", font=("Helvetica", 11, "bold"), fg=rem_color, bg="#ffffff").grid(row=current_row, column=3, sticky="e", padx=(0, 10), pady=4)

                btn_del = tk.Button(
                    grid_table, text="✕", font=("Helvetica", 10), fg="#ef4444", bg="#ffffff",
                    relief=tk.FLAT, bd=0, cursor="hand2", command=lambda n=cat.name: self.on_delete_category(n)
                )
                btn_del.grid(row=current_row, column=4, sticky="e", padx=(4, 0))

                current_row += 1

        # Footer Action Bar
        self.footer_frame = tk.Frame(self.body_frame, bg="#ffffff")
        self.footer_frame.pack(fill=tk.X, pady=(12, 4))

        add_btn_text = "+ Add Income" if self.group.group_type == "income" else "+ Add Expense"
        btn_add = ttk.Button(
            self.footer_frame, text=add_btn_text, cursor="hand2",
            command=self._toggle_inline_add_row
        )
        btn_add.pack(side=tk.LEFT)

        if self.group.group_type != "income":
            btn_del_grp = tk.Button(
                self.footer_frame, text="Delete Group", font=("Helvetica", 9),
                fg="#94a3b8", bg="#ffffff", activeforeground="#ef4444", activebackground="#ffffff",
                relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.on_delete_group(self.group.name)
            )
            btn_del_grp.pack(side=tk.RIGHT)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.lbl_arrow.config(text="▾")
            self.body_frame.pack(fill=tk.X)
        else:
            self.lbl_arrow.config(text="▸")
            self.body_frame.pack_forget()
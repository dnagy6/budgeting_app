"""
File: source/gui/widgets/category_group_card.py
Purpose: Collapsible Accordion Card widget for displaying category groups and child envelopes.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from source.domain.category import Category
from source.domain.category_group import CategoryGroup


class CategoryGroupCard(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        group: CategoryGroup,
        on_add_category: Callable[[str, str], None],
        on_edit_category: Callable[[Category], None],
        on_delete_category: Callable[[str], None],
        on_delete_group: Callable[[str], None],
        **kwargs
    ):
        super().__init__(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0", bd=0, **kwargs)
        self.group = group
        self.on_add_category = on_add_category
        self.on_edit_category = on_edit_category
        self.on_delete_category = on_delete_category
        self.on_delete_group = on_delete_group
        self.is_expanded = True

        self._create_ui()

    def _create_ui(self):
        # 1. Group Header Bar
        self.header_frame = tk.Frame(self, bg="#f8fafc", padx=12, pady=10, cursor="hand2")
        self.header_frame.pack(fill=tk.X)
        self.header_frame.bind("<Button-1>", lambda e: self.toggle_expand())

        # Expand / Collapse Arrow Icon
        self.lbl_arrow = tk.Label(
            self.header_frame,
            text="▾",
            font=("Helvetica", 12, "bold"),
            bg="#f8fafc",
            fg="#475569"
        )
        self.lbl_arrow.pack(side=tk.LEFT, padx=(0, 6))

        # Group Name
        lbl_title = tk.Label(
            self.header_frame,
            text=self.group.name,
            font=("Helvetica", 12, "bold"),
            bg="#f8fafc",
            fg="#0f172a"
        )
        lbl_title.pack(side=tk.LEFT)

        # Delete Group Button (Right-most)
        btn_del_group = tk.Button(
            self.header_frame,
            text="✕",
            font=("Helvetica", 10),
            fg="#94a3b8",
            activeforeground="#ef4444",
            bg="#f8fafc",
            activebackground="#f8fafc",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.on_delete_group(self.group.name)
        )
        btn_del_group.pack(side=tk.RIGHT, padx=(8, 0))

        # Header Summary Totals (Planned vs Spent/Received)
        total_planned = self.group.get_total_planned()
        total_actual = self.group.get_total_actual()
        actual_label = "Received" if self.group.group_type == "income" else "Spent"

        summary_text = f"Planned: ${total_planned:,.2f}   |   {actual_label}: ${total_actual:,.2f}"
        self.lbl_summary = tk.Label(
            self.header_frame,
            text=summary_text,
            font=("Helvetica", 10, "bold"),
            bg="#f8fafc",
            fg="#64748b"
        )
        self.lbl_summary.pack(side=tk.RIGHT)

        # 2. Body Container (Child Envelopes)
        self.body_frame = tk.Frame(self, bg="#ffffff", padx=12, pady=4)
        self.body_frame.pack(fill=tk.X)

        self._render_category_rows()

    def _render_category_rows(self):
        for child in self.body_frame.winfo_children():
            child.destroy()

        if not self.group.categories:
            lbl_empty = tk.Label(
                self.body_frame,
                text="No envelopes in this group yet.",
                font=("Helvetica", 9, "italic"),
                fg="#94a3b8",
                bg="#ffffff",
                pady=6
            )
            lbl_empty.pack(anchor="w")
        else:
            # Table Header for Child Rows
            header_row = tk.Frame(self.body_frame, bg="#ffffff", pady=4)
            header_row.pack(fill=tk.X)

            tk.Label(header_row, text="CATEGORY", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff", width=22, anchor="w").pack(side=tk.LEFT)
            tk.Label(header_row, text="PLANNED", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff", width=14, anchor="e").pack(side=tk.LEFT)
            tk.Label(header_row, text="SPENT / RECEIVED", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff", width=18, anchor="e").pack(side=tk.LEFT)
            tk.Label(header_row, text="REMAINING", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff", width=14, anchor="e").pack(side=tk.LEFT)
            tk.Label(header_row, text="", width=8, bg="#ffffff").pack(side=tk.RIGHT)

            # Item Rows
            for cat in self.group.categories:
                self._create_category_row(cat)

        # 3. Card Footer Action (+ Add Item)
        btn_label = "+ Add Income" if self.group.group_type == "income" else "+ Add Expense"
        btn_add = tk.Button(
            self.body_frame,
            text=btn_label,
            font=("Helvetica", 10, "bold"),
            fg="#0284c7",
            bg="#ffffff",
            activeforeground="#0369a1",
            activebackground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.on_add_category(self.group.name, self.group.group_type)
        )
        btn_add.pack(anchor="w", pady=(8, 4))

    def _create_category_row(self, cat: Category):
        row = tk.Frame(self.body_frame, bg="#ffffff", pady=6)
        row.pack(fill=tk.X)

        # Divider line
        div = tk.Frame(self.body_frame, bg="#f1f5f9", height=1)
        div.pack(fill=tk.X)

        # Name
        lbl_name = tk.Label(row, text=cat.name, font=("Helvetica", 11), fg="#1e293b", bg="#ffffff", width=22, anchor="w")
        lbl_name.pack(side=tk.LEFT)

        # Planned
        lbl_planned = tk.Label(row, text=f"${cat.planned_amount:,.2f}", font=("Helvetica", 11), fg="#334155", bg="#ffffff", width=14, anchor="e")
        lbl_planned.pack(side=tk.LEFT)

        # Actual
        actual_val = cat.get_actual_amount()
        lbl_actual = tk.Label(row, text=f"${actual_val:,.2f}", font=("Helvetica", 11), fg="#334155", bg="#ffffff", width=18, anchor="e")
        lbl_actual.pack(side=tk.LEFT)

        # Remaining
        remaining_val = cat.get_remaining_amount()
        rem_color = "#dc2626" if remaining_val < 0 else "#16a34a"
        lbl_rem = tk.Label(row, text=f"${remaining_val:,.2f}", font=("Helvetica", 11, "bold"), fg=rem_color, bg="#ffffff", width=14, anchor="e")
        lbl_rem.pack(side=tk.LEFT)

        # Actions: Edit & Delete
        actions_frame = tk.Frame(row, bg="#ffffff")
        actions_frame.pack(side=tk.RIGHT)

        btn_edit = tk.Button(
            actions_frame, text="✎", font=("Helvetica", 10),
            fg="#64748b", bg="#ffffff", relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda c=cat: self.on_edit_category(c)
        )
        btn_edit.pack(side=tk.LEFT, padx=2)

        btn_del = tk.Button(
            actions_frame, text="✕", font=("Helvetica", 10),
            fg="#ef4444", bg="#ffffff", relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda n=cat.name: self.on_delete_category(n)
        )
        btn_del.pack(side=tk.LEFT, padx=2)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.lbl_arrow.config(text="▾")
            self.body_frame.pack(fill=tk.X)
        else:
            self.lbl_arrow.config(text="▸")
            self.body_frame.pack_forget()
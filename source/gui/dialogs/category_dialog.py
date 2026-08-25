from decimal import Decimal
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from source.domain.budget import Budget
from source.domain.category import Category
from source.gui.dialogs.base_dialog import BaseDialog
from source.services.budget_service import BudgetService


class AddCategoryDialog(BaseDialog):
    """Pop-up window for adding or editing a category envelope."""

    def __init__(
        self,
        parent: tk.Widget,
        budget: Budget,
        on_success_callback: Callable[[], None],
        existing_category: Optional[Category] = None,
        default_group: Optional[str] = None,
        default_type: str = "expense",
        service: Optional[BudgetService] = None
    ):
        title_text = "Edit Category Envelope" if existing_category else "Add Category Envelope"
        super().__init__(parent, title=title_text, width=460, height=280)

        self.service = service
        self.budget = budget
        self.on_success = on_success_callback
        self.existing_category = existing_category

        # 1. Category Name
        self.name_entry = ttk.Entry(self.main_frame, font=("Helvetica", 10))
        self.add_form_row(0, "Category Name:", self.name_entry)

        # 2. Parent Category Group Dropdown
        existing_groups = []
        if self.service:
            existing_groups = [g.name for g in self.service.repository.get_all_category_groups()]
        elif self.budget.groups:
            existing_groups = [g.name for g in self.budget.groups]

        self.group_var = tk.StringVar(value=default_group or (existing_groups[0] if existing_groups else ""))
        self.group_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.group_var,
            values=existing_groups,
            font=("Helvetica", 10)
        )
        self.add_form_row(1, "Category Group:", self.group_dropdown)

        # 3. Type Dropdown
        self.type_var = tk.StringVar(value=default_type)
        self.type_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.type_var,
            values=["expense", "income"],
            state="readonly",
            font=("Helvetica", 10)
        )
        self.add_form_row(2, "Type:", self.type_dropdown)

        # 4. Planned Amount Entry
        self.amount_entry = ttk.Entry(self.main_frame, font=("Helvetica", 10))
        self.add_form_row(3, "Planned Amount ($):", self.amount_entry)

        # Populate field data if editing
        if existing_category:
            self.name_entry.insert(0, existing_category.name)
            self.type_var.set(existing_category.category_type)
            self.amount_entry.insert(0, str(existing_category.planned_amount))
            # Find current group
            for grp in self.budget.groups:
                if existing_category in grp.categories:
                    self.group_var.set(grp.name)
                    break

        self.name_entry.focus()

        # Save Button
        btn_text = "Update Envelope" if existing_category else "Save Envelope"
        btn_save = ttk.Button(self.main_frame, text=btn_text, command=self.save_category)
        btn_save.grid(row=4, column=0, columnspan=2, pady=20)

    def save_category(self):
        name = self.name_entry.get().strip()
        group_name = self.group_var.get().strip()
        category_type = self.type_var.get().strip().lower()
        amount_raw = self.amount_entry.get().strip()

        if not name:
            messagebox.showwarning("Input Error", "Please enter a category name.", parent=self)
            return

        try:
            amount = float(amount_raw) if amount_raw else 0.0
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Planned amount must be a positive number.", parent=self)
            return

        if self.service:
            old_name = self.existing_category.name if self.existing_category else None
            self.service.save_category(
                budget=self.budget,
                name=name,
                category_type=category_type,
                planned_amount=amount,
                group_name=group_name if group_name else None,
                old_name=old_name
            )
        else:
            self.budget.add_or_update_category(
                name=name,
                category_type=category_type,
                planned_amount=amount,
                group_name=group_name
            )

        self.on_success()
        self.destroy()
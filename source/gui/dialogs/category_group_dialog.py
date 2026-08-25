"""
Purpose: Pop-up modal to create or edit parent category groups.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from source.gui.dialogs.base_dialog import BaseDialog
from source.services.budget_service import BudgetService


class AddCategoryGroupDialog(BaseDialog):
    def __init__(
        self,
        parent: tk.Widget,
        on_success_callback: Callable[[], None],
        service: BudgetService
    ):
        super().__init__(parent, title="Add Category Group", width=420, height=200)
        self.service = service
        self.on_success = on_success_callback

        # 1. Group Name
        self.name_entry = ttk.Entry(self.main_frame, font=("Helvetica", 11))
        self.add_form_row(0, "Group Name:", self.name_entry)

        # 2. Group Type
        self.type_var = tk.StringVar(value="expense")
        self.type_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.type_var,
            values=["expense", "income"],
            state="readonly",
            font=("Helvetica", 10)
        )
        self.add_form_row(1, "Group Type:", self.type_dropdown)

        self.name_entry.focus()

        # 3. Submit Button
        btn_save = ttk.Button(self.main_frame, text="Create Group", command=self.save_group)
        btn_save.grid(row=2, column=0, columnspan=2, pady=20)

    def save_group(self):
        name = self.name_entry.get().strip()
        group_type = self.type_var.get().strip().lower()

        if not name:
            messagebox.showwarning("Input Error", "Please enter a group name.", parent=self)
            return

        # Save to database
        self.service.repository.add_category_group(name=name, group_type=group_type)
        self.on_success()
        self.destroy()
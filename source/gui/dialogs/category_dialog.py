import tkinter as tk
from tkinter import ttk, messagebox
from source.domain.category import Category
from source.gui.dialogs.base_dialog import BaseDialog


class AddCategoryDialog(BaseDialog):
    """Pop-up window for adding or editing a category envelope."""

    def __init__(self, parent, budget, on_success_callback, existing_category=None):
        title_text = "Edit Category Envelope" if existing_category else "Add Category Envelope"
        super().__init__(parent, title=title_text, width=450, height=240)

        self.budget = budget
        self.on_success = on_success_callback
        self.existing_category = existing_category

        # Form Inputs
        self.name_entry = ttk.Entry(self.main_frame)
        self.add_form_row(0, "Category Name:", self.name_entry)

        self.type_var = tk.StringVar(value="expense")
        self.type_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.type_var,
            values=["expense", "income"],
            state="readonly"
        )
        self.add_form_row(1, "Type:", self.type_dropdown)

        self.amount_entry = ttk.Entry(self.main_frame)
        self.add_form_row(2, "Planned Amount ($):", self.amount_entry)

        # Populate field data if editing an existing envelope
        if existing_category:
            self.name_entry.insert(0, existing_category.name)
            self.type_var.set(existing_category.category_type)
            self.amount_entry.insert(0, str(existing_category.planned_amount))

        self.name_entry.focus()

        # Save Button
        btn_text = "Update Envelope" if existing_category else "Save Envelope"
        btn_save = ttk.Button(self.main_frame, text=btn_text, command=self.save_category)
        btn_save.grid(row=3, column=0, columnspan=2, pady=20)

    def save_category(self):
        name = self.name_entry.get().strip()
        category_type = self.type_var.get().strip()
        amount_raw = self.amount_entry.get().strip()  # Fixed: reading from self.amount_entry

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

        self.budget.add_or_update_category(
            name=name,
            category_type=category_type,
            planned_amount=amount
        )
        self.on_success()
        self.destroy()
"""
File: source/gui/dialogs/transaction_dialog.py
Purpose: Pop-up window for logging a new income or expense transaction.

What this file does:
- Displays a form to pick a category envelope, dollar amount, description, and date.
- Validates the input numbers and text to ensure they are valid.
- Creates a new transaction and adds it to the chosen category envelope.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from source.domain.transaction import Transaction
from source.gui.dialogs.base_dialog import BaseDialog


class LogTransactionDialog(BaseDialog):
    """Pop-up window for logging a new transaction against a category envelope."""

    def __init__(self, parent, budget, on_success_callback):
        super().__init__(parent, title="Log Transaction", width=450, height=280)

        self.budget = budget
        self.on_success = on_success_callback

        # Category Dropdown
        category_names = [cat.name for cat in self.budget.categories]
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.category_var,
            values=category_names,
            state="readonly" if category_names else "disabled"
        )
        self.add_form_row(0, "Category Envelope:", self.category_dropdown)
        if category_names:
            self.category_dropdown.current(0)

        # Amount Entry
        self.amount_entry = ttk.Entry(self.main_frame)
        self.add_form_row(1, "Amount ($):", self.amount_entry)

        # Description Entry
        self.desc_entry = ttk.Entry(self.main_frame)
        self.add_form_row(2, "Description:", self.desc_entry)

        # Date Entry
        self.date_entry = ttk.Entry(self.main_frame)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.add_form_row(3, "Date (YYYY-MM-DD):", self.date_entry)

        self.amount_entry.focus()

        # Action Button
        btn_save = ttk.Button(self.main_frame, text="Log Transaction", command=self.save_transaction)
        btn_save.grid(row=4, column=0, columnspan=2, pady=(18, 0))

    def save_transaction(self):
        """Validate input and attach transaction to selected category envelope."""
        cat_name = self.category_var.get().strip()
        amount_raw = self.amount_entry.get().strip()
        description = self.desc_entry.get().strip()
        date_str = self.date_entry.get().strip()

        if not cat_name:
            messagebox.showwarning("Input Error", "Please select a category envelope.", parent=self)
            return

        if not description:
            messagebox.showwarning("Input Error", "Please enter a description for the transaction.", parent=self)
            return

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a positive number greater than 0.", parent=self)
            return

        selected_cat = self.budget.get_category_by_name(cat_name)
        if not selected_cat:
            messagebox.showerror("Error", "Selected category could not be found.", parent=self)
            return

        try:
            tx = Transaction(amount=amount, description=description, date=date_str if date_str else None)
            selected_cat.add_transaction(tx)
        except ValueError as e:
            messagebox.showwarning("Input Error", str(e), parent=self)
            return

        self.on_success()
        self.destroy()




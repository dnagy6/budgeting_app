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

class LogTransactionDialog(tk.Toplevel):
    """Pop up window for logging a new transaction against a specified category envelope."""

    def __init__(self, parent, budget, on_success_callback):
        super().__init__(parent)
        self.budget = budget
        self.on_success = on_success_callback

        self.title("Log Transaction")
        self.geometry("400x300")
        self.resizable(False, False)

        # window focus and stays on top
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        frame = ttk.Frame(self, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Selection of category envelope as Dropdown menu
        ttk.Label(frame, text="Category Envelope:").grid(row=0, column=0, sticky=tk.W, pady=5)
        category_names = [cat.name for cat in self.budget.categories]
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=category_names,
            state="readonly" if category_names else "disabled",
            width=23
        )
        self.category_dropdown.grid(row=0, column=1, pady=5)
        if category_names:
            self.category_dropdown.current(0)

        # Amount Input
        ttk.Label(frame, text="Amount ($):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_entry = ttk.Entry(frame, width=25)
        self.amount_entry.grid(row=1, column=1, pady=5)

        # Description Input
        ttk.Label(frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(frame, width=25)
        self.desc_entry.grid(row=2, column=1, pady=5)

        # Date Input with a default value of today's date
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(frame, width=25)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=1, pady=5)

        self.amount_entry.focus()

        # button to save the transaction and prepare to close the dialog
        btn_save = ttk.Button(frame, text="Log Transaction", command=self.save_transaction)
        btn_save.grid(row=4, column=0, columnspan=2, pady=20)

    def save_transaction(self):
        """Validate the users input and create a new transaction IF the input is a valid entry."""

        cat_name = self.category_var.get().strip()
        amount_raw = self.amount_entry.get().strip()
        description = self.desc_entry.get().strip()
        date_str = self.date_entry.get().strip()

        if not cat_name:
            messagebox.showerror("Input Error", "Please select an existing category envelope.", parent = self)
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




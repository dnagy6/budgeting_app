import tkinter as tk
from tkinter import ttk, messagebox
from source.domain.category import Category


class AddCategoryDialog(tk.Toplevel):
    """Pop-up window for adding or editing a category envelope."""

    def __init__(self, parent, budget, on_success_callback, existing_category=None):
        super().__init__(parent)
        self.budget = budget
        self.on_success = on_success_callback
        self.existing_category = existing_category

        dialog_title = "Edit Category Envelope" if existing_category else "Add Category Envelope"
        self.title(dialog_title)
        self.geometry("380x250")
        self.resizable(False, False)

        # Ensure dialog stays on top and retains window focus
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        # Layout
        frame = ttk.Frame(self, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Name Input
        ttk.Label(frame, text="Category Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=25)
        self.name_entry.grid(row=0, column=1, pady=5)

        # Type Dropdown
        ttk.Label(frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="expense")
        self.type_dropdown = ttk.Combobox(
            frame,
            textvariable=self.type_var,
            values=["expense", "income"],
            state="readonly",
            width=23
        )
        self.type_dropdown.grid(row=1, column=1, pady=5)

        # Planned Amount Input
        ttk.Label(frame, text="Planned Amount ($):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.planned_entry = ttk.Entry(frame, width=25)
        self.planned_entry.grid(row=2, column=1, pady=5)

        # Pre-fill if editing
        if self.existing_category:
            self.name_entry.insert(0, self.existing_category.name)
            self.type_var.set(self.existing_category.category_type)
            self.planned_entry.insert(0, f"{self.existing_category.planned_amount:.2f}")

        self.name_entry.focus()

        # Save Button
        btn_text = "Update Envelope" if existing_category else "Save Envelope"
        btn_save = ttk.Button(frame, text=btn_text, command=self.save_category)
        btn_save.grid(row=3, column=0, columnspan=2, pady=20)

    def save_category(self):
        name = self.name_entry.get().strip()
        cat_type = self.type_var.get().strip()
        planned_raw = self.planned_entry.get().strip()

        if not name:
            messagebox.showwarning("Input Error", "Please enter a category name.", parent=self)
            return

        try:
            planned = float(planned_raw)
            if planned < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Planned amount must be a valid positive number.", parent=self)
            return

        self.budget.add_or_update_category(name, cat_type, planned)
        self.on_success()
        self.destroy()
import tkinter as tk
from tkinter import ttk, messagebox
from source.models import Budget, Category, Transaction

class AddCategoryDialog(tk.Toplevel):
    """Pop-up window for adding or updating a category envelope."""

    def __init__(self, parent, budget, on_success_callback, existing_category = None):
        super().__init__(parent)
        self.budget = budget
        self.on_success = on_success_callback
        self.existing_category = existing_category

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.title("Add / Edit Category Envelope")
        self.geometry("380x250")
        self.resizable(False, False)
        self.grab_set()  # Focus on this window until closed

        # Form Layout
        frame = ttk.Frame(self, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Category Name
        ttk.Label(frame, text="Category Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=25)
        self.name_entry.grid(row=0, column=1, pady=5)
        self.name_entry.focus()

        # Category Type
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

        # Planned Amount
        ttk.Label(frame, text="Planned Amount ($):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.planned_entry = ttk.Entry(frame, width=25)
        self.planned_entry.grid(row=2, column=1, pady=5)

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

        # Call domain logic
        cat, is_new = self.budget.add_or_update_category(name, cat_type, planned)
        self.on_success()
        self.destroy()


class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zero-Based Budgeting App")
        self.root.geometry("750x550")
        self.root.minsize(650, 450)

        # In-memory storage for budgets: (year, month) -> Budget
        self.budgets = {}
        self.current_year = 2026
        self.current_month = 8
        self.rollovers = {}

        # Load or initialize active budget
        self.current_budget = self.get_or_create_budget(self.current_year, self.current_month)

        # Build the user interface layout
        self.create_header_ui()
        self.create_summary_ui()
        self.create_category_table_ui()
        self.create_action_buttons_ui()

        # Populate initial view
        self.refresh_ui()

    def get_or_create_budget(self, year, month):
        key = (year, month)
        if key not in self.budgets:
            self.budgets[key] = Budget(month=month, year=year, categories=[])
        return self.budgets[key]

# UI Components:

    def create_header_ui(self):
        """Top banner showing active month/year."""
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        self.title_label = ttk.Label(
            header_frame,
            text=f"Budget Overview — {self.current_month}/{self.current_year}",
            font=("Helvetica", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT)

    def create_summary_ui(self):
        """Cards displaying live total calculations."""
        summary_frame = ttk.LabelFrame(self.root, text=" Monthly Totals ", padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        # Total Income
        ttk.Label(summary_frame, text="Total Income:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=10)
        self.income_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10))
        self.income_val_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Total Allocated
        ttk.Label(summary_frame, text="Total Allocated:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky=tk.W, padx=10)
        self.allocated_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10))
        self.allocated_val_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        # Left to Budget
        ttk.Label(summary_frame, text="Left to Budget:", font=("Helvetica", 10, "bold")).grid(row=0, column=4, sticky=tk.W, padx=10)
        self.unallocated_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10, "bold"))
        self.unallocated_val_label.grid(row=0, column=5, sticky=tk.W)

    def create_category_table_ui(self):
        """Data grid showing all category envelopes."""
        table_frame = ttk.LabelFrame(self.root, text=" Category Envelopes ", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Define columns
        columns = ("type", "name", "planned", "actual", "remaining")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        # Define headers
        self.tree.heading("type", text="Type")
        self.tree.heading("name", text="Category Name")
        self.tree.heading("planned", text="Planned")
        self.tree.heading("actual", text="Actual (Spent/Received)")
        self.tree.heading("remaining", text="Remaining / Pending")

        # Column widths
        self.tree.column("type", width=80, anchor=tk.CENTER)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("planned", width=110, anchor=tk.E)
        self.tree.column("actual", width=150, anchor=tk.E)
        self.tree.column("remaining", width=150, anchor=tk.E)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        #Double-click Shortcut to Edit Category
        self.tree.bind("<Double-1>", lambda event: self.open_edit_category_dialog())

    def create_action_buttons_ui(self):
        """Bottom toolbar with action buttons."""
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)

        btn_add_cat = ttk.Button(
            action_frame,
            text="Add Category",
            command=self.open_add_category_dialog
        )
        btn_add_cat.pack(side=tk.LEFT, padx=5)

        btn_edit_cat = ttk.Button(
            action_frame,
            text="Edit Selected",
            command=self.open_edit_category_dialog
        )
        btn_edit_cat.pack(side=tk.LEFT, padx=5)

        btn_log_tx = ttk.Button(action_frame, text="Log Transaction", command=self.placeholder_action)
        btn_log_tx.pack(side=tk.LEFT, padx=5)

        btn_rollover = ttk.Button(action_frame, text="Close Month & Roll Over", command=self.placeholder_action)
        btn_rollover.pack(side=tk.LEFT, padx=5)

#Action Handlers:
    def open_add_category_dialog(self):
        """Always opens a blank dialog to add a new envelope."""
        AddCategoryDialog(self.root, self.current_budget, self.refresh_ui, existing_category=None)

    def open_edit_category_dialog(self):
        """Edits the currently highlighted category row."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a category from the table first.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        cat_name = item_values[1]
        selected_cat = self.current_budget.get_category_by_name(cat_name)

        if selected_cat:
            AddCategoryDialog(self.root, self.current_budget, self.refresh_ui, existing_category=selected_cat)

    def placeholder_action(self):
        messagebox.showinfo("In Progress", "This button will trigger a dialog box in our next step!")

    # ------------------------------------------------------------------
    # Data Refresh & Render
    # ------------------------------------------------------------------

    def refresh_ui(self):
        """Refreshes summary cards and table rows with current domain data."""
        # Update Title Header
        self.title_label.config(text=f"Budget Overview — {self.current_month}/{self.current_year}")

        # Update Totals
        rollover_cash = self.rollovers.get((self.current_year, self.current_month), 0.0)
        total_income = self.current_budget.get_total_income() + rollover_cash
        total_allocated = self.current_budget.get_total_allocated()
        unallocated = total_income - total_allocated

        self.income_val_label.config(text=f"${total_income:,.2f}")
        self.allocated_val_label.config(text=f"${total_allocated:,.2f}")

        # Highlight negative unallocated amounts
        if unallocated < 0:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", foreground="red")
        else:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", foreground="black")

        # Clear existing table rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate table rows
        for cat in self.current_budget.categories:
            cat_type = cat.category_type.capitalize()
            actual = cat.get_actual_amount()
            remaining = cat.get_remaining_amount()

            self.tree.insert(
                "",
                tk.END,
                values=(
                    cat_type,
                    cat.name,
                    f"${cat.planned_amount:,.2f}",
                    f"${actual:,.2f}",
                    f"${remaining:,.2f}"
                )
            )

def launch_gui():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
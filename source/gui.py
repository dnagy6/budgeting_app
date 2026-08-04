import tkinter as tk
from tkinter import ttk, messagebox
from models import Budget, Category, Transaction

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

    def create_action_buttons_ui(self):
        """Bottom toolbar with action buttons."""
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)

        btn_add_cat = ttk.Button(action_frame, text="Add / Edit Category", command=self.placeholder_action)
        btn_add_cat.pack(side=tk.LEFT, padx=5)

        btn_log_tx = ttk.Button(action_frame, text="Log Transaction", command=self.placeholder_action)
        btn_log_tx.pack(side=tk.LEFT, padx=5)

        btn_rollover = ttk.Button(action_frame, text="Close Month & Roll Over", command=self.placeholder_action)
        btn_rollover.pack(side=tk.LEFT, padx=5)

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

    def placeholder_action(self):
        messagebox.showinfo("In Progress", "This button will trigger a dialog box in our next step!")


def launch_gui():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
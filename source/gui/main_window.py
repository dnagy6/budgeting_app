import tkinter as tk
from tkinter import ttk, messagebox
from source.domain.budget import Budget
from source.domain.transaction import Transaction
from source.gui.dialogs.category_dialog import AddCategoryDialog
from source.gui.dialogs.transaction_dialog import LogTransactionDialog
from source.persistence.repository import BudgetRepository


class BudgetApp:
    def __init__(self, root, repository: BudgetRepository):
        self.root = root
        self.repository = repository
        self.root.title("Zero-Based Budgeting App")
        self.root.geometry("820x550")
        self.root.minsize(650, 450)

        # Storage
        self.budgets = {}
        self.current_year = 2026
        self.current_month = 8
        self.rollovers = {}

        # Active budget
        self.current_budget = self.get_or_create_budget(self.current_year, self.current_month)

        #Load SAVED Data from DB upon starting application
        self.load_from_repository()

        # Build UI
        self.create_header_ui()
        self.create_summary_ui()
        self.create_category_table_ui()
        self.create_action_buttons_ui()

        # Render view
        self.refresh_ui()

    def get_or_create_budget(self, year, month):
        key = (year, month)
        if key not in self.budgets:
            self.budgets[key] = Budget(month=month, year=year, categories=[])
        return self.budgets[key]

    def create_header_ui(self):
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        self.title_label = ttk.Label(
            header_frame,
            text=f"Budget Overview — {self.current_month}/{self.current_year}",
            font=("Helvetica", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT)

    def create_summary_ui(self):
        summary_frame = ttk.LabelFrame(self.root, text=" Monthly Totals ", padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(summary_frame, text="Total Income:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=10)
        self.income_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10))
        self.income_val_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_frame, text="Total Allocated:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky=tk.W, padx=10)
        self.allocated_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10))
        self.allocated_val_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_frame, text="Left to Budget:", font=("Helvetica", 10, "bold")).grid(row=0, column=4, sticky=tk.W, padx=10)
        self.unallocated_val_label = ttk.Label(summary_frame, text="$0.00", font=("Helvetica", 10, "bold"))
        self.unallocated_val_label.grid(row=0, column=5, sticky=tk.W)

    def create_category_table_ui(self):
        table_frame = ttk.LabelFrame(self.root, text=" Category Envelopes ", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("type", "name", "planned", "actual", "remaining")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("type", text="Type")
        self.tree.heading("name", text="Category Name")
        self.tree.heading("planned", text="Planned")
        self.tree.heading("actual", text="Actual (Spent/Received)")
        self.tree.heading("remaining", text="Remaining / Pending")

        self.tree.column("type", width=80, anchor=tk.CENTER)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("planned", width=110, anchor=tk.E)
        self.tree.column("actual", width=150, anchor=tk.E)
        self.tree.column("remaining", width=150, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda event: self.open_edit_category_dialog())

    def create_action_buttons_ui(self):
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)

        btn_add_cat = ttk.Button(
            action_frame,
            text="Add Category",
            command=self.open_add_category_dialog
        )
        btn_add_cat.pack(side=tk.LEFT, padx=8)

        btn_edit_cat = ttk.Button(
            action_frame,
            text="Edit Selected",
            command=self.open_edit_category_dialog
        )
        btn_edit_cat.pack(side=tk.LEFT, padx=5)

        btn_delete_cat = ttk.Button(
            action_frame,
            text = "Delete Selected",
            command = self.delete_selected_category
        )
        btn_delete_cat.pack(side=tk.LEFT, padx=5)

        btn_log_tx = ttk.Button(
            action_frame,
            text="Log Transaction",
            command=self.open_log_transaction_dialog
        )
        btn_log_tx.pack(side=tk.LEFT, padx=5)

        btn_rollover = ttk.Button(action_frame, text="Close Month & Roll Over", command=self.placeholder_action)
        btn_rollover.pack(side=tk.LEFT, padx=5)

    def open_add_category_dialog(self):
        """Opens dialog to create a brand new category envelope."""
        AddCategoryDialog(
            self.root,
            self.current_budget,
            self.refresh_ui,
            existing_category=None,
            repository=self.repository
        )

    def open_edit_category_dialog(self):
        """Opens dialog to edit an existing selected category envelope."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a category from the table first.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        cat_name = item_values[1]
        selected_cat = self.current_budget.get_category_by_name(cat_name)

        if selected_cat:
            AddCategoryDialog(
                self.root,
                self.current_budget,
                self.refresh_ui,
                existing_category=selected_cat,
                repository=self.repository  # <-- Added repository here
            )

    def delete_selected_category(self):
        """Deletes the selected category envelope after user confirmation."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a category from the table first.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        cat_name = item_values[1]

        # Confirmation popup before deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the envelope '{cat_name}'?",
            parent=self.root
        )

        if confirm:
            # 1. Remove from database
            if self.repository:
                self.repository.delete_category_by_name(cat_name)

            # 2. Remove from in-memory budget
            cat_to_remove = self.current_budget.get_category_by_name(cat_name)
            if cat_to_remove and cat_to_remove in self.current_budget.categories:
                self.current_budget.categories.remove(cat_to_remove)

            # 3. Refresh display
            self.refresh_ui()

    def open_log_transaction_dialog(self):
        if not self.current_budget.categories:
            messagebox.showwarning("No Categories", "Please add at least one category envelope before logging a transaction.")
            return
        LogTransactionDialog(
            self.root, 
            self.current_budget, 
            self.refresh_ui,
            repository = self.repository
        )

    def placeholder_action(self):
        messagebox.showinfo("In Progress", "This button will trigger in our next step!")

    def refresh_ui(self):
        self.title_label.config(text=f"Budget Overview — {self.current_month}/{self.current_year}")

        rollover_cash = self.rollovers.get((self.current_year, self.current_month), 0.0)
        total_income = self.current_budget.get_total_income() + rollover_cash
        total_allocated = self.current_budget.get_total_allocated()
        unallocated = total_income - total_allocated

        self.income_val_label.config(text=f"${total_income:,.2f}")
        self.allocated_val_label.config(text=f"${total_allocated:,.2f}")

        if unallocated < 0:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", foreground="red")
        else:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", foreground="black")

        for item in self.tree.get_children():
            self.tree.delete(item)

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

    def load_from_repository(self):
        """Retrieves stored categories and transactions from SQLite and populates the in-memory budget."""
        if not self.repository:
            return

        db_categories = self.repository.get_all_categories()
        for db_cat in db_categories:
            self.current_budget.add_or_update_category(
                name = db_cat.name,
                category_type = db_cat.category_type,
                planned_amount = float(db_cat.allocated_amount)
            )

        db_transactions = self.repository.get_all_transactions()
        for db_tx in db_transactions:
            if db_tx.category:
                domain_cat = self.current_budget.get_category_by_name(db_tx.category.name)
                if domain_cat:
                    tx_date = db_tx.trans_date.strftime("%Y-%m-%d") if db_tx.trans_date else None
                    tx = Transaction(
                        amount = float(db_tx.amount),
                        description = db_tx.note or "",
                        date = tx_date
                    )
                    domain_cat.add_transaction(tx)

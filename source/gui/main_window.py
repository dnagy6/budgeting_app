import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Domain & Services
from source.domain.budget import Budget
from source.domain.category import Category
from source.gui.dialogs.category_dialog import AddCategoryDialog
from source.gui.dialogs.category_group_dialog import AddCategoryGroupDialog
from source.gui.dialogs.transaction_dialog import LogTransactionDialog
from source.persistence.repository import BudgetRepository
from source.services.budget_service import BudgetService
from source.services.rollover_service import RolloverService

# Widgets
from source.gui.widgets.category_group_card import CategoryGroupCard
from source.gui.widgets.month_picker import MonthPickerPopup
from source.gui.widgets.nav_sidebar import NavSidebar
from source.gui.widgets.transaction_panel import TransactionPanel


class BudgetApp:
    def __init__(self, root: tk.Tk, service: BudgetService):
        self.root = root
        self.service = service
        self.rollover_service = RolloverService(self.service)

        self.root.title("Zero-Based Budgeting App")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 600)

        # Storage & State
        self.budgets = {}
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month

        # Active budget loading
        if self.service:
            self.current_budget = self.service.load_budget(self.current_year, self.current_month)
        else:
            self.current_budget = Budget(month=self.current_month, year=self.current_year)

        # Build 3-Column Layout Frames
        self._build_layout_columns()

        # Build UI Components
        self.create_header_ui()
        self.create_summary_ui()
        self.create_scrollable_groups_canvas()
        self.create_footer_actions_ui()
        self.create_right_rail_ui()

        # Render view
        self.refresh_ui()

    def _build_layout_columns(self):
        # Column 1: Left Navigation Rail
        self.nav_sidebar = NavSidebar(
            self.root,
            on_tab_change=self.on_nav_tab_changed,
            on_profile_click=self.on_profile_clicked
        )
        self.nav_sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Column 2: Center Budget Canvas (Expandable)
        self.center_frame = tk.Frame(self.root, bg="#f8fafc")
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Column 3: Right Transaction Rail (Fixed width 350px)
        self.right_frame = tk.Frame(
            self.root,
            bg="#ffffff",
            width=350,
            highlightthickness=1,
            highlightbackground="#e2e8f0"
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)

    def create_header_ui(self):
        header_frame = tk.Frame(self.center_frame, bg="#f8fafc", padx=20, pady=16)
        header_frame.pack(fill=tk.X)

        month_name = calendar.month_name[self.current_month]
        self.btn_month_selector = tk.Button(
            header_frame,
            text=f"{month_name} {self.current_year} ▾",
            font=("Helvetica", 22, "bold"),
            relief=tk.FLAT,
            bd=0,
            bg="#f8fafc",
            activebackground="#f1f5f9",
            cursor="hand2",
            command=self.open_month_picker
        )
        self.btn_month_selector.pack(side=tk.LEFT)

        self.btn_reset_budget = ttk.Button(
            header_frame,
            text="Reset Budget ▾",
            command=self.show_reset_budget_options
        )
        self.btn_reset_budget.pack(side=tk.RIGHT, padx=6)

    def create_summary_ui(self):
        summary_card = tk.Frame(self.center_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0", padx=16, pady=14)
        summary_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Income Total
        col1 = tk.Frame(summary_card, bg="#ffffff")
        col1.pack(side=tk.LEFT, expand=True)
        tk.Label(col1, text="TOTAL INCOME", font=("Helvetica", 9, "bold"), fg="#64748b", bg="#ffffff").pack(anchor="w")
        self.income_val_label = tk.Label(col1, text="$0.00", font=("Helvetica", 14, "bold"), fg="#0f172a", bg="#ffffff")
        self.income_val_label.pack(anchor="w")

        # Allocated Total
        col2 = tk.Frame(summary_card, bg="#ffffff")
        col2.pack(side=tk.LEFT, expand=True)
        tk.Label(col2, text="TOTAL ALLOCATED", font=("Helvetica", 9, "bold"), fg="#64748b", bg="#ffffff").pack(anchor="w")
        self.allocated_val_label = tk.Label(col2, text="$0.00", font=("Helvetica", 14, "bold"), fg="#0f172a", bg="#ffffff")
        self.allocated_val_label.pack(anchor="w")

        # Left to Budget
        col3 = tk.Frame(summary_card, bg="#ffffff")
        col3.pack(side=tk.LEFT, expand=True)
        tk.Label(col3, text="LEFT TO BUDGET", font=("Helvetica", 9, "bold"), fg="#64748b", bg="#ffffff").pack(anchor="w")
        self.unallocated_val_label = tk.Label(col3, text="$0.00", font=("Helvetica", 14, "bold"), fg="#16a34a", bg="#ffffff")
        self.unallocated_val_label.pack(anchor="w")

    def create_scrollable_groups_canvas(self):
        """Creates a scrollable canvas container for CategoryGroupCards."""
        container = tk.Frame(self.center_frame, bg="#f8fafc")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(container, bg="#f8fafc", bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.groups_inner_frame = tk.Frame(self.canvas, bg="#f8fafc")

        self.groups_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_footer_actions_ui(self):
        footer_frame = tk.Frame(self.center_frame, bg="#f8fafc", padx=20, pady=10)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_add_group = ttk.Button(
            footer_frame,
            text="+ Add Category Group",
            command=self.open_add_group_dialog
        )
        btn_add_group.pack(side=tk.LEFT, padx=(0, 6))

        btn_log_tx = ttk.Button(
            footer_frame,
            text="Log Transaction",
            command=self.open_log_transaction_dialog
        )
        btn_log_tx.pack(side=tk.LEFT, padx=6)

        btn_rollover = ttk.Button(
            footer_frame,
            text="Close Month & Roll Over",
            command=self.close_month_and_rollover
        )
        btn_rollover.pack(side=tk.RIGHT)

    def create_right_rail_ui(self):
        """Mounts the full interactive TransactionPanel in the right rail."""
        self.transaction_panel = TransactionPanel(
            self.right_frame,
            service=self.service,
            on_data_changed=self.reload_and_refresh
        )
        self.transaction_panel.pack(fill=tk.BOTH, expand=True)

    def open_add_group_dialog(self):
        AddCategoryGroupDialog(
            self.root,
            on_success_callback=self.reload_and_refresh,
            service=self.service
        )

    def open_add_category_to_group(self, group_name: str, group_type: str):
        AddCategoryDialog(
            self.root,
            self.current_budget,
            on_success_callback=self.reload_and_refresh,
            default_group=group_name,
            default_type=group_type,
            service=self.service
        )

    def open_edit_category(self, category: Category):
        AddCategoryDialog(
            self.root,
            self.current_budget,
            on_success_callback=self.reload_and_refresh,
            existing_category=category,
            service=self.service
        )

    def handle_inline_category_edit(self, old_name: str, new_name: str, new_amount: float):
        """Updates category name or planned amount directly from inline clicks."""
        # Find which group this envelope belongs to
        target_cat = self.current_budget.get_category_by_name(old_name)
        group_name = None
        if target_cat:
            for grp in self.current_budget.groups:
                if target_cat in grp.categories:
                    group_name = grp.name
                    break

        self.service.save_category(
            budget=self.current_budget,
            name=new_name,
            category_type=target_cat.category_type if target_cat else "expense",
            planned_amount=new_amount,
            group_name=group_name,
            old_name=old_name if new_name != old_name else None
        )
        self.reload_and_refresh()

    def handle_group_reorder_complete(self, ordered_names: list[str]):
        """Persists the explicit visual order to SQLite and refreshes."""
        self.service.reorder_category_groups(ordered_names)
        self.reload_and_refresh()

    def delete_category_envelope(self, cat_name: str):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{cat_name}' from this month?", parent=self.root):
            self.service.delete_category(self.current_budget, cat_name)
            self.reload_and_refresh()

    def delete_category_group(self, group_name: str):
        if messagebox.askyesno(
            "Delete Category Group",
            f"Are you sure you want to delete the group '{group_name}'?\n\n"
            "Child envelopes will remain in the database but become unassigned.",
            parent=self.root
        ):
            self.service.delete_category_group(group_name)
            self.reload_and_refresh()

    def handle_move_category_group(self, group_name: str, direction: str):
        """Moves a category group up or down in sort order and re-renders."""
        moved = self.service.move_category_group(group_name, direction)
        if moved:
            self.reload_and_refresh()

    def open_log_transaction_dialog(self):
        if not self.current_budget.categories:
            messagebox.showwarning("No Categories", "Please add at least one category envelope before logging a transaction.")
            return
        LogTransactionDialog(
            self.root,
            self.current_budget,
            self.reload_and_refresh,
            service=self.service
        )

    def reload_and_refresh(self):
        self.current_budget = self.service.load_budget(self.current_year, self.current_month)
        self.refresh_ui()

    def close_month_and_rollover(self):
        surplus = self.rollover_service.calculate_month_surplus(self.current_budget)
        confirm = messagebox.askyesno(
            "Close Month & Roll Over",
            f"End budget for {self.current_month}/{self.current_year}?\n\n"
            f"Leftover pool: ${surplus:,.2f}\n"
            "This will advance to next month.",
            parent=self.root
        )
        if confirm:
            self.current_budget = self.rollover_service.close_and_rollover_month(self.current_budget)
            self.current_year = self.current_budget.year
            self.current_month = self.current_budget.month
            self.refresh_ui()

    def open_month_picker(self):
        MonthPickerPopup(
            parent_button=self.btn_month_selector,
            initial_year=self.current_year,
            initial_month=self.current_month,
            on_select_callback=self.change_budget_month
        )

    def change_budget_month(self, year: int, month: int):
        month_name = calendar.month_name[month]

        if not self.service.has_budget_for_month(year, month):
            prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
            has_prev = self.service.has_budget_for_month(prev_year, prev_month)

            if has_prev:
                choice = messagebox.askyesnocancel(
                    f"Start Planning for {month_name} {year}",
                    f"No budget found for {month_name} {year}.\n\n"
                    f"• Yes: Copy categories & amounts from previous month\n"
                    f"• No: Start fresh with $0.00 planned\n"
                    f"• Cancel: Return to current view",
                    parent=self.root
                )
                if choice is None:
                    return
                elif choice is True:
                    self.service.copy_previous_month_budget(year, month)
                else:
                    self.service.initialize_fresh_month(year, month)
            else:
                start = messagebox.askyesno(
                    f"Start Planning for {month_name} {year}",
                    f"Start planning for {month_name} {year}?",
                    parent=self.root
                )
                if not start:
                    return
                self.service.initialize_fresh_month(year, month)

        self.current_year = year
        self.current_month = month
        self.reload_and_refresh()

    def show_reset_budget_options(self):
        month_name = calendar.month_name[self.current_month]
        choice = messagebox.askyesnocancel(
            f"Reset {month_name} {self.current_year} Budget",
            f"Choose a reset option:\n\n"
            f"• Yes: Set all planned amounts to $0.00\n"
            f"• No: Overwrite with last month's planned amounts\n"
            f"• Cancel: Keep current budget as-is",
            parent=self.root
        )
        if choice is True:
            self.service.zero_out_month(self.current_year, self.current_month)
            self.reload_and_refresh()
        elif choice is False:
            copied = self.service.copy_previous_month_budget(self.current_year, self.current_month)
            if copied:
                self.reload_and_refresh()
            else:
                messagebox.showinfo("No Previous Budget", "No previous budget found to copy from.")

    def on_nav_tab_changed(self, tab_id: str):
        pass

    def on_profile_clicked(self):
        pass

    def refresh_ui(self):
        month_name = calendar.month_name[self.current_month]
        self.btn_month_selector.config(text=f"{month_name} {self.current_year} ▾")

        total_income = self.current_budget.get_total_income()
        total_allocated = self.current_budget.get_total_allocated()
        unallocated = self.current_budget.get_remaining_to_budget()

        self.income_val_label.config(text=f"${total_income:,.2f}")
        self.allocated_val_label.config(text=f"${total_allocated:,.2f}")

        if unallocated < 0:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", fg="#dc2626")
        else:
            self.unallocated_val_label.config(text=f"${unallocated:,.2f}", fg="#16a34a")

        # Synchronize Transaction Panel period and items
        if hasattr(self, "transaction_panel"):
            self.transaction_panel.set_period(self.current_year, self.current_month)

        # 1. Capture current expansion states before destroying cards
        card_states = {
            card.group.name: card.is_expanded
            for card in self.groups_inner_frame.winfo_children()
            if isinstance(card, CategoryGroupCard)
        }

        # 2. Clear existing group cards
        for child in self.groups_inner_frame.winfo_children():
            child.destroy()

        if not self.current_budget.groups:
            lbl_empty = tk.Label(
                self.groups_inner_frame,
                text="No category groups created yet.\nClick '+ Add Category Group' below to start organizing your budget.",
                font=("Helvetica", 11),
                fg="#94a3b8",
                bg="#f8fafc",
                pady=40
            )
            lbl_empty.pack(fill=tk.BOTH, expand=True)
            return

        # 3. Render cards with their preserved state
        for grp in self.current_budget.groups:
            was_expanded = card_states.get(grp.name, True)
            card = CategoryGroupCard(
                self.groups_inner_frame,
                group=grp,
                on_add_category=self.open_add_category_to_group,
                on_inline_edit=self.handle_inline_category_edit,
                on_delete_category=self.delete_category_envelope,
                on_delete_group=self.delete_category_group,
                on_reorder_complete=self.handle_group_reorder_complete,
                initial_expanded=was_expanded
            )
            card.pack(fill=tk.X, pady=(0, 12))
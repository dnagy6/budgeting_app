import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Domain & Services
from source.settings import Theme, AppConfig
from source.domain.budget import Budget
from source.domain.category import Category
from source.gui.dialogs.transaction_dialog import LogTransactionDialog
from source.persistence.repository import BudgetRepository
from source.services.budget_service import BudgetService
from source.services.rollover_service import RolloverService

# Widgets
from source.gui.widgets.header_view import HeaderView
from source.gui.widgets.summary_card import SummaryCard
from source.gui.widgets.footer_actions import FooterActions
from source.gui.widgets.expense_card import ExpenseCard
from source.gui.widgets.category_group_card import CategoryGroupCard
from source.gui.widgets.month_picker import MonthPickerPopup
from source.gui.widgets.nav_sidebar import NavSidebar
from source.gui.widgets.transaction_panel import TransactionPanel


class BudgetApp:
    def __init__(self, root: tk.Tk, service: BudgetService):
        self.root = root
        self.service = service
        self.rollover_service = RolloverService(self.service)

        self.root.title(AppConfig.APP_TITLE)
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)

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
        self.header_view = HeaderView(
            self.center_frame,
            current_month=self.current_month,
            current_year=self.current_year,
            on_month_click=self.open_month_picker,
            on_reset_click=self.show_reset_budget_options
        )
        self.header_view.pack(fill=tk.X)

        self.summary_card = SummaryCard(self.center_frame)
        self.summary_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.expense_card = ExpenseCard(self.center_frame)
        self.expense_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.footer_actions = FooterActions(
            self.center_frame,
            on_add_group=self.open_add_group_dialog,
            on_log_transaction=self.open_log_transaction_dialog,
            on_rollover=self.close_month_and_rollover
        )
        self.footer_actions.pack(fill=tk.X, side=tk.BOTTOM)
        self.create_right_rail_ui()

        # Render view
        self.refresh_ui()

    def _build_layout_columns(self):
        # Column 1: Left Navigation Rail (NavSidebar handles its own styling)
        self.nav_sidebar = NavSidebar(
            self.root,
            on_tab_change=self.on_nav_tab_changed,
            on_profile_click=self.on_profile_clicked
        )
        self.nav_sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Column 2: Center Budget Canvas (Expandable)
        self.center_frame = tk.Frame(self.root, bg=Theme.BG_CARD)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Column 3: Right Transaction Rail (Fixed width 350px)
        self.right_frame = tk.Frame(
            self.root,
            bg=Theme.BG_CARD,
            width=350,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)

    def create_right_rail_ui(self):
        """Mounts the full interactive TransactionPanel in the right rail."""
        self.transaction_panel = TransactionPanel(
            self.right_frame,
            service=self.service,
            on_data_changed=self.reload_and_refresh
        )
        self.transaction_panel.pack(fill=tk.BOTH, expand=True)

    def open_add_group_dialog(self):
        """Creates a blank inline category group directly in the active budget view."""
        # Check if an 'Untitled Group' already exists to avoid duplicate placeholders
        default_name = "New Group"
        counter = 1
        existing_names = {g.name for g in self.current_budget.groups}
        while default_name in existing_names:
            default_name = f"New Group {counter}"
            counter += 1

        # Save it immediately with a unique placeholder name tied to this specific group
        self.service.save_category(
            budget=self.current_budget,
            name=f"{default_name} Envelope",  # <--- Unique name prevents collision/theft
            category_type="expense",
            planned_amount=0.0,
            group_name=default_name
        )
        
        # Reload and refresh so the new inline card appears on canvas ready for editing
        self.reload_and_refresh()

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

    def handle_inline_group_rename(self, old_name: str, new_name: str):
        """Renames or reactivates a category group in the repository and reloads."""
        self.service.repository.update_category_group_name(
            old_name,
            new_name,
            year=self.current_year,
            month=self.current_month
        )
        self.reload_and_refresh()

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

    def handle_inline_category_save(self, group_name: str, category_name: str, planned_amount: float, category_type: str):
        """Saves a new category created via the inline card input row directly to SQLite."""
        self.service.save_category(
            budget=self.current_budget,
            name=category_name,
            planned_amount=planned_amount,
            group_name=group_name,
            category_type=category_type
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
            f"Are you sure you want to delete the group '{group_name}' for {calendar.month_name[self.current_month]} {self.current_year}?\n\n"
            "This will remove its envelopes for this month without affecting other months.",
            parent=self.root
        ):
            self.service.delete_category_group(self.current_budget, group_name)
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
            parent_button=self.header_view.btn_month_selector,
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
        self.header_view.update_header(self.current_month, self.current_year)

        # 1. Calculate Income Received and Left to Budget (keeping your math intact)
        total_income_received = sum(
            cat.get_actual_amount()
            for grp in self.current_budget.groups
            if grp.group_type == "income"
            for cat in grp.categories
        )

        total_allocated_expenses = sum(
            cat.planned_amount
            for grp in self.current_budget.groups
            if grp.group_type != "income"
            for cat in grp.categories
        )

        unallocated = total_income_received - total_allocated_expenses

        self.summary_card.update_values(total_income_received, unallocated)

        if hasattr(self, "transaction_panel"):
            self.transaction_panel.set_period(self.current_year, self.current_month)

        # Render budget groups using the modular expense card container
        self.expense_card.render_groups(
            groups=self.current_budget.groups,
            callbacks={
                "on_inline_save_category": self.handle_inline_category_save,
                "on_add_category": self.open_add_category_to_group,
                "on_inline_edit": self.handle_inline_category_edit,
                "on_delete_category": self.delete_category_envelope,
                "on_delete_group": self.delete_category_group,
                "on_reorder_complete": self.handle_group_reorder_complete,
                "on_rename_group": self.handle_inline_group_rename,
            }
        )
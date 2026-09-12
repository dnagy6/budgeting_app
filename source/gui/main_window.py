import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Domain & Services
from source.settings import Theme, AppConfig
from source.domain.budget import Budget
from source.domain.category import Category
from source.gui.dialogs.transaction_dialog import LogTransactionDialog
from source.persistence.repositories import BudgetRepository
from source.services.budget_service import BudgetService
from source.services.rollover_service import RolloverService

# Widgets
from source.gui.widgets.header_view import HeaderView
from source.gui.widgets.summary_card import SummaryCard
from source.gui.views.budget_view import ExpenseCard
from source.gui.widgets.category_group_card import CategoryGroupCard
from source.gui.widgets.month_picker import MonthPickerPopup
from source.gui.widgets.nav_sidebar import NavSidebar
from source.gui.widgets.transactions_minimap import TransactionsMinimap

# Tabs/ views
from source.gui.views.transactions_view import TransactionPanel
from source.gui.views.accounts_view import AccountsView


class BudgetApp:
    def __init__(self, root: tk.Tk, service: BudgetService):
        self.root = root
        self.service = service
        self.rollover_service = RolloverService(self.service)

        self.root.title(AppConfig.APP_TITLE)
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)

        self._subscribers = {"DATA_UPDATED": []}

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

        self.subscribe("DATA_UPDATED", self.reload_and_refresh)

        # Build 3-Column Layout Frames
        self._build_layout_columns()

        # Build UI Components
        self.header_view = HeaderView(
            self.budget_header_frame,
            current_month=self.current_month,
            current_year=self.current_year,
            on_month_click=self.open_month_picker,
            on_prev_month=self.prev_month,
            on_next_month=self.next_month,
            on_today_click=self.go_to_today,
            on_log_transaction=self.open_log_transaction_dialog,
            on_reset_click=self.show_reset_budget_options
        )
        self.header_view.pack(fill=tk.X)

        self.summary_card = SummaryCard(self.right_frame)
        self.summary_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        self.expense_card = ExpenseCard(self.center_frame)
        self.expense_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        

        # Render view
        self.refresh_ui()

    def subscribe(self, event_name: str, callback):
        """Registers a UI component's refresh function to listen for a specific event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def broadcast(self, event_name: str, *args, **kwargs):
        """Silently triggers all listening functions when data changes."""
        for callback in self._subscribers.get(event_name, []):
            callback(*args, **kwargs)
    
    def _build_layout_columns(self):
        # Column 1: Left Navigation Rail
        self.nav_sidebar = NavSidebar(
            self.root,
            on_tab_change=self.on_nav_tab_changed,
            on_profile_click=self.on_profile_clicked
        )
        self.nav_sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Dynamic Content Area (Holds all tabs)
        self.main_content_area = tk.Frame(self.root, bg=Theme.BG_CARD)
        self.main_content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- TAB 1: Budget Container ---
        self.budget_view_frame = tk.Frame(self.main_content_area, bg=Theme.BG_CARD)

        self.budget_header_frame = tk.Frame(self.budget_view_frame, bg=Theme.BG_CARD)
        self.budget_header_frame.pack(side=tk.TOP, fill=tk.X)

        self.budget_body_frame = tk.Frame(self.budget_view_frame, bg=Theme.BG_CARD)
        self.budget_body_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Center Column: Budget 
        self.center_frame = tk.Frame(self.budget_body_frame, bg=Theme.BG_CARD)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Column: SUMMARY CARD
        self.right_frame = tk.Frame(
            self.budget_body_frame,
            bg=Theme.BG_CARD,
            width=350,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 20), pady=(0, 20))
        self.right_frame.pack_propagate(False)

        # --- TAB 2: Transactions Container ---
        self.transactions_view_frame = tk.Frame(self.main_content_area, bg=Theme.BG_CARD)
        
        self.transaction_panel = TransactionPanel(
            self.transactions_view_frame,
            service=self.service,
            on_data_changed=lambda: self.broadcast("DATA_UPDATED")
        )
        self.transaction_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.minimap = TransactionsMinimap(self.transactions_view_frame)
        self.minimap.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=(0, 20))

        # --- TAB 3: Accounts Container ---
        self.accounts_view = AccountsView(
            self.main_content_area,
            on_accounts_updated=lambda: self.broadcast("DATA_UPDATED")
        )

        # Default TAB
        self.active_tab = "budget"
        self.budget_view_frame.pack(fill=tk.BOTH, expand=True)

    def open_add_group_dialog(self):
        """Creates a blank inline category group directly in the active budget view."""
        default_name = "New Group"
        counter = 1
        existing_names = {g.name for g in self.current_budget.groups}
        while default_name in existing_names:
            default_name = f"New Group {counter}"
            counter += 1

        self.service.save_category(
            budget=self.current_budget,
            name=f"{default_name} Envelope",
            category_type="expense",
            planned_amount=0.0,
            group_name=default_name
        )
        
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
        if hasattr(self, "accounts_view") and self.active_tab == "accounts":
            self.accounts_view.refresh()
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

    def prev_month(self):
        m = self.current_month - 1
        y = self.current_year
        if m < 1:
            m = 12
            y -= 1
        self.change_budget_month(y, m)

    def next_month(self):
        m = self.current_month + 1
        y = self.current_year
        if m > 12:
            m = 1
            y += 1
        self.change_budget_month(y, m)

    def go_to_today(self):
        now = datetime.now()
        if self.current_year != now.year or self.current_month != now.month:
            self.change_budget_month(now.year, now.month)

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
        normalized_tab = tab_id.lower()
        if normalized_tab == self.active_tab:
            return
        
        self.budget_view_frame.pack_forget()
        self.transactions_view_frame.pack_forget()
        if hasattr(self, "accounts_view"):
            self.accounts_view.pack_forget()

        if normalized_tab == "budget":
            self.budget_view_frame.pack(fill=tk.BOTH, expand=True)
        elif normalized_tab == "transactions":
            self.transactions_view_frame.pack(fill=tk.BOTH, expand=True)
            self.transaction_panel.refresh()
        elif normalized_tab == "accounts":
            self.accounts_view.pack(fill=tk.BOTH, expand=True)
            self.accounts_view.refresh()
        
        self.active_tab = normalized_tab

    def on_profile_clicked(self):
        pass

    def refresh_ui(self):
        self.header_view.update_header(self.current_month, self.current_year)

        # 1. Planned Totals for Zero-Based Allocation ("Left to Budget")
        total_planned_income = sum(
            cat.planned_amount
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

        unallocated = total_planned_income - total_allocated_expenses

        # 2. Actual Cash Flow Telemetry ("Income Received")
        total_income_received = sum(
            cat.get_actual_amount()
            for grp in self.current_budget.groups
            if grp.group_type == "income"
            for cat in grp.categories
        )

        # Update the SummaryCard telemetry
        self.summary_card.update_values(
            income=total_income_received,
            unallocated=unallocated,
            groups=self.current_budget.groups
        )

        if hasattr(self, "transaction_panel"):
            self.transaction_panel.set_period(self.current_year, self.current_month)

        # Render budget groups using the modular expense card container
        self.expense_card.render_groups(
            groups=self.current_budget.groups,
            callbacks={
                "on_add_group": self.open_add_group_dialog,
                "on_inline_save_category": self.handle_inline_category_save,
                "on_add_category": self.open_add_category_to_group,
                "on_inline_edit": self.handle_inline_category_edit,
                "on_delete_category": self.delete_category_envelope,
                "on_delete_group": self.delete_category_group,
                "on_reorder_complete": self.handle_group_reorder_complete,
                "on_rename_group": self.handle_inline_group_rename,
            }
        )
        # Transaction Minimap stays in sync with budget changes
        if hasattr(self, "minimap"):
            self.minimap.refresh_data(
                budget_groups=self.current_budget.groups, 
                unallocated=unallocated
            )
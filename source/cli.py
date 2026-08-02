from models import Budget, Category, Transaction


def print_header(title):
    print("\n" + "=" * 50)
    print(f" {title.upper()}")
    print("=" * 50)


def get_or_create_budget(budgets, year, month):
    key = (year, month)
    if key not in budgets:
        budgets[key] = Budget(month=month, year=year, categories=[])
    return budgets[key]


def display_budget_summary(budget, rollover_funds=0.0):
    print_header(f"Budget Overview ({budget.month}/{budget.year})")
    
    new_income = budget.get_total_income()
    total_available = new_income + rollover_funds
    total_allocated = budget.get_total_allocated()
    remaining_unallocated = total_available - total_allocated

    print(f" Rollover from Prev Month: ${rollover_funds:,.2f}")
    print(f" New Income (This Month):  ${new_income:,.2f}")
    print(f" -------------------------------------------")
    print(f" Total Available Funds:    ${total_available:,.2f}")
    print(f" Total Envelope Allocations: ${total_allocated:,.2f}")
    print(f" Left to Budget (Unallocated): ${remaining_unallocated:,.2f}")
    print("-" * 50)

    if not budget.categories:
        print(" No category envelopes created for this month yet.")
        return

    print(" ENVELOPES / CATEGORIES:")
    for cat in budget.categories:
        actual = cat.get_actual_amount()
        rem = cat.get_remaining_amount()
        cat_type = cat.category_type.capitalize()

        if cat.category_type == "income":
            actual_label = "Received"
            rem_label = "Pending"
        else:
            actual_label = "Spent"
            rem_label = "Remaining"
        
        print(f"  • [{cat_type}] {cat.name}:")
        print(f"      Planned: ${cat.planned_amount:,.2f} | {actual_label}: ${actual:,.2f} | {rem_label}: ${rem:,.2f}")


def run_cli():
    # In-memory dictionary storing budgets keyed by (year, month)
    budgets = {}
    
    # Start in August 2026
    current_year = 2026
    current_month = 8
    
    # Track rollover cash passed into each month: (year, month) -> amount
    rollovers = {}

    while True:
        current_budget = get_or_create_budget(budgets, current_year, current_month)
        current_rollover = rollovers.get((current_year, current_month), 0.0)

        print_header(f"Zero-Based Budgeting App — Active: {current_month}/{current_year}")
        print(" 1. View Current Month Summary")
        print(" 2. Add Category Envelope")
        print(" 3. Log Expense / Income Transaction")
        print(" 4. Close Month & Roll Over Unspent Cash to Next Month")
        print(" 5. Switch Active Month / Year")
        print(" 6. Exit")
        print("-" * 50)

        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            display_budget_summary(current_budget, current_rollover)

        elif choice == "2":
            print_header("Add Category Envelope")
            name = input("Category Name (e.g., Groceries, Rent, Emergency Fund): ").strip()
            if not name:
                print("⚠️ Name cannot be empty.")
                continue

            print("Type: [1] Expense  [2] Income")
            type_choice = input("Select Type (1 or 2): ").strip()
            cat_type = "income" if type_choice == "2" else "expense"

            try:
                planned = float(input("Planned Amount ($): ").strip())
            except ValueError:
                print("⚠️ Invalid number format.")
                continue

            new_cat = Category(name=name, category_type=cat_type, planned_amount=planned)
            current_budget.categories.append(new_cat)
            print(f"✅ Added '{name}' envelope to {current_month}/{current_year}!")

        elif choice == "3":
            print_header("Log Transaction")
            if not current_budget.categories:
                print("⚠️ Please add at least one category envelope first!")
                continue

            print("Select Category:")
            for idx, cat in enumerate(current_budget.categories, start=1):
                print(f"  {idx}. {cat.name} ({cat.category_type})")

            try:
                cat_idx = int(input("Category Number: ").strip()) - 1
                selected_cat = current_budget.categories[cat_idx]
                amount = float(input("Transaction Amount ($): ").strip())
            except (ValueError, IndexError):
                print("⚠️ Invalid selection or amount.")
                continue

            note = input("Note/Description (optional): ").strip()
            tx = Transaction(amount=amount, note=note)
            selected_cat.transactions.append(tx)
            print(f"✅ Logged ${amount:,.2f} under '{selected_cat.name}'!")

        elif choice == "4":
            print_header("Close Month & Roll Over")
            
            # Calculate total actual income vs total actual expenses spent
            total_income_actual = 0.0
            total_expense_actual = 0.0

            for cat in current_budget.categories:
                if cat.category_type == "income":
                    total_income_actual += cat.get_actual_amount()
                else:
                    total_expense_actual += cat.get_actual_amount()

            # Total unspent cash from current month
            unspent_cash = total_income_actual - total_expense_actual

            if unspent_cash <= 0:
                print(f"ℹ️ No surplus cash to roll over (Unspent cash: ${unspent_cash:,.2f}).")
                continue

            print(f"💵 Unspent cash remaining from {current_month}/{current_year}: ${unspent_cash:,.2f}")
            target_envelope = input("Enter target envelope name in NEXT month to receive rollover (e.g., Savings): ").strip()

            # Determine next month and year
            next_month = 1 if current_month == 12 else current_month + 1
            next_year = current_year + 1 if current_month == 12 else current_year

            # Apply to next month's budget
            next_budget = get_or_create_budget(budgets, next_year, next_month)
            next_budget.apply_rollover(unspent_cash, target_envelope)
            
            # Record rollover cash tracker for summary display
            rollovers[(next_year, next_month)] = rollovers.get((next_year, next_month), 0.0) + unspent_cash

            print(f"✅ Successfully rolled over ${unspent_cash:,.2f} into '{target_envelope}' for {next_month}/{next_year}!")
            
            # Auto-switch to next month
            current_month = next_month
            current_year = next_year
            print(f"👉 Switched active view to {current_month}/{current_year}.")

        elif choice == "5":
            print_header("Switch Active Month / Year")
            try:
                m = int(input("Enter Month (1-12): ").strip())
                y = int(input("Enter Year (e.g., 2026): ").strip())
                if 1 <= m <= 12:
                    current_month = m
                    current_year = y
                    print(f"✅ Switched to {current_month}/{current_year}")
                else:
                    print("⚠️ Invalid month.")
            except ValueError:
                print("⚠️ Invalid input format.")

        elif choice == "6":
            print("\nThanks for using Zero-Based Budgeter! Goodbye.\n")
            break

        else:
            print("⚠️ Invalid choice. Select 1-6.")


if __name__ == "__main__":
    run_cli()
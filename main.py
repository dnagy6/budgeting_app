import tkinter as tk
from source.gui.main_window import BudgetApp
from source.persistence.database import init_db
from source.persistence.repository import BudgetRepository


def main():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":

    init_db()
    repo = BudgetRepository()

    main()
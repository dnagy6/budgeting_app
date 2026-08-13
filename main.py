import tkinter as tk
import sys

from source.gui.main_window import BudgetApp
from source.persistence.database import init_db
from source.persistence.repository import BudgetRepository


def main(repo: BudgetRepository):

    
    root = tk.Tk()
    app = BudgetApp(root, repository = repo)
    root.mainloop()


if __name__ == "__main__":

    init_db()
    repo = BudgetRepository()

    main(repo)
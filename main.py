import tkinter as tk
import sys

from source.gui.main_window import BudgetApp
from source.persistence.database import init_db
from source.persistence.repository import BudgetRepository
from source.services.budget_service import BudgetService


def main(service: BudgetService):

    
    root = tk.Tk()
    app = BudgetApp(root, service = service)
    root.mainloop()


if __name__ == "__main__":

    init_db()
    repo = BudgetRepository()
    service = BudgetService(repo)

    main(service)
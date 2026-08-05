import tkinter as tk
from source.gui.main_window import BudgetApp


def main():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
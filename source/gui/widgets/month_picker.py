"""
Purpose: Dropdown card popover for selecting any month and year.
"""

import calendar
import tkinter as tk
from datetime import date


class MonthPickerPopup(tk.Toplevel):
    def __init__(self, parent_button: tk.Widget, initial_year: int, initial_month: int, on_select_callback):
        self.root_window = parent_button.winfo_toplevel()
        super().__init__(self.root_window)
        self.parent_button = parent_button
        self.on_select = on_select_callback
        self.selected_year = initial_year
        self.selected_month = initial_month
        self.display_year = initial_year

        # Floating card styling (frameless popover)
        self.transient(self.root_window)
        self.overrideredirect(True)
        self.configure(bg="#ffffff", highlightthickness=1, highlightbackground="#cccccc")

        # Build UI first so Tkinter can compute exact required dimensions
        self.create_ui()
        self.position_below_widget()

        # Dismiss when clicking outside
        self._root_click_bind_id = self.root_window.bind("<Button-1>", self._check_click_outside, add="+")
        self.bind("<Escape>", lambda event: self.destroy())

    def _check_click_outside(self, event):
        """Closes the popup if the click occurred outside its boundary"""
        if not self.winfo_exists():
            return
        
        x, y = event.x_root, event.y_root
        bx = self.winfo_rootx()
        by = self.winfo_rooty()
        bw = self.winfo_width()
        bh = self.winfo_height()

        if not (bx <= x <= bx + bw and by <= y <= by + bh):
            clicked_widget = event.widget
            if clicked_widget:
                # Release button when pressed, while popup monthly picker is open
                def _button_release(e):
                    try:
                        clicked_widget.unbind("<ButtonRelease-1>")
                    except Exception:
                        pass
                    return "break"

                try:
                    clicked_widget.bind("<ButtonRelease-1>", _button_release, add=False)
                except Exception:
                    pass

            self.destroy()

    def position_below_widget(self):
        self.update_idletasks()
        self.parent_button.update_idletasks()

        x = self.parent_button.winfo_rootx()
        y = self.parent_button.winfo_rooty() + self.parent_button.winfo_height() + 4

        # Dynamic sizing ensures all 4 columns (Apr, Aug, Dec) are visible on macOS
        req_w = max(340, self.winfo_reqwidth() + 10)
        req_h = max(185, self.winfo_reqheight() + 10)
        self.geometry(f"{req_w}x{req_h}+{x}+{y}")

    def create_ui(self):
        for child in self.winfo_children():
            child.destroy()

        # 1. Header: Stepper Controls (‹ 2026 ›)
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill=tk.X, padx=12, pady=(10, 6))

        btn_prev = tk.Button(
            header_frame, text="‹", font=("Helvetica", 14, "bold"),
            relief=tk.FLAT, bg="#ffffff", activebackground="#f0f0f0",
            cursor="hand2", command=self.prev_year
        )
        btn_prev.pack(side=tk.LEFT)

        lbl_year = tk.Label(
            header_frame, text=str(self.display_year),
            font=("Helvetica", 13, "bold"), bg="#ffffff", fg="#222222"
        )
        lbl_year.pack(side=tk.LEFT, expand=True)

        btn_next = tk.Button(
            header_frame, text="›", font=("Helvetica", 14, "bold"),
            relief=tk.FLAT, bg="#ffffff", activebackground="#f0f0f0",
            cursor="hand2", command=self.next_year
        )
        btn_next.pack(side=tk.RIGHT)

        # 2. 4x3 Month Grid (Cols 0-3: Jan-Apr, May-Aug, Sep-Dec)
        grid_frame = tk.Frame(self, bg="#ffffff")
        grid_frame.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

        for c in range(4):
            grid_frame.columnconfigure(c, weight=1)

        months = [calendar.month_abbr[i] for i in range(1, 13)]
        for idx, m_name in enumerate(months):
            m_num = idx + 1
            row, col = divmod(idx, 4)

            is_active = (self.display_year == self.selected_year and m_num == self.selected_month)

            btn = tk.Button(
                grid_frame,
                text=m_name,
                width=4,
                relief=tk.RAISED if not is_active else tk.SUNKEN,
                font=("Helvetica", 11),
                cursor="hand2" if not is_active else "arrow",
                command=lambda m=m_num: self.select_month(m)
            )

            # Gray out & disable current month
            if is_active:
                btn.config(state=tk.DISABLED)

            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

    def prev_year(self):
        self.display_year -= 1
        self.create_ui()

    def next_year(self):
        self.display_year += 1
        self.create_ui()

    def select_month(self, month: int):
        self.on_select(self.display_year, month)
        self.destroy()

    def destroy(self):
        try:
            self.root_window.unbind("<Button-1>", self._root_click_bind_id)
        except Exception:
            pass
        super().destroy()
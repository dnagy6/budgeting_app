"""
File: source/gui/widgets/card_inline_edit_mixin.py
Purpose: Encapsulates click-to-edit labels and inline creation input rows.
"""

import tkinter as tk
from tkinter import ttk

class CardInlineEditMixin:
    def _start_inline_group_name_edit(self):
        old_name = self.group.name
        self.lbl_title.pack_forget()

        entry = tk.Entry(self.lbl_title.master, font=("Helvetica", 12, "bold"))
        entry.insert(0, old_name)
        entry.select_range(0, tk.END)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.focus_set()

        def save_group_name(event=None):
            new_name = entry.get().strip()
            entry.destroy()
            self.lbl_title.pack(side=tk.LEFT)
            if new_name and new_name != old_name:
                if hasattr(self, "on_rename_group") and self.on_rename_group:
                    self.on_rename_group(old_name, new_name)
                else:
                    self.group.name = new_name
                    self.lbl_title.config(text=new_name)

        def cancel(event=None):
            entry.destroy()
            self.lbl_title.pack(side=tk.LEFT)

        entry.bind("<Return>", save_group_name)
        entry.bind("<FocusOut>", save_group_name)
        entry.bind("<Escape>", cancel)

    def _start_inline_name_edit(self, cat, label, parent_grid):
        info = label.grid_info()
        label.grid_remove()

        entry = tk.Entry(parent_grid, font=("Helvetica", 11))
        entry.insert(0, cat.name)
        entry.select_range(0, tk.END)
        entry.grid(row=info["row"], column=info["column"], sticky="w", pady=2)
        entry.focus_set()

        def save_name(event=None):
            new_name = entry.get().strip()
            entry.destroy()
            if new_name and new_name != cat.name:
                if self.on_inline_edit:
                    self.on_inline_edit(cat.name, new_name, cat.planned_amount)
            else:
                label.grid()

        def cancel(event=None):
            entry.destroy()
            label.grid()

        entry.bind("<Return>", save_name)
        entry.bind("<FocusOut>", save_name)
        entry.bind("<Escape>", cancel)

    def _start_inline_amount_edit(self, cat, label, parent_grid):
        info = label.grid_info()
        label.grid_remove()

        entry = tk.Entry(parent_grid, font=("Helvetica", 11), width=10, justify="right")
        entry.insert(0, f"{cat.planned_amount:.2f}")
        entry.select_range(0, tk.END)
        entry.grid(row=info["row"], column=info["column"], sticky="e", padx=10, pady=2)
        entry.focus_set()

        def save_amount(event=None):
            raw = entry.get().replace("$", "").replace(",", "").strip()
            entry.destroy()
            try:
                val = float(raw) if raw else 0.0
                if val < 0:
                    raise ValueError
                if val != cat.planned_amount:
                    if self.on_inline_edit:
                        self.on_inline_edit(cat.name, cat.name, val)
                else:
                    label.grid()
            except ValueError:
                label.grid()

        def cancel(event=None):
            entry.destroy()
            label.grid()

        entry.bind("<Return>", save_amount)
        entry.bind("<FocusOut>", save_amount)
        entry.bind("<Escape>", cancel)

    def _toggle_inline_add_row(self):
        if hasattr(self, "inline_row_frame") and self.inline_row_frame.winfo_exists():
            return

        self.inline_row_frame = tk.Frame(self.body_frame, bg="#ffffff", pady=6)
        self.inline_row_frame.pack(fill=tk.X, padx=16, before=self.footer_frame)

        self.ent_name = tk.Entry(self.inline_row_frame, font=("Helvetica", 11))
        self.ent_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.ent_name.insert(0, "Name")
        self.ent_name.focus_set()
        self.ent_name.select_range(0, tk.END)
        self.ent_name.bind("<FocusIn>", lambda e: self.ent_name.delete(0, tk.END) if self.ent_name.get() == "Name" else None)

        self.ent_amount = tk.Entry(self.inline_row_frame, font=("Helvetica", 11), width=10)
        self.ent_amount.pack(side=tk.LEFT, padx=(0, 6))
        self.ent_amount.insert(0, "0.00")

        btn_save = tk.Button(
            self.inline_row_frame, text="✓", font=("Helvetica", 10, "bold"),
            bg="#16a34a", fg="#ffffff", relief=tk.FLAT, bd=0, cursor="hand2",
            command=self._commit_inline_item
        )
        btn_save.pack(side=tk.LEFT, padx=(0, 4))

        btn_cancel = tk.Button(
            self.inline_row_frame, text="✕", font=("Helvetica", 10, "bold"),
            bg="#ef4444", fg="#ffffff", relief=tk.FLAT, bd=0, cursor="hand2",
            command=self.inline_row_frame.destroy
        )
        btn_cancel.pack(side=tk.LEFT)

        self.ent_name.bind("<Return>", lambda e: self._commit_inline_item())
        self.ent_amount.bind("<Return>", lambda e: self._commit_inline_item())

    def _commit_inline_item(self):
        name = self.ent_name.get().strip()
        raw_amount = self.ent_amount.get().strip()

        if not name or name == "Name":
            return

        try:
            amount = float(raw_amount)
        except ValueError:
            amount = 0.0

        if hasattr(self, "on_inline_save_category") and self.on_inline_save_category:
            self.on_inline_save_category(
                group_name=self.group.name,
                category_name=name,
                planned_amount=amount,
                category_type=self.group.group_type
            )

        if hasattr(self, "inline_row_frame") and self.inline_row_frame.winfo_exists():
            self.inline_row_frame.destroy()
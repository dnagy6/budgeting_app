"""
File: source/gui/widgets/card_inline_edit_mixin.py
Purpose: Encapsulates click-to-edit labels and column-aligned inline creation input rows.
"""

import tkinter as tk
from tkinter import ttk
from source.settings import Theme

class CardInlineEditMixin:
    def _start_inline_group_name_edit(self):
        old_name = self.group.name
        self.lbl_title.pack_forget()

        entry = tk.Entry(
            self.lbl_title.master,
            font=Theme.FONT_HEADER,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Theme.ACCENT_PRIMARY
        )
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

        entry = tk.Entry(
            parent_grid,
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Theme.ACCENT_PRIMARY
        )
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

        entry = tk.Entry(
            parent_grid,
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Theme.ACCENT_PRIMARY,
            width=10,
            justify="right"
        )
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
        # If the group has no categories yet, render the table structure first so grid_table exists
        if not self.group.categories:
            self._render_category_grid()

        if not hasattr(self, "grid_table") or not self.grid_table.winfo_exists():
            return

        # Prevent opening duplicate input rows
        if hasattr(self, "ent_name") and self.ent_name.winfo_exists():
            return

        row_idx = len(self.group.categories) * 2 + 1

        # Subtle divider above the input row
        self.inline_div = tk.Frame(self.grid_table, bg=Theme.BORDER_SUBTLE, height=1)
        self.inline_div.grid(row=row_idx, column=0, columnspan=5, sticky="ew", pady=2)
        row_idx += 1

        # Name Entry gridded directly into Column 0 (Category Name)
        self.ent_name = tk.Entry(
            self.grid_table,
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Theme.ACCENT_PRIMARY
        )
        self.ent_name.grid(row=row_idx, column=0, sticky="ew", pady=4)
        self.ent_name.focus_set()

        # Planned Amount Entry gridded directly into Column 1 (Planned)
        self.ent_amount = tk.Entry(
            self.grid_table,
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_SUBTLE,
            width=10,
            justify="right"
        )
        self.ent_amount.grid(row=row_idx, column=1, sticky="e", padx=(0, 10), pady=4)
        self.ent_amount.insert(0, "0.00")

        # Smooth Keyboard Navigation: Enter on name moves to amount; Enter on amount saves.
        def focus_amount(event):
            self.ent_amount.focus_set()
            self.ent_amount.select_range(0, tk.END)
            return "break"

        def commit(event=None):
            self._commit_inline_item()

        def cancel(event=None):
            self._remove_inline_row()

        self.ent_name.bind("<Return>", focus_amount)
        self.ent_name.bind("<Escape>", cancel)
        self.ent_amount.bind("<Return>", commit)
        self.ent_amount.bind("<Escape>", cancel)

    def _remove_inline_row(self):
        for attr in ("ent_name", "ent_amount", "inline_div"):
            if hasattr(self, attr) and getattr(self, attr).winfo_exists():
                getattr(self, attr).destroy()

    def _commit_inline_item(self):
        name = self.ent_name.get().strip() if hasattr(self, "ent_name") else ""
        raw_amount = self.ent_amount.get().strip() if hasattr(self, "ent_amount") else "0.00"

        self._remove_inline_row()

        if not name:
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
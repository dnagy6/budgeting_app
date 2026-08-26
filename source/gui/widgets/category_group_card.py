"""
File: source/gui/widgets/category_group_card.py
Purpose: Accordion Card with drag-and-drop grip handle and inline click-to-edit envelopes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from source.domain.category import Category
from source.domain.category_group import CategoryGroup


class CategoryGroupCard(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        group: CategoryGroup,
        on_add_category: Callable[[str, str], None],
        on_inline_edit: Callable[[str, str, float], None],
        on_delete_category: Callable[[str], None],
        on_delete_group: Callable[[str], None],
        on_reorder_complete: Callable[[], None],
        on_rename_group: Optional[Callable[[str, str], None]] = None,
        initial_expanded: bool = True,
        **kwargs
    ):
        self.on_rename_group = on_rename_group

        super().__init__(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0", bd=0, **kwargs)
        self.group = group
        self.container_parent = parent
        self.on_add_category = on_add_category
        self.on_inline_edit = on_inline_edit
        self.on_delete_category = on_delete_category
        self.on_delete_group = on_delete_group
        self.on_reorder_complete = on_reorder_complete
        self.is_expanded = initial_expanded

        self._create_ui()

    def _create_ui(self):
        # 1. Group Header Bar
        self.header_frame = tk.Frame(self, bg="#f8fafc", padx=12, pady=10)
        self.header_frame.pack(fill=tk.X)

        controls_left = tk.Frame(self.header_frame, bg="#f8fafc")
        controls_left.pack(side=tk.LEFT)

        # Drag Grip Handle (⋮⋮)
        self.lbl_grip = tk.Label(
            controls_left,
            text="⋮⋮",
            font=("Helvetica", 14, "bold"),
            bg="#f8fafc",
            fg="#94a3b8",
            cursor="fleur"
        )
        self.lbl_grip.pack(side=tk.LEFT, padx=(0, 8))
        self._bind_drag_events(self.lbl_grip)

        # Expand / Collapse Arrow
        self.lbl_arrow = tk.Label(
            controls_left,
            text="▾",
            font=("Helvetica", 12, "bold"),
            bg="#f8fafc",
            fg="#475569",
            cursor="hand2"
        )
        self.lbl_arrow.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_arrow.bind("<Button-1>", lambda e: self.toggle_expand())

        # # Group Name Title
        self.lbl_title = tk.Label(
            controls_left,
            text=self.group.name,
            font=("Helvetica", 12, "bold"),
            bg="#f8fafc",
            fg="#0f172a",
            cursor="xterm"  # Indicates text editability
        )
        self.lbl_title.pack(side=tk.LEFT)
        self.lbl_title.bind("<Button-1>", lambda e: self._start_inline_group_name_edit())

        # Header Summary Totals
        total_planned = self.group.get_total_planned()
        total_actual = self.group.get_total_actual()
        actual_label = "Received" if self.group.group_type == "income" else "Spent"

        summary_text = f"Planned: ${total_planned:,.2f}   |   {actual_label}: ${total_actual:,.2f}"
        self.lbl_summary = tk.Label(
            self.header_frame,
            text=summary_text,
            font=("Helvetica", 10, "bold"),
            bg="#f8fafc",
            fg="#64748b"
        )
        self.lbl_summary.pack(side=tk.RIGHT)

        # 2. Body Container (Child Envelopes)
        self.body_frame = tk.Frame(self, bg="#ffffff", padx=16, pady=6)
        self.body_frame.pack(fill=tk.X)

        self._render_category_grid()

        # Apply initial collapsed state if needed
        if not self.is_expanded:
            self.lbl_arrow.config(text="▸")
            self.body_frame.pack_forget()

    def _render_category_grid(self):
        for child in self.body_frame.winfo_children():
            child.destroy()

        if not self.group.categories:
            lbl_empty = tk.Label(
                self.body_frame,
                text="No envelopes in this group yet.",
                font=("Helvetica", 10, "italic"),
                fg="#94a3b8",
                bg="#ffffff",
                pady=8
            )
            lbl_empty.pack(anchor="w")
        else:
            # Single Shared Grid for Table Header & Rows
            grid_table = tk.Frame(self.body_frame, bg="#ffffff")
            grid_table.pack(fill=tk.X)

            grid_table.columnconfigure(0, weight=1)       # Category Name
            grid_table.columnconfigure(1, minsize=120)    # Planned
            grid_table.columnconfigure(2, minsize=140)    # Spent/Received
            grid_table.columnconfigure(3, minsize=120)    # Remaining
            grid_table.columnconfigure(4, minsize=40)     # Delete Action

            # Header Labels
            actual_header = "RECEIVED" if self.group.group_type == "income" else "SPENT / RECEIVED"
            tk.Label(grid_table, text="CATEGORY", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=(0, 6))
            tk.Label(grid_table, text="PLANNED", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=1, sticky="e", padx=(0, 10), pady=(0, 6))
            tk.Label(grid_table, text=actual_header, font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=2, sticky="e", padx=(0, 10), pady=(0, 6))
            tk.Label(grid_table, text="REMAINING", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#ffffff").grid(row=0, column=3, sticky="e", padx=(0, 10), pady=(0, 6))

            current_row = 1
            for cat in self.group.categories:
                # Divider
                div = tk.Frame(grid_table, bg="#f1f5f9", height=1)
                div.grid(row=current_row, column=0, columnspan=5, sticky="ew", pady=2)
                current_row += 1

                # 1. Category Name (Click-to-Edit)
                lbl_name = tk.Label(
                    grid_table,
                    text=cat.name,
                    font=("Helvetica", 11),
                    fg="#1e293b",
                    bg="#ffffff",
                    cursor="xterm"
                )
                lbl_name.grid(row=current_row, column=0, sticky="w", pady=4)
                lbl_name.bind("<Button-1>", lambda e, c=cat, l=lbl_name: self._start_inline_name_edit(c, l, grid_table))

                # 2. Planned Amount (Click-to-Edit)
                lbl_planned = tk.Label(
                    grid_table,
                    text=f"${cat.planned_amount:,.2f}",
                    font=("Helvetica", 11),
                    fg="#0284c7",
                    bg="#ffffff",
                    cursor="hand2"
                )
                lbl_planned.grid(row=current_row, column=1, sticky="e", padx=(0, 10), pady=4)
                lbl_planned.bind("<Button-1>", lambda e, c=cat, l=lbl_planned: self._start_inline_amount_edit(c, l, grid_table))

                # 3. Actual Amount (Read-only)
                actual_val = cat.get_actual_amount()
                tk.Label(
                    grid_table,
                    text=f"${actual_val:,.2f}",
                    font=("Helvetica", 11),
                    fg="#334155",
                    bg="#ffffff"
                ).grid(row=current_row, column=2, sticky="e", padx=(0, 10), pady=4)

                # 4. Remaining Amount (Read-only)
                rem_val = cat.get_remaining_amount()
                rem_color = "#dc2626" if rem_val < 0 else "#16a34a"
                tk.Label(
                    grid_table,
                    text=f"${rem_val:,.2f}",
                    font=("Helvetica", 11, "bold"),
                    fg=rem_color,
                    bg="#ffffff"
                ).grid(row=current_row, column=3, sticky="e", padx=(0, 10), pady=4)

                # 5. Delete Action (✕)
                btn_del = tk.Button(
                    grid_table,
                    text="✕",
                    font=("Helvetica", 10),
                    fg="#ef4444",
                    bg="#ffffff",
                    relief=tk.FLAT,
                    bd=0,
                    cursor="hand2",
                    command=lambda n=cat.name: self.on_delete_category(n)
                )
                btn_del.grid(row=current_row, column=4, sticky="e", padx=(4, 0))

                current_row += 1

        # 3. Card Footer Action Bar
        footer = tk.Frame(self.body_frame, bg="#ffffff")
        footer.pack(fill=tk.X, pady=(12, 4))

        btn_label = "+ Add Income" if self.group.group_type == "income" else "+ Add Expense"
        btn_add = tk.Button(
            footer,
            text=btn_label,
            font=("Helvetica", 10, "bold"),
            fg="#0284c7",
            bg="#ffffff",
            activeforeground="#0369a1",
            activebackground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.on_add_category(self.group.name, self.group.group_type)
        )
        btn_add.pack(side=tk.LEFT)

        btn_del_grp = tk.Button(
            footer,
            text="Delete Group",
            font=("Helvetica", 9),
            fg="#94a3b8",
            bg="#ffffff",
            activeforeground="#ef4444",
            activebackground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.on_delete_group(self.group.name)
        )
        btn_del_grp.pack(side=tk.RIGHT)

    # --- INLINE EDITING LOGIC ---

    def _start_inline_group_name_edit(self):
        """Replaces category group title label with an inline Entry field."""
        old_name = self.group.name
        
        # Hide label
        self.lbl_title.pack_forget()

        # Create inline entry inside the header frame
        entry = ttk.Entry(self.lbl_title.master, font=("Helvetica", 12, "bold"))
        entry.insert(0, old_name)
        entry.select_range(0, tk.END)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.focus_set()

        def save_group_name(event=None):
            new_name = entry.get().strip()
            entry.destroy()
            self.lbl_title.pack(side=tk.LEFT)
            
            if new_name and new_name != old_name:
                # Notify parent/main window to update repository and domain model
                if hasattr(self, "on_rename_group") and self.on_rename_group:
                    self.on_rename_group(old_name, new_name)
                else:
                    # Fallback or direct callback if mapped
                    self.group.name = new_name
                    self.lbl_title.config(text=new_name)

        def cancel(event=None):
            entry.destroy()
            self.lbl_title.pack(side=tk.LEFT)

        entry.bind("<Return>", save_group_name)
        entry.bind("<FocusOut>", save_group_name)
        entry.bind("<Escape>", cancel)

    def _start_inline_name_edit(self, cat: Category, label: tk.Label, parent_grid: tk.Frame):
        """Replaces category name label with an inline Entry field."""
        info = label.grid_info()
        label.grid_remove()

        entry = ttk.Entry(parent_grid, font=("Helvetica", 11))
        entry.insert(0, cat.name)
        entry.select_range(0, tk.END)
        entry.grid(row=info["row"], column=info["column"], sticky="w", pady=2)
        entry.focus_set()

        def save_name(event=None):
            new_name = entry.get().strip()
            entry.destroy()
            if new_name and new_name != cat.name:
                self.on_inline_edit(cat.name, new_name, cat.planned_amount)
            else:
                label.grid()

        def cancel(event=None):
            entry.destroy()
            label.grid()

        entry.bind("<Return>", save_name)
        entry.bind("<FocusOut>", save_name)
        entry.bind("<Escape>", cancel)

    def _start_inline_amount_edit(self, cat: Category, label: tk.Label, parent_grid: tk.Frame):
        """Replaces planned amount label with an inline Entry field."""
        info = label.grid_info()
        label.grid_remove()

        entry = ttk.Entry(parent_grid, font=("Helvetica", 11), width=10, justify="right")
        entry.insert(0, f"{cat.planned_amount:.2f}")
        entry.select_range(0, tk.END)
        entry.grid(row=info["row"], column=info["column"], sticky="e", padx=(0, 10), pady=2)
        entry.focus_set()

        def save_amount(event=None):
            raw = entry.get().replace("$", "").replace(",", "").strip()
            entry.destroy()
            try:
                val = float(raw) if raw else 0.0
                if val < 0:
                    raise ValueError
                if val != cat.planned_amount:
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

    # --- DRAG AND DROP LOGIC ---

    def _bind_drag_events(self, widget: tk.Widget):
        widget.bind("<ButtonPress-1>", self._on_drag_start)
        widget.bind("<B1-Motion>", self._on_drag_motion)
        widget.bind("<ButtonRelease-1>", self._on_drag_release)

    def _on_drag_start(self, event):
        self._start_y = event.y_root
        self._is_dragging = False

    def _on_drag_motion(self, event):
        # 8px threshold before activating drag mode
        if abs(event.y_root - self._start_y) > 8:
            if not self._is_dragging:
                self._is_dragging = True
                self.config(highlightbackground="#0284c7", highlightthickness=2)
                # Temporarily collapse body while dragging for a compact, responsive tile
                if self.is_expanded:
                    self.body_frame.pack_forget()
                    self.lbl_arrow.config(text="▸")

            y_curr = event.y_root
            siblings = [
                c for c in self.container_parent.winfo_children()
                if isinstance(c, CategoryGroupCard) and c is not self
            ]
            for s in siblings:
                s_y = s.winfo_rooty()
                s_h = s.winfo_height()
                if s_y <= y_curr <= s_y + s_h:
                    s.config(highlightbackground="#93c5fd", highlightthickness=2)
                else:
                    s.config(highlightbackground="#e2e8f0", highlightthickness=1)

    def _on_drag_release(self, event):
        # Reset border highlights on all cards
        siblings = [
            c for c in self.container_parent.winfo_children()
            if isinstance(c, CategoryGroupCard)
        ]
        for s in siblings:
            s.config(highlightbackground="#e2e8f0", highlightthickness=1)

        # If it was just a click without dragging, restore state if needed and return
        if not getattr(self, "_is_dragging", False):
            return

        self._is_dragging = False
        y_release = event.y_root

        # Get all other cards sorted by current vertical position
        other_cards = sorted(
            [c for c in siblings if c is not self],
            key=lambda c: c.winfo_rooty()
        )

        # Calculate insertion index based on sibling card midpoints
        target_idx = len(other_cards)
        for idx, card in enumerate(other_cards):
            card_mid = card.winfo_rooty() + (card.winfo_height() // 2)
            if y_release < card_mid:
                target_idx = idx
                break

        # Build new visual order
        new_order = [c.group.name for c in other_cards]
        new_order.insert(target_idx, self.group.name)

        # Persist new order and re-render
        if self.on_reorder_complete:
            self.on_reorder_complete(new_order)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.lbl_arrow.config(text="▾")
            self.body_frame.pack(fill=tk.X)
        else:
            self.lbl_arrow.config(text="▸")
            self.body_frame.pack_forget()
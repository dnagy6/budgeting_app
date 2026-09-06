"""
File: source/gui/widgets/summary_card.py
Purpose: Telemetry sidebar displaying hero budget totals and group progress bars.
"""

import tkinter as tk
from source.settings import Theme


class SummaryCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            bd=0,
            highlightthickness=0,
            **kwargs
        )
        self._create_ui()

    def _create_ui(self):
        # 1. Hero Metric: Left to Budget
        lbl_unallocated_title = tk.Label(
            self,
            text="LEFT TO BUDGET",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_unallocated_title.pack(anchor="w")

        self.unallocated_val_label = tk.Label(
            self,
            text="$0.00",
            font=Theme.FONT_LARGE_TITLE,
            fg=Theme.SUCCESS,
            bg=Theme.BG_CARD
        )
        self.unallocated_val_label.pack(anchor="w", pady=(0, 16))

        # 2. Hero Metric: Income Received
        lbl_income_title = tk.Label(
            self,
            text="INCOME RECEIVED",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_income_title.pack(anchor="w")

        self.income_val_label = tk.Label(
            self,
            text="$0.00",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        self.income_val_label.pack(anchor="w", pady=(0, 20))

        # 3. Hairline Divider
        div = tk.Frame(self, bg=Theme.BORDER_HAIRLINE, height=1)
        div.pack(fill=tk.X, pady=(0, 16))

        # 4. Telemetry Section Header
        lbl_breakdown = tk.Label(
            self,
            text="EXPENSE BREAKDOWN",
            font=Theme.FONT_LABEL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_breakdown.pack(anchor="w", pady=(0, 12))

        # 5. Dynamic Container for Group Telemetry Cards
        self.telemetry_container = tk.Frame(self, bg=Theme.BG_CARD)
        self.telemetry_container.pack(fill=tk.BOTH, expand=True)

    def update_values(self, income: float, unallocated: float, groups: list = None):
        # Format Income Received
        self.income_val_label.config(text=f"${income:,.2f}")

        # Format Left to Budget with standard financial negative formatting
        if unallocated < 0:
            formatted_unallocated = f"-${abs(unallocated):,.2f}"
            self.unallocated_val_label.config(text=formatted_unallocated, fg=Theme.DANGER)
        else:
            formatted_unallocated = f"${unallocated:,.2f}"
            self.unallocated_val_label.config(text=formatted_unallocated, fg=Theme.SUCCESS)

        # Render Group Progress Bars
        if groups is not None:
            self._render_group_telemetry(groups)

    def _render_group_telemetry(self, groups: list):
        for child in self.telemetry_container.winfo_children():
            child.destroy()

        expense_groups = [
            g for g in groups
            if g.group_type != "income" and g.name.lower() != "income"
        ]

        if not expense_groups:
            lbl_empty = tk.Label(
                self.telemetry_container,
                text="No expense groups to track.",
                font=Theme.FONT_BODY,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_empty.pack(anchor="w", pady=6)
            return

        for grp in expense_groups:
            planned = grp.get_total_planned()
            spent = grp.get_total_actual()
            remaining = planned - spent

            pct = (spent / planned) if planned > 0 else (1.0 if spent > 0 else 0.0)

            # Bar color: Red if overspent, green if on track
            if spent > planned and planned > 0:
                bar_color = Theme.DANGER
            elif pct >= 0.85:
                bar_color = Theme.BRAND_HIGHLIGHT
            else:
                bar_color = Theme.SUCCESS

            grp_box = tk.Frame(self.telemetry_container, bg=Theme.BG_CARD)
            grp_box.pack(fill=tk.X, pady=(0, 14))

            # Row 1: Group Name & Total Budget
            header_row = tk.Frame(grp_box, bg=Theme.BG_CARD)
            header_row.pack(fill=tk.X)

            lbl_grp_name = tk.Label(
                header_row,
                text=grp.name,
                font=Theme.FONT_BODY,
                fg=Theme.TEXT_PRIMARY,
                bg=Theme.BG_CARD
            )
            lbl_grp_name.pack(side=tk.LEFT)

            lbl_grp_planned = tk.Label(
                header_row,
                text=f"${planned:,.2f} budget",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_grp_planned.pack(side=tk.RIGHT)

            # Row 2: Progress Track & Fill
            outer_bar = tk.Frame(grp_box, bg=Theme.HOVER_BG, height=6)
            outer_bar.pack(fill=tk.X, pady=(4, 4))
            outer_bar.pack_propagate(False)

            inner_bar = tk.Frame(outer_bar, bg=bar_color, height=6)
            inner_bar.place(x=0, y=0, relwidth=min(pct, 1.0), relheight=1.0)

            # Row 3: Spent & Remaining Stats
            stats_row = tk.Frame(grp_box, bg=Theme.BG_CARD)
            stats_row.pack(fill=tk.X)

            lbl_spent = tk.Label(
                stats_row,
                text=f"${spent:,.2f} spent",
                font=Theme.FONT_LABEL,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD
            )
            lbl_spent.pack(side=tk.LEFT)

            rem_text = f"-${abs(remaining):,.2f}" if remaining < 0 else f"${remaining:,.2f}"
            rem_fg = Theme.DANGER if remaining < 0 else Theme.SUCCESS

            lbl_remaining = tk.Label(
                stats_row,
                text=f"{rem_text} remaining",
                font=Theme.FONT_LABEL,
                fg=rem_fg,
                bg=Theme.BG_CARD
            )
            lbl_remaining.pack(side=tk.RIGHT)
"""
File: source/gui/widgets/card_drag_mixin.py
Purpose: Encapsulates drag-and-drop reordering mechanics for category group cards.
"""

import tkinter as tk

class CardDragMixin:
    def _bind_drag_events(self, widget: tk.Widget):
        widget.bind("<ButtonPress-1>", self._on_drag_start)
        widget.bind("<B1-Motion>", self._on_drag_motion)
        widget.bind("<ButtonRelease-1>", self._on_drag_release)

    def _on_drag_start(self, event):
        self._start_y = event.y_root
        self._is_dragging = False

    def _on_drag_motion(self, event):
        if abs(event.y_root - self._start_y) > 8:
            if not self._is_dragging:
                self._is_dragging = True
                self.config(highlightbackground="#0284c7", highlightthickness=2)
                if self.is_expanded:
                    self.body_frame.pack_forget()
                    self.lbl_arrow.config(text="▸")

            y_curr = event.y_root
            siblings = [
                c for c in self.container_parent.winfo_children()
                if isinstance(c, type(self)) and c is not self
            ]
            for s in siblings:
                s_y = s.winfo_rooty()
                s_h = s.winfo_height()
                if s_y <= y_curr <= s_y + s_h:
                    s.config(highlightbackground="#93c5fd", highlightthickness=2)
                else:
                    s.config(highlightbackground="#e2e8f0", highlightthickness=1)

    def _on_drag_release(self, event):
        siblings = [
            c for c in self.container_parent.winfo_children()
            if isinstance(c, type(self)) and c is not self
        ]
        for s in siblings:
            s.config(highlightbackground="#e2e8f0", highlightthickness=1)

        if not getattr(self, "_is_dragging", False):
            return

        self._is_dragging = False
        y_release = event.y_root

        other_cards = sorted(
            [c for c in siblings],
            key=lambda c: c.winfo_rooty()
        )

        target_idx = len(other_cards)
        for idx, card in enumerate(other_cards):
            card_mid = card.winfo_rooty() + (card.winfo_height() // 2)
            if y_release < card_mid:
                target_idx = idx
                break

        new_order = [c.group.name for c in other_cards]
        new_order.insert(target_idx, self.group.name)

        if hasattr(self, "on_reorder_complete") and self.on_reorder_complete:
            self.on_reorder_complete(new_order)
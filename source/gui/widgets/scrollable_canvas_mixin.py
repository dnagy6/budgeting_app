"""
File: source/gui/widgets/scrollable_canvas_mixin.py
Purpose: Encapsulates cross-platform smooth canvas scrolling using Tcl/Tk path-based event routing.
"""

import tkinter as tk

class ScrollableCanvasMixin:
    _active_scroll_containers = []

    def _init_scrollable_mixin(self, container: tk.Widget, canvas: tk.Canvas, inner_frame: tk.Frame):
        self._scroll_container = container
        self._scroll_canvas = canvas
        self._scroll_inner_frame = inner_frame

        if self not in ScrollableCanvasMixin._active_scroll_containers:
            ScrollableCanvasMixin._active_scroll_containers.append(self)

        self._scroll_inner_frame.bind("<Configure>", self._update_scroll_region)
        self._scroll_canvas.bind(
            "<Configure>",
            lambda e: (
                self._scroll_canvas.itemconfig(self._scroll_canvas_window, width=e.width) 
                if hasattr(self, "_scroll_canvas_window") else None, 
                self._update_scroll_region()
            )
        )

        top = container.winfo_toplevel()
        if not getattr(top, "_global_mousewheel_bound", False):
            top.bind_all("<MouseWheel>", ScrollableCanvasMixin._global_on_mousewheel)
            top.bind_all("<Button-4>", ScrollableCanvasMixin._global_on_mousewheel)
            top.bind_all("<Button-5>", ScrollableCanvasMixin._global_on_mousewheel)
            top._global_mousewheel_bound = True

    def _update_scroll_region(self, event=None):
        self._scroll_canvas.update_idletasks()
        content_height = self._scroll_inner_frame.winfo_reqheight()
        canvas_height = self._scroll_canvas.winfo_height()

        if content_height <= canvas_height:
            self._scroll_canvas.yview_moveto(0.0)
            self._scroll_canvas.configure(scrollregion=(0, 0, self._scroll_canvas.winfo_width(), canvas_height))
        else:
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    @classmethod
    def _global_on_mousewheel(cls, event):
        # Extract the raw Tcl/Tk hierarchical path of the exact widget under the cursor 
        # Example: '.!frame.!canvas.!frame.!categorygroupcard'
        widget_path = str(event.widget)
        
        for instance in cls._active_scroll_containers:
            # If the hovered widget's path originates from inside this specific container, route the scroll here!
            if widget_path.startswith(str(instance._scroll_container)):
                instance._handle_scroll(event)
                return "break"

    def _handle_scroll(self, event):
        content_height = self._scroll_inner_frame.winfo_reqheight()
        canvas_height = self._scroll_canvas.winfo_height()
        if content_height <= canvas_height:
            return

        if getattr(event, "num", None) == 4:
            self._scroll_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self._scroll_canvas.yview_scroll(1, "units")
        else:
            delta = getattr(event, "delta", 0)
            if delta:
                # Windows usually sends increments of 120
                if abs(delta) >= 120:
                    amount = int(-1 * (delta / 120))
                else:
                    # macOS trackpad sends native small integers
                    amount = int(-1 * delta)
                    
                    # Safeguard against truncation to 0 for micro-gestures
                    if amount == 0:
                        amount = -1 if delta > 0 else 1

                self._scroll_canvas.yview_scroll(amount, "units")
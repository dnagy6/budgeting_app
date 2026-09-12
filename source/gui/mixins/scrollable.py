"""
File: source/gui/widgets/scrollable_canvas_mixin.py
Purpose: Hybrid scroll engine supporting 60 FPS mouse-wheel lerp interpolation 
         and direct 1:1 macOS trackpad gesture synchronization.
"""

import sys
import time
import tkinter as tk


class ScrollableCanvasMixin:
    _active_scroll_containers = []

    def _init_scrollable_mixin(self, container: tk.Widget, canvas: tk.Canvas, inner_frame: tk.Frame):
        self._scroll_container = container
        self._scroll_canvas = canvas
        self._scroll_inner_frame = inner_frame

        # Animation state for physical mouse wheels
        self._target_fraction = 0.0
        self._animating = False
        self._after_id = None

        # Cadence tracker to distinguish trackpad vs. mouse wheel
        self._last_event_time = 0.0
        self._is_trackpad_stream = False

        # 1-pixel sub-increments for precise positioning
        self._scroll_canvas.configure(yscrollincrement=1)

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
            self._target_fraction = 0.0
            self._scroll_canvas.configure(scrollregion=(0, 0, self._scroll_canvas.winfo_width(), canvas_height))
        else:
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    @classmethod
    def _global_on_mousewheel(cls, event):
        """Routes wheel events to whichever active container the cursor is hovering over."""
        for instance in cls._active_scroll_containers:
            if not instance._scroll_container.winfo_exists() or not instance._scroll_container.winfo_viewable():
                continue

            c_path = str(instance._scroll_container)
            w_path = str(event.widget)

            hovered = event.widget.winfo_containing(event.x_root, event.y_root) if hasattr(event.widget, "winfo_containing") else None
            h_path = str(hovered) if hovered else ""

            if w_path.startswith(c_path) or h_path.startswith(c_path):
                instance._handle_scroll(event)
                return "break"

    def _handle_scroll(self, event):
        content_height = self._scroll_inner_frame.winfo_reqheight()
        canvas_height = self._scroll_canvas.winfo_height()

        if content_height <= canvas_height or canvas_height <= 0:
            return

        max_scroll_px = max(1, content_height - canvas_height)
        now = time.time()
        dt = now - self._last_event_time
        self._last_event_time = now

        # Linux scroll buttons
        if getattr(event, "num", None) in (4, 5):
            delta_px = -50 if event.num == 4 else 50
            self._start_mouse_lerp(delta_px, content_height, max_scroll_px)
            return

        delta = getattr(event, "delta", 0)
        if not delta:
            return

        # 1. Standard mouse wheel with 120-increments (Windows or Logitech Options on Mac)
        if abs(delta) >= 120:
            delta_px = int(-1 * (delta / 120) * 50)
            self._start_mouse_lerp(delta_px, content_height, max_scroll_px)
            return

        # 2. Non-Darwin fallback
        if sys.platform != "darwin":
            delta_px = int(-1 * delta * 50)
            self._start_mouse_lerp(delta_px, content_height, max_scroll_px)
            return

        # 3. macOS Engine Selection:
        # Trackpad events arrive continuously in rapid succession (dt < 45ms).
        # Physical mouse wheel clicks are separated by longer gaps (> 50ms).
        if dt < 0.045:
            self._is_trackpad_stream = True
        elif dt > 0.08:
            self._is_trackpad_stream = False

        if self._is_trackpad_stream:
            # Cancel any running mouse wheel lerp so it doesn't fight the trackpad
            if self._animating:
                if self._after_id:
                    self._scroll_canvas.after_cancel(self._after_id)
                    self._after_id = None
                self._animating = False

            # Direct 1:1 hardware scroll (zero latency, zero lerp delay)
            delta_px = -int(delta * 14)
            current_fraction = self._scroll_canvas.yview()[0]
            current_px = current_fraction * content_height
            target_px = max(0, min(current_px + delta_px, max_scroll_px))

            self._scroll_canvas.yview_moveto(target_px / content_height)
            self._target_fraction = target_px / content_height
        else:
            # Physical mouse notch on macOS
            delta_px = -50 if delta > 0 else 50
            self._start_mouse_lerp(delta_px, content_height, max_scroll_px)

    def _start_mouse_lerp(self, delta_px: int, content_height: int, max_scroll_px: int):
        """Initializes ease-out lerp interpolation for physical wheel clicks."""
        current_fraction = self._scroll_canvas.yview()[0]
        if not self._animating:
            self._target_fraction = current_fraction

        target_px = (self._target_fraction * content_height) + delta_px
        target_px = max(0, min(target_px, max_scroll_px))
        self._target_fraction = target_px / content_height

        if not self._animating:
            self._animating = True
            self._smooth_step(content_height)

    def _smooth_step(self, content_height: int):
        """Glides to the target fraction at 60 FPS."""
        if not self._scroll_canvas.winfo_exists():
            self._animating = False
            self._after_id = None
            return

        current_fraction = self._scroll_canvas.yview()[0]
        diff = self._target_fraction - current_fraction

        threshold = 0.5 / content_height if content_height > 0 else 0.0005
        if abs(diff) <= threshold:
            self._scroll_canvas.yview_moveto(self._target_fraction)
            self._animating = False
            self._after_id = None
            return

        next_fraction = current_fraction + (diff * 0.25)
        self._scroll_canvas.yview_moveto(next_fraction)
        self._after_id = self._scroll_canvas.after(16, lambda: self._smooth_step(content_height))
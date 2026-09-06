import os
from pathlib import Path

class AppConfig:
    # 1. System Paths (OS-agnostic using pathlib)
    BASE_DIR = Path(__file__).resolve().parent.parent
    DB_PATH = BASE_DIR / "source" / "persistence" / "budget.db"

    # 2. Window Defaults & Metadata
    APP_TITLE = "Zero-Based Budgeting App"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 750
    MIN_WIDTH = 1000
    MIN_HEIGHT = 680

    # 3. Financial Localization Defaults
    CURRENCY_SYMBOL = "$"
    DECIMAL_PLACES = 2

class Theme:
    # Text
    TEXT_PRIMARY = "#0f172a"   
    TEXT_MUTED = "#475569"

    # Typography
    FONT_TITLE = ("Avenir", 14, "bold")
    FONT_LARGE_TITLE = ("Avenir", 22, "bold")
    FONT_HEADER = ("Avenir", 11, "bold")
    FONT_BODY = ("Avenir", 11)
    FONT_LABEL = ("Avenir", 9, "bold")
    FONT_ITALIC_MUTED = ("Avenir", 10, "italic")

    # Backgrounds
    BG_MAIN = "#f4f7fa"        
    BG_SIDEBAR = "#1e293b"     
    BG_CARD = "#ffffff"
    BG_HEADER = "#f3f4f6"        
    
    # Accents
    ACCENT_PRIMARY = "#3b82f6" 
    ACCENT_POWDER = "#e0f2fe"
    BRAND_HIGHLIGHT = "#38bdf8"
    HOVER_BG = "#f1f5f9"
    BORDER_SUBTLE = "#cbd5e1"
    BORDER_HAIRLINE = "#F1F5F9"

    # Sidebar Specific
    SIDEBAR_BG = "#1e293b"
    SIDEBAR_TEXT_INACTIVE = "#cbd5e1"
    SIDEBAR_TEXT_ACTIVE = "#ffffff"
    SIDEBAR_ACTIVE_BG = "#3b82f6"
    SIDEBAR_HOVER_BG = "#334155"

    #Input Fields
    INPUT_BG = "#f9fafb"
    INPUT_BORDER = "#e5e7eb"
    
    # Status Colors
    SUCCESS = "#059669"
    DANGER = "#e11d48"

    # Status Pills (Leftover & Remaining Badges)
    PILL_SUCCESS_BG = "#dcfce7"
    PILL_SUCCESS_TEXT = "#166534"

    PILL_DANGER_BG = "#fee2e2"
    PILL_DANGER_TEXT = "#991b1b"

    PILL_NEUTRAL_BG = "#f3f4f6"
    PILL_NEUTRAL_TEXT = "#6b7280"
    
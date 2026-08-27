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
    # Backgrounds
    BG_MAIN = "#f4f7fa"        
    BG_SIDEBAR = "#1e293b"     
    BG_CARD = "#ffffff"        
    
    # Accents
    ACCENT_PRIMARY = "#3b82f6" 
    ACCENT_POWDER = "#e0f2fe"
    BRAND_HIGHLIGHT = "#38bdf8"
    HOVER_BG = "#f1f5f9"

    # Sidebar Specific
    SIDEBAR_BG = "#1e293b"
    SIDEBAR_TEXT_INACTIVE = "#cbd5e1"  # Crisp, readable light cool-gray
    SIDEBAR_TEXT_ACTIVE = "#ffffff"    # Pure white
    SIDEBAR_ACTIVE_BG = "#3b82f6"      # Vibrant powdered blue for the active tab
    SIDEBAR_HOVER_BG = "#334155"
    
    # Text
    TEXT_PRIMARY = "#0f172a"   
    TEXT_MUTED = "#475569"
    
    # Status Colors
    SUCCESS = "#059669"        
    DANGER = "#e11d48"         
    BORDER_SUBTLE = "#cbd5e1"  
    
    # Typography
    FONT_TITLE = ("Avenir", 14, "bold")
    FONT_LARGE_TITLE = ("Avenir", 22, "bold")
    FONT_HEADER = ("Avenir", 11, "bold")
    FONT_BODY = ("Avenir", 11)
    FONT_LABEL = ("Avenir", 9, "bold")
    FONT_ITALIC_MUTED = ("Avenir", 10, "italic")
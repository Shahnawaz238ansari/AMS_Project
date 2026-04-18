# ═══════════════════════════════════════════════════
#  GLOBAL THEME MANAGER  —  AMS Project
#  Professional Color Palette
# ═══════════════════════════════════════════════════

DARK = {
    "bg":           "#0f172a",
    "header_bg":    "#1e293b",
    "card_bg":      "#1e293b",
    "entry_bg":     "#1e293b",
    "fg":           "#f1f5f9",
    "sub_fg":       "#94a3b8",
    "accent":       "#38bdf8",
    "accent2":      "#818cf8",
    "success":      "#34d399",
    "warning":      "#fbbf24",
    "danger":       "#f87171",
    "toggle_bg":    "#334155",
    "toggle_fg":    "#f1f5f9",
    "toggle_text":  "☀️  Light Mode",
    "tree_bg":      "#1e293b",
    "tree_field":   "#1e293b",
    "frame_bg":     "#0f172a",
    "divider":      "#334155",
    "btn_reg":      "#0369a1",
    "btn_reg_h":    "#0284c7",
    "btn_login_s":  "#059669",
    "btn_login_sh": "#10b981",
    "btn_login_t":  "#b45309",
    "btn_login_th": "#d97706",
    "btn_attend":   "#6d28d9",
    "btn_attend_h": "#7c3aed",
}

LIGHT = {
    "bg":           "#c8e0f9",
    "header_bg":    "#82aee7",
    "card_bg":      "#e2e8f0",
    "entry_bg":     "#ffffff",
    "fg":           "#0f172a",
    "sub_fg":       "#475569",
    "accent":       "#0284c7",
    "accent2":      "#4f46e5",
    "success":      "#059669",
    "warning":      "#d97706",
    "danger":       "#dc2626",
    "toggle_bg":    "#cbd5e1",
    "toggle_fg":    "#0f172a",
    "toggle_text":  "🌙  Dark Mode",
    "tree_bg":      "#ffffff",
    "tree_field":   "#ffffff",
    "frame_bg":     "#f8fafc",
    "divider":      "#cbd5e1",
    "btn_reg":      "#0369a1",
    "btn_reg_h":    "#0284c7",
    "btn_login_s":  "#059669",
    "btn_login_sh": "#10b981",
    "btn_login_t":  "#b45309",
    "btn_login_th": "#d97706",
    "btn_attend":   "#6d28d9",
    "btn_attend_h": "#7c3aed",
}

_is_dark = True

def get_theme():
    return DARK if _is_dark else LIGHT

def toggle_theme():
    global _is_dark
    _is_dark = not _is_dark
    return get_theme()

def is_dark():
    return _is_dark
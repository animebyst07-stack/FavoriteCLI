from prompt_toolkit.styles import Style

STYLE = Style.from_dict({
    "frame":          "#ff8c00",
    "frame-title":    "#ff8c00 bold",
    "prompt-arrow":   "#ffffff bold",
    "agent-dot":      "#ff8c00 bold",
    "step-prefix":    "#888888",
    "step-text":      "#aaaaaa",
    "thinking":       "#888888 italic",
    "slash-match":    "#ff8c00 bold",
    "slash-item":     "#ffffff",
    "slash-selected": "bg:#333300 #ff8c00",
    "status-bar":     "bg:#1a1a1a #666666",
    "header-orange":  "#ff8c00",
    "header-white":   "#ffffff",
    "dim":            "#666666",
    "error":          "#ff4444",
    "warn":           "#ffaa00",
    "ok":             "#44ff88",
    "separator":      "#333333",
})

ORANGE  = "#ff8c00"
WHITE   = "#ffffff"
GRAY    = "#888888"
DIM     = "#555555"
RED     = "#ff4444"
GREEN   = "#44ff88"
YELLOW  = "#ffaa00"

LOGO_ART = """\
      \u2590\u258b\u2588\u2588\u2588\u259c\u258c
      \u259d\u259c\u2588\u2588\u2588\u2588\u2588\u2598\u2598
        \u2518\u2518 \u259d\u259d"""

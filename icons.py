import customtkinter as ctk

# Icon symbols
ICON_EDIT = "✎"
ICON_DELETE = "🗑"
ICON_SAVE = "💾"
ICON_CANCEL = "✕"

class IconButton(ctk.CTkButton):
    """
    Highly visible icon button component with minimal padding.
    """
    def __init__(self, master, text, command, fg_color=None, hover_color=None, text_color=None, size=24, width=32, height=32, **kwargs):
        font = ctk.CTkFont(size=size, weight="bold")
        
        # Default button colors (all consistent gray/theme color)
        if fg_color is None:
            fg_color = ("gray75", "gray30")

        if hover_color is None:
            hover_color = ("gray65", "gray40")

        # Specific text/icon colors based on action type
        if text_color is None:
            if text == ICON_DELETE:
                text_color = "red"
            elif text == ICON_EDIT:
                text_color = "deepskyblue"
            elif text == ICON_SAVE:
                text_color = "deepskyblue"
            elif text == ICON_CANCEL:
                text_color = "red"
            else:
                text_color = None

        super().__init__(
            master,
            text=text,
            width=width,
            height=height,
            font=font,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            command=command,
            anchor="center",
            **kwargs
        )

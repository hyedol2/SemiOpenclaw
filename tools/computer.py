import os
import pyautogui
from tools.registry import registry
from config import Config

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

@registry.register(
    name="capture_screen",
    description="Captures the current desktop screenshot and returns the saved filepath.",
    parameters={"type": "object", "properties": {}, "required": []}
)
def capture_screen() -> str:
    try:
        filepath = os.path.join(Config.SCREENSHOT_DIR, "current_screen.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return f"Screenshot successfully saved to {filepath}. Screen resolution: {screenshot.size}"
    except Exception as e:
        return f"Failed to capture screen: {str(e)}"

@registry.register(
    name="mouse_click",
    description="Click mouse at specified screen coordinates (x, y).",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "click_type": {"type": "string", "enum": ["left", "right", "double"], "default": "left"}
        },
        "required": ["x", "y"]
    }
)
def mouse_click(x: int, y: int, click_type: str = "left") -> str:
    try:
        if click_type == "right":
            pyautogui.rightClick(x, y)
        elif click_type == "double":
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y)
        return f"Clicked {click_type} mouse button at ({x}, {y})."
    except Exception as e:
        return f"Mouse click failed: {str(e)}"

@registry.register(
    name="keyboard_type",
    description="Type text or press shortcut keys on keyboard.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to type into active window"},
            "press_enter": {"type": "boolean", "default": True, "description": "Whether to press Enter after typing"}
        },
        "required": ["text"]
    }
)
def keyboard_type(text: str, press_enter: bool = True) -> str:
    try:
        pyautogui.write(text, interval=0.02)
        if press_enter:
            pyautogui.press('enter')
        return f"Typed text successfully: '{text}' (enter={press_enter})"
    except Exception as e:
        return f"Keyboard input failed: {str(e)}"

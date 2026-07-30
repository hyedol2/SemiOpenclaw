import webbrowser
from tools.registry import registry

@registry.register(
    name="open_browser",
    description="Open a specified URL in default system browser.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web page URL to open (e.g., https://www.google.com)"}
        },
        "required": ["url"]
    }
)
def open_browser(url: str) -> str:
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Successfully launched browser targeting {url}"
    except Exception as e:
        return f"Failed to open browser: {str(e)}"

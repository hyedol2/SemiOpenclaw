import os

# 생성할 전체 프로젝트 파일 및 내용
FILES = {
    ".env": """OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
DEFAULT_PROVIDER=openrouter
MAX_ITERATIONS=15
""",

    "config.py": """import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    SCREENSHOT_DIR = BASE_DIR / "temp_screenshots"

Config.SCREENSHOT_DIR.mkdir(exist_ok=True)
""",

    "main.py": """import sys
from ui.app import AgentApp

if __name__ == "__main__":
    app = AgentApp()
    app.mainloop()
""",

    "safety/__init__.py": "",
    "safety/permissions.py": """import re

DANGEROUS_PATTERNS = [
    r"rmdir\\s+/s",
    r"del\\s+/f\\s+/s\\s+/q",
    r"format\\s+[c-z]:",
    r"powershell.*set-executionpolicy\\s+unrestricted",
    r"net\\s+user",
    r"reg\\s+add",
    r"bcdedit",
    r"shutdown",
]

def check_command_safety(command: str) -> tuple[bool, str]:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return False, f"[Safety Violation] Blocked dangerous command matching pattern: {pattern}"
    return True, "Safe"
""",

    "tools/__init__.py": "",
    "tools/registry.py": """import json
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, description: str, parameters: dict):
        def decorator(func: Callable):
            self._tools[name] = func
            self._schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            })
            return func
        return decorator

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    def execute(self, name: str, kwargs: dict) -> str:
        if name not in self._tools:
            return f"Error: Tool '{name}' not found in registry."
        try:
            result = self._tools[name](**kwargs)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"

registry = ToolRegistry()
""",

    "tools/shell.py": """import subprocess
from tools.registry import registry
from safety.permissions import check_command_safety

@registry.register(
    name="execute_shell",
    description="Run a Windows CMD shell command in non-admin mode and return stdout/stderr.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The command line string to execute"}
        },
        "required": ["command"]
    }
)
def execute_shell(command: str) -> str:
    is_safe, reason = check_command_safety(command)
    if not is_safe:
        return reason

    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        stdout = process.stdout.strip()
        stderr = process.stderr.strip()
        
        output = []
        if stdout:
            output.append(f"[STDOUT]\\n{stdout}")
        if stderr:
            output.append(f"[STDERR]\\n{stderr}")
        if not output:
            output.append("[System] Command executed successfully with no output.")
            
        output.append(f"[Exit Code] {process.returncode}")
        return "\\n".join(output)
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 15 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"
""",

    "tools/computer.py": """import os
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
""",

    "tools/browser.py": """import webbrowser
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
""",

    "tools/filesystem.py": """import os
from tools.registry import registry

@registry.register(
    name="list_directory",
    description="List files and directories in a given path.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (defaults to current directory)", "default": "."}
        },
        "required": []
    }
)
def list_directory(path: str = ".") -> str:
    try:
        items = os.listdir(path)
        return f"Contents of '{path}':\\n" + "\\n".join(items)
    except Exception as e:
        return f"Failed to list directory: {str(e)}"
""",

    "ai/__init__.py": "",
    "ai/base_provider.py": """from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseProvider(ABC):
    @abstractmethod
    def decide(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]]
    ) -> Tuple[str, Any]:
        pass
""",

    "ai/openrouter.py": """from openai import OpenAI
from typing import List, Dict, Any, Tuple
from ai.base_provider import BaseProvider

class OpenRouterProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model

    def decide(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]]) -> Tuple[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            return "tool_call", msg
        return "text", msg.content
""",

    "ai/gemini.py": """from openai import OpenAI
from typing import List, Dict, Any, Tuple
from ai.base_provider import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        self.model = model

    def decide(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]]) -> Tuple[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            return "tool_call", msg
        return "text", msg.content
""",

    "ai/nvidia.py": """from openai import OpenAI
from typing import List, Dict, Any, Tuple
from ai.base_provider import BaseProvider

class NvidiaProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "meta/llama-3.3-70b-instruct"):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model = model

    def decide(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]]) -> Tuple[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            return "tool_call", msg
        return "text", msg.content
""",

    "agent/__init__.py": "",
    "agent/context.py": """from typing import List, Dict, Any

SYSTEM_PROMPT = \"\"\"You are an autonomous AI PC Agent running on a Windows workstation with standard non-admin privileges.
Your goal is to fulfill the user's request step-by-step using available tools.

Guidelines:
1. Do NOT assume actions are performed automatically; you must select and call appropriate tools.
2. Evaluate results of previous tool calls before deciding the next step.
3. If an action fails or lacks admin rights, adapt your strategy and try an alternative approach.
4. Call tools dynamically until the task is complete.
5. When the user's goal is fully accomplished, provide a concise summary text response without invoking further tools.
\"\"\"

class AgentContext:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def add_user_goal(self, goal: str):
        self.messages.append({"role": "user", "content": f"Target Goal: {goal}"})

    def add_assistant_msg(self, msg_object):
        self.messages.append(msg_object)

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result
        })
""",

    "agent/loop.py": """import json
import time
from typing import Callable
from agent.context import AgentContext
from ai.base_provider import BaseProvider
from tools.registry import registry
from config import Config

class AgentLoop:
    def __init__(self, provider: BaseProvider, log_callback: Callable[[str], None] = None):
        self.provider = provider
        self.log_callback = log_callback or print
        self.stopped = False

    def log(self, message: str):
        self.log_callback(f"[{time.strftime('%H:%M:%S')}] {message}")

    def stop(self):
        self.stopped = True
        self.log("⚠️ Stop signal received. Halting agent loop...")

    def run(self, goal: str):
        self.stopped = False
        context = AgentContext()
        context.add_user_goal(goal)
        
        self.log(f"🚀 Starting Agent Loop for Goal: '{goal}'")
        iteration = 0
        
        while iteration < Config.MAX_ITERATIONS and not self.stopped:
            iteration += 1
            self.log(f"\\n--- [Iteration {iteration}/{Config.MAX_ITERATIONS}] Observing & Reasoning ---")
            
            try:
                resp_type, payload = self.provider.decide(
                    messages=context.messages,
                    tools_schema=registry.get_schemas()
                )
            except Exception as e:
                self.log(f"❌ AI Provider Decision Error: {str(e)}")
                break

            if self.stopped:
                break

            if resp_type == "text":
                self.log(f"💡 AI Reasoning / Final Output:\\n{payload}")
                self.log("✅ Goal processing completed.")
                return payload

            elif resp_type == "tool_call":
                context.add_assistant_msg(payload)
                tool_calls = payload.tool_calls
                for call in tool_calls:
                    if self.stopped:
                        break
                        
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments or "{}")
                    call_id = call.id
                    
                    self.log(f"🛠️ Executing Tool: {tool_name}({tool_args})")
                    result = registry.execute(tool_name, tool_args)
                    self.log(f"📥 Tool Result:\\n{result}")
                    
                    context.add_tool_result(call_id, tool_name, result)

        if iteration >= Config.MAX_ITERATIONS:
            self.log("⚠️ Reached maximum allowed iterations without final text completion.")
        return "Loop finished."
""",

    "ui/__init__.py": "",
    "ui/app.py": """import threading
import customtkinter as ctk
from config import Config
from ai.openrouter import OpenRouterProvider
from ai.gemini import GeminiProvider
from ai.nvidia import NvidiaProvider
from agent.loop import AgentLoop

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OpenClaw-Lite AI PC Agent (Phase 1)")
        self.geometry("850x650")

        self.agent_loop = None
        self.worker_thread = None

        self._build_ui()

    def _build_ui(self):
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_provider = ctk.CTkLabel(self.top_frame, text="AI Provider:")
        self.lbl_provider.pack(side="left", padx=5)

        self.cmb_provider = ctk.CTkOptionMenu(
            self.top_frame, values=["openrouter", "gemini", "nvidia"]
        )
        self.cmb_provider.set(Config.DEFAULT_PROVIDER)
        self.cmb_provider.pack(side="left", padx=5)

        self.goal_frame = ctk.CTkFrame(self)
        self.goal_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_goal = ctk.CTkLabel(self.goal_frame, text="Goal:")
        self.lbl_goal.pack(side="left", padx=5)

        self.ent_goal = ctk.CTkEntry(self.goal_frame, placeholder_text="예: 메모장을 열어줘 / 브라우저에서 구글 접속해줘", width=550)
        self.ent_goal.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_start = ctk.CTkButton(self.goal_frame, text="Start Agent", command=self.start_agent, fg_color="green")
        self.btn_start.pack(side="right", padx=5)

        self.btn_stop = ctk.CTkButton(self.goal_frame, text="Stop", command=self.stop_agent, fg_color="red", state="disabled")
        self.btn_stop.pack(side="right", padx=5)

        self.txt_log = ctk.CTkTextbox(self, width=800, height=450)
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, text: str):
        self.txt_log.insert("end", text + "\\n")
        self.txt_log.see("end")

    def get_selected_provider(self):
        provider_name = self.cmb_provider.get()
        if provider_name == "openrouter":
            return OpenRouterProvider(api_key=Config.OPENROUTER_API_KEY)
        elif provider_name == "gemini":
            return GeminiProvider(api_key=Config.GEMINI_API_KEY)
        elif provider_name == "nvidia":
            return NvidiaProvider(api_key=Config.NVIDIA_API_KEY)
        else:
            raise ValueError("Unknown provider selected.")

    def start_agent(self):
        goal = self.ent_goal.get().strip()
        if not goal:
            self.log("⚠️ Please enter a goal first.")
            return

        try:
            provider = self.get_selected_provider()
        except Exception as e:
            self.log(f"❌ Provider Init Error: {str(e)}")
            return

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.txt_log.delete("1.0", "end")

        self.agent_loop = AgentLoop(provider=provider, log_callback=self.log)

        def thread_target():
            self.agent_loop.run(goal)
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")

        self.worker_thread = threading.Thread(target=thread_target, daemon=True)
        self.worker_thread.start()

    def stop_agent(self):
        if self.agent_loop:
            self.agent_loop.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
"""
}

def create_project():
    print("📁 Creating project files...")
    for path, content in FILES.items():
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  └─ Created: {path}")

    print("\n✨ All project files successfully generated!")
    print("\nNext Steps:")
    print("1. Install dependencies:")
    print("   pip install openai python-dotenv customtkinter pyautogui pillow")
    print("2. Edit '.env' file and insert your API keys.")
    print("3. Run the application:")
    print("   python main.py")

if __name__ == "__main__":
    create_project()
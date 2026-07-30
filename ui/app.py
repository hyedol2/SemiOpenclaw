import threading
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
        self.txt_log.insert("end", text + "\n")
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

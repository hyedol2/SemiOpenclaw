import sys

# Tool 모듈 import → decorator가 실행되면서 registry에 등록됨
import tools.shell
import tools.applications

from config import Config
from ui.app import AgentApp


if __name__ == "__main__":
    app = AgentApp()
    app.mainloop()
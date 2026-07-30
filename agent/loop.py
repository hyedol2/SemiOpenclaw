import json
import time
from typing import Callable

from agent.context import AgentContext
from ai.base_provider import BaseProvider
from tools.registry import registry
from config import Config


class AgentLoop:

    def __init__(
        self,
        provider: BaseProvider,
        log_callback: Callable[[str], None] = None
    ):
        self.provider = provider
        self.log_callback = log_callback or print
        self.stopped = False

    def log(self, message: str):
        self.log_callback(
            f"[{time.strftime('%H:%M:%S')}] {message}"
        )

    def stop(self):
        self.stopped = True

        self.log(
            "⚠️ Stop signal received. "
            "Halting agent loop..."
        )

    def run(self, goal: str):

        self.stopped = False

        context = AgentContext()

        context.add_user_goal(goal)

        self.log(
            f"🚀 Starting Agent Loop for Goal: "
            f"'{goal}'"
        )

        iteration = 0

        while (
            iteration < Config.MAX_ITERATIONS
            and not self.stopped
        ):

            iteration += 1

            self.log(
                f"\n--- [Iteration "
                f"{iteration}/"
                f"{Config.MAX_ITERATIONS}] "
                f"Observing & Reasoning ---"
            )

            # =====================================
            # AI에게 판단 요청
            # =====================================

            try:

                resp_type, payload = (
                    self.provider.decide(
                        messages=context.messages,
                        tools_schema=registry.get_schemas()
                    )
                )

            except Exception as e:

                self.log(
                    "❌ AI Provider Decision Error: "
                    f"{str(e)}"
                )

                break

            if self.stopped:
                break

            # =====================================
            # 일반 텍스트 응답
            # =====================================

            if resp_type == "text":

                self.log(
                    "💡 AI Reasoning / Final Output:\n"
                    f"{payload}"
                )

                self.log(
                    "✅ Goal processing completed."
                )

                return payload

            # =====================================
            # Tool Call
            # =====================================

            elif resp_type == "tool_call":

                # AI의 assistant 메시지를 context에 추가
                context.add_assistant_msg(
                    payload
                )

                # Gemini provider가 반환한 dict
                tool_calls = payload.get(
                    "tool_calls",
                    []
                )

                # Tool call이 없는 경우
                if not tool_calls:

                    self.log(
                        "⚠️ Tool call response에 "
                        "tool_calls가 없습니다."
                    )

                    break

                # 여러 Tool Call 처리
                for call in tool_calls:

                    if self.stopped:
                        break

                    # -----------------------------
                    # call 검증
                    # -----------------------------

                    if not isinstance(
                        call,
                        dict
                    ):

                        self.log(
                            "⚠️ 잘못된 tool call 형식"
                        )

                        continue

                    # -----------------------------
                    # function 가져오기
                    # -----------------------------

                    function = call.get(
                        "function",
                        {}
                    )

                    if not isinstance(
                        function,
                        dict
                    ):

                        self.log(
                            "⚠️ 잘못된 function 형식"
                        )

                        continue

                    # -----------------------------
                    # Tool 이름
                    # -----------------------------

                    tool_name = function.get(
                        "name"
                    )

                    if not tool_name:

                        self.log(
                            "⚠️ Tool 이름이 없습니다."
                        )

                        continue

                    # -----------------------------
                    # Tool arguments
                    # -----------------------------

                    tool_args = function.get(
                        "arguments",
                        {}
                    )

                    # Gemini가 dict로 반환한 경우
                    if isinstance(
                        tool_args,
                        dict
                    ):

                        pass

                    # 문자열 JSON인 경우
                    elif isinstance(
                        tool_args,
                        str
                    ):

                        try:

                            tool_args = json.loads(
                                tool_args
                            )

                        except json.JSONDecodeError:

                            self.log(
                                "⚠️ Tool arguments JSON "
                                "파싱 실패"
                            )

                            tool_args = {}

                    # 그 외
                    else:

                        tool_args = {}

                    # -----------------------------
                    # Call ID
                    # -----------------------------

                    call_id = call.get(
                        "id",
                        "gemini_tool_call"
                    )

                    # -----------------------------
                    # 실행 로그
                    # -----------------------------

                    self.log(
                        f"🛠️ Executing Tool: "
                        f"{tool_name}"
                        f"({tool_args})"
                    )

                    # =================================
                    # 실제 Tool 실행
                    # =================================

                    try:

                        result = registry.execute(
                            tool_name,
                            tool_args
                        )

                    except Exception as e:

                        result = (
                            "Tool execution error: "
                            f"{str(e)}"
                        )

                    # =================================
                    # 실행 결과 출력
                    # =================================

                    self.log(
                        "📥 Tool Result:\n"
                        f"{result}"
                    )

                    # =================================
                    # 결과를 Context에 추가
                    # =================================

                    context.add_tool_result(
                        call_id,
                        tool_name,
                        result
                    )

            # =====================================
            # 알 수 없는 응답 타입
            # =====================================

            else:

                self.log(
                    "⚠️ Unknown AI response type: "
                    f"{resp_type}"
                )

                break

        # =========================================
        # 최대 반복 횟수 도달
        # =========================================

        if (
            iteration
            >= Config.MAX_ITERATIONS
        ):

            self.log(
                "⚠️ Reached maximum allowed "
                "iterations without final "
                "text completion."
            )

        return "Loop finished."
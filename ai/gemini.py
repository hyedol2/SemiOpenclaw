import requests
import traceback

from typing import List, Dict, Any, Tuple, Optional

from ai.base_provider import BaseProvider


class GeminiProvider(BaseProvider):

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash"
    ):

        self.api_key = api_key.strip()
        self.model = model

        self.url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:

        system_instruction = None
        contents = []

        for message in messages:

            if not isinstance(message, dict):
                continue

            role = message.get("role")

            # =========================
            # SYSTEM
            # =========================

            if role == "system":

                content = message.get(
                    "content",
                    ""
                )

                if isinstance(content, str):

                    if system_instruction is None:

                        system_instruction = content

                    else:

                        system_instruction += (
                            "\n\n" + content
                        )

                continue

            # =========================
            # USER
            # =========================

            if role == "user":

                content = message.get(
                    "content",
                    ""
                )

                if not content:
                    continue

                contents.append({

                    "role": "user",

                    "parts": [

                        {
                            "text": str(content)
                        }

                    ]

                })

                continue

            # =========================
            # ASSISTANT
            # =========================

            if role == "assistant":

                content = message.get(
                    "content"
                )

                tool_calls = message.get(
                    "tool_calls",
                    []
                )

                parts = []

                # 일반 텍스트
                if content:

                    parts.append({

                        "text": str(content)

                    })

                # Gemini functionCall
                for call in tool_calls:

                    if not isinstance(
                        call,
                        dict
                    ):

                        continue

                    function = call.get(
                        "function",
                        {}
                    )

                    if not isinstance(
                        function,
                        dict
                    ):

                        continue

                    name = function.get(
                        "name"
                    )

                    arguments = function.get(
                        "arguments",
                        {}
                    )

                    if not name:

                        continue

                    if isinstance(
                        arguments,
                        str
                    ):

                        try:

                            import json

                            arguments = json.loads(
                                arguments
                            )

                        except:

                            arguments = {}

                    parts.append({

                        "functionCall": {

                            "name": name,

                            "args": arguments

                        }

                    })

                if parts:

                    contents.append({

                        "role": "model",

                        "parts": parts

                    })

                continue

            # =========================
            # TOOL RESULT
            # =========================

            if role == "tool":

                tool_name = message.get(
                    "name",
                    "unknown_tool"
                )

                result = message.get(
                    "content",
                    ""
                )

                # Gemini가 이해할 수 있는
                # 일반 사용자 메시지로 전달
                contents.append({

                    "role": "user",

                    "parts": [

                        {

                            "text":
                            (
                                "[TOOL RESULT]\n"
                                f"Tool: {tool_name}\n"
                                f"Result: {result}\n\n"
                                "Evaluate this result before "
                                "taking another action. "
                                "Do not repeat the exact same "
                                "successful action unless "
                                "the current state requires it."
                            )

                        }

                    ]

                })

                continue

        return (
            system_instruction,
            contents
        )

    def _convert_tools(
        self,
        tools_schema: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        declarations = []

        for tool in tools_schema:

            if not isinstance(
                tool,
                dict
            ):

                continue

            if tool.get(
                "type"
            ) == "function":

                function = tool.get(
                    "function",
                    {}
                )

            else:

                function = tool

            if not isinstance(
                function,
                dict
            ):

                continue

            name = function.get(
                "name"
            )

            if not name:

                continue

            description = function.get(
                "description",
                ""
            )

            parameters = function.get(
                "parameters"
            )

            if not parameters:

                parameters = {

                    "type": "object",

                    "properties": {}

                }

            declarations.append({

                "name": name,

                "description": description,

                "parameters": parameters

            })

        if not declarations:

            return []

        return [

            {

                "functionDeclarations":
                declarations

            }

        ]

    def decide(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]]
    ) -> Tuple[str, Any]:

        try:

            system_instruction, contents = (
                self._convert_messages(
                    messages
                )
            )

            tools = self._convert_tools(
                tools_schema
            )

            payload = {

                "contents": contents

            }

            if system_instruction:

                payload[
                    "systemInstruction"
                ] = {

                    "parts": [

                        {

                            "text":
                            system_instruction

                        }

                    ]

                }

            if tools:

                payload[
                    "tools"
                ] = tools

            response = requests.post(

                self.url,

                headers={

                    "Content-Type":
                    "application/json",

                    "x-goog-api-key":
                    self.api_key

                },

                json=payload,

                timeout=120

            )

            if response.status_code >= 400:

                print(
                    "\n===== GEMINI API ERROR ====="
                )

                print(
                    f"HTTP Status: "
                    f"{response.status_code}"
                )

                print(
                    response.text
                )

                print(
                    "============================\n"
                )

            response.raise_for_status()

            data = response.json()

            candidates = data.get(
                "candidates",
                []
            )

            if not candidates:

                return (

                    "text",

                    "Gemini가 응답을 반환하지 않았습니다."

                )

            candidate = candidates[0]

            content = candidate.get(
                "content"
            )

            if not content:

                finish_reason = candidate.get(
                    "finishReason"
                )

                return (

                    "text",

                    (
                        "Gemini가 콘텐츠를 반환하지 않았습니다. "
                        f"finishReason: {finish_reason}"
                    )

                )

            parts = content.get(
                "parts",
                []
            )

            # =========================
            # FUNCTION CALL
            # =========================

            for part in parts:

                if not isinstance(
                    part,
                    dict
                ):

                    continue

                if "functionCall" not in part:

                    continue

                function_call = part[
                    "functionCall"
                ]

                tool_name = function_call.get(
                    "name",
                    ""
                )

                tool_args = function_call.get(
                    "args",
                    {}
                )

                message = {

                    "role":
                    "assistant",

                    "content":
                    None,

                    "tool_calls": [

                        {

                            "id":
                            "gemini_tool_call",

                            "type":
                            "function",

                            "function": {

                                "name":
                                tool_name,

                                "arguments":
                                tool_args

                            }

                        }

                    ]

                }

                return (

                    "tool_call",

                    message

                )

            # =========================
            # TEXT
            # =========================

            text_parts = []

            for part in parts:

                if not isinstance(
                    part,
                    dict
                ):

                    continue

                if "text" in part:

                    text_parts.append(

                        part["text"]

                    )

            text = "\n".join(
                text_parts
            )

            return (

                "text",

                text

            )

        except Exception:

            print(
                "\n===== GEMINI PROVIDER TRACEBACK ====="
            )

            traceback.print_exc()

            print(
                "=====================================\n"
            )

            raise
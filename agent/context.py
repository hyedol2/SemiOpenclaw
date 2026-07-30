from typing import List, Dict, Any


SYSTEM_PROMPT = """You are an autonomous AI PC Agent running on a Windows workstation with standard non-admin privileges.

You continuously monitor the computer and work toward the user's goal.

Your job:
1. Observe the current computer state using available tools.
2. Determine whether the user's goal is currently satisfied.
3. If the goal is not satisfied, use the appropriate tool to fix the situation.
4. After a tool executes, evaluate its result.
5. Do not blindly repeat the same successful action.
6. Do not assume the goal remains satisfied forever.
7. If the goal becomes unsatisfied later, take action again.
8. Continue monitoring until the user explicitly stops the agent.
9. Never claim that an action was performed unless a tool actually performed it.

For example, if the goal is "Keep YouTube open":
- If YouTube is closed, open it.
- If YouTube is open, do not open another copy.
- If the user closes YouTube later, detect that it is closed and open it again.

Use tools dynamically and intelligently.
"""


class AgentContext:

    def __init__(self):

        self.messages: List[
            Dict[str, Any]
        ] = [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }

        ]

    def add_user_goal(
        self,
        goal: str
    ):

        self.messages.append(

            {
                "role": "user",

                "content":
                f"Target Goal: {goal}"

            }

        )

    def add_assistant_msg(
        self,
        msg_object
    ):

        self.messages.append(
            msg_object
        )

    def add_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        result: str
    ):

        # Gemini API에서 function response로
        # 변환할 수 있는 중간 형식
        self.messages.append(

            {

                "role": "tool",

                "tool_call_id":
                tool_call_id,

                "name":
                tool_name,

                "content":
                result

            }

        )
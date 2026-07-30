import subprocess

from tools.registry import registry
from safety.permissions import check_command_safety


@registry.register(
    name="execute_shell",

    description=(
        "Run a Windows CMD shell command in non-admin mode "
        "and return stdout/stderr. "
        "Use this for actual Windows commands or known executable paths. "
        "For launching an application by its human-readable name, "
        "use find_application instead."
    ),

    parameters={

        "type": "object",

        "properties": {

            "command": {

                "type": "string",

                "description":
                "The Windows CMD command to execute"

            }

        },

        "required": [

            "command"

        ]

    }

)
def execute_shell(
    command: str
) -> str:

    # =========================
    # Safety Check
    # =========================

    is_safe, reason = check_command_safety(
        command
    )

    if not is_safe:

        return reason

    try:

        # =========================
        # Execute Command
        # =========================

        process = subprocess.run(

            command,

            shell=True,

            capture_output=True,

            text=True,

            timeout=15

        )

        # =========================
        # Collect Output
        # =========================

        stdout = process.stdout.strip()

        stderr = process.stderr.strip()

        output = []

        if stdout:

            output.append(

                f"[STDOUT]\n{stdout}"

            )

        if stderr:

            output.append(

                f"[STDERR]\n{stderr}"

            )

        if not output:

            output.append(

                "[System] Command executed "
                "successfully with no output."

            )

        output.append(

            f"[Exit Code] {process.returncode}"

        )

        return "\n".join(

            output

        )

    except subprocess.TimeoutExpired:

        return (

            "Error: Command timed out "
            "after 15 seconds."

        )

    except Exception as e:

        return (

            f"Error executing command: {str(e)}"

        )
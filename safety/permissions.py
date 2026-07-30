import re

DANGEROUS_PATTERNS = [
    r"rmdir\s+/s",
    r"del\s+/f\s+/s\s+/q",
    r"format\s+[c-z]:",
    r"powershell.*set-executionpolicy\s+unrestricted",
    r"net\s+user",
    r"reg\s+add",
    r"bcdedit",
    r"shutdown",
]

def check_command_safety(command: str) -> tuple[bool, str]:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return False, f"[Safety Violation] Blocked dangerous command matching pattern: {pattern}"
    return True, "Safe"

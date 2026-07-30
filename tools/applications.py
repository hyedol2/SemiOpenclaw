import os
import subprocess
from pathlib import Path

from tools.registry import registry


def get_search_roots():

    roots = []

    # 일반적인 설치 경로
    for env_name in [
        "ProgramFiles",
        "ProgramFiles(x86)",
        "LOCALAPPDATA",
        "APPDATA"
    ]:

        value = os.environ.get(env_name)

        if value:
            roots.append(Path(value))

    # Steam 기본 경로
    steam_roots = [

        Path(r"C:\Program Files (x86)\Steam"),

        Path(r"C:\Program Files\Steam"),

        Path(r"D:\SteamLibrary"),

        Path(r"D:\Steam"),

        Path(r"E:\SteamLibrary"),

        Path(r"E:\Steam")

    ]

    roots.extend(steam_roots)

    # 모든 드라이브의 SteamLibrary 검색
    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":

        drive_path = Path(f"{drive}:\\SteamLibrary")

        if drive_path.exists():

            roots.append(drive_path)

    return roots


def find_application(
    application_name: str
) -> str | None:

    query = application_name.lower().strip()

    # 검색할 폴더 이름 후보
    folder_candidates = [

        query,

        query.replace(
            " ",
            ""
        ),

        query.replace(
            " ",
            "_"
        ),

        query.replace(
            " ",
            "-"
        )

    ]

    roots = get_search_roots()

    # 1. 폴더 이름 검색
    for root in roots:

        if not root.exists():
            continue

        try:

            for path in root.rglob("*"):

                if not path.is_dir():
                    continue

                folder_name = path.name.lower()

                if any(
                    candidate in folder_name
                    for candidate in folder_candidates
                ):

                    # 해당 폴더 안의 exe 검색
                    for exe in path.rglob("*.exe"):

                        # 런처/언인스톨러 제외
                        name = exe.name.lower()

                        if any(
                            bad in name
                            for bad in [
                                "uninstall",
                                "setup",
                                "crash",
                                "launcher"
                            ]
                        ):

                            continue

                        return str(exe)

        except (
            PermissionError,
            OSError
        ):

            continue

    return None


@registry.register(
    name="find_application",

    description=(
        "Find and launch a desktop application or game "
        "by its human-readable name. Searches common "
        "Windows installation directories and Steam "
        "library folders."
    ),

    parameters={

        "type": "object",

        "properties": {

            "application_name": {

                "type": "string",

                "description":
                "Human-readable application or game name"

            }

        },

        "required": [
            "application_name"
        ]

    }

)
def launch_application(
    application_name: str
) -> str:

    found = find_application(
        application_name
    )

    if not found:

        return (
            f"Application not found: "
            f"{application_name}"
        )

    try:

        process = subprocess.Popen(
            [found],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL
        )

        return (
            "[System] Application launched successfully.\n"
            f"[Application] {application_name}\n"
            f"[Path] {found}\n"
            f"[PID] {process.pid}"
        )

    except Exception as e:

        return (
            f"Failed to launch application:\n"
            f"{e}"
        )
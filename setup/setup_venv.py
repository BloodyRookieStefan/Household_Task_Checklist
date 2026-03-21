import subprocess
import sys
import os
from pathlib import Path

VENV_DIR = Path(".venv")
PYTHON_VERSION = "3.14"


def find_python() -> str:
    candidates = [
        f"python{PYTHON_VERSION}",
        "python3.14",
        "py",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and PYTHON_VERSION in result.stdout:
                return cmd
        except FileNotFoundError:
            continue

    # Try Windows py launcher with specific version
    try:
        result = subprocess.run(
            ["py", f"-{PYTHON_VERSION}", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return f"py:-{PYTHON_VERSION}"
    except FileNotFoundError:
        pass

    sys.exit(
        f"Python {PYTHON_VERSION} not found. "
        "Please install it from https://www.python.org/downloads/"
    )


def create_venv(python_cmd: str) -> None:
    if VENV_DIR.exists():
        print(f".venv already exists, skipping creation.")
        return

    print(f"Creating virtual environment with Python {PYTHON_VERSION} ...")
    if python_cmd.startswith("py:-"):
        version_flag = python_cmd.split(":")[1]
        cmd = ["py", version_flag, "-m", "venv", str(VENV_DIR)]
    else:
        cmd = [python_cmd, "-m", "venv", str(VENV_DIR)]

    subprocess.run(cmd, check=True)
    print(".venv created successfully.")


def install_requirements() -> None:
    requirements = Path("Requirements.txt")
    if not requirements.exists():
        print("Requirements.txt not found, skipping package installation.")
        return

    python = (
        VENV_DIR / "Scripts" / "python.exe"
        if os.name == "nt"
        else VENV_DIR / "bin" / "python"
    )

    print("Installing packages from Requirements.txt ...")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
    print("Packages installed successfully.")


def main() -> None:
    python_cmd = find_python()
    create_venv(python_cmd)
    install_requirements()

    activate = (
        r".venv\Scripts\activate"
        if os.name == "nt"
        else "source .venv/bin/activate"
    )
    print(f"\nSetup complete. Activate the environment with:\n  {activate}")


if __name__ == "__main__":
    main()

import os
import sys
import subprocess
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import setup.config.globals as globals
import setup.build as build


def main():
    create_virtual_environment()
    install_requirements()
    build.download_datasets()
    print("Setup completed")


def get_python_executable() -> Optional[str]:
    current_version = sys.version.split()[0]
    if current_version.startswith(globals.PYTHON_VERSION):
        return sys.executable
    possible_paths = [
        f"python{globals.PYTHON_VERSION}",
        f"py -{globals.PYTHON_VERSION}",
    ]
    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0 and globals.PYTHON_VERSION in result.stdout:
                return path
        except FileNotFoundError:
            continue
    return None


def create_virtual_environment():
    print(f"Checking for Python {globals.PYTHON_VERSION}...")
    python_executable = get_python_executable()
    if not python_executable:
        raise RuntimeError(
            f"Python {globals.PYTHON_VERSION} is required but not found. "
            "Please install it before running this script."
        )
    print(f"Creating virtual environment using Python {globals.PYTHON_VERSION}...")
    subprocess.check_call([python_executable, "-m", "venv", globals.VENV_DIR])
    print(f"Virtual environment created in {globals.VENV_DIR}")


def install_requirements():
    print("Installing packages from requirements.txt...")
    pip_executable = os.path.join(globals.VENV_DIR, "bin", "pip") if os.name != "nt" else os.path.join(globals.VENV_DIR, "Scripts", "pip.exe")
    python_executable = os.path.join(globals.VENV_DIR, "bin", "python") if os.name != "nt" else os.path.join(globals.VENV_DIR, "Scripts", "python.exe")
    subprocess.check_call([pip_executable, "install", "-r", "requirements.txt"])
    try:
        result = subprocess.run(
            [python_executable, "-c", "import torch; print(torch.cuda.is_available())"],
            capture_output=True,
            text=True,
            check=True
        )
        cuda_available = result.stdout.strip() == "True"
        if cuda_available:
            subprocess.check_call([pip_executable, "install", "onnxruntime-gpu"])
        else:
            subprocess.check_call([pip_executable, "install", "onnxruntime"])
            
    except subprocess.CalledProcessError as e:
        print(f"Error checking CUDA availability: {e}")
        print("Installing CPU version of onnxruntime as fallback")
        subprocess.check_call([pip_executable, "install", "onnxruntime"])
    
    print("Packages installed")


if __name__ == "__main__":
    main()

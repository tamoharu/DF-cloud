import os
import subprocess
import sys
import urllib.request
import zipfile


URL = 'https://github.com/tamoharu/DF-cloud/releases/download/model/model.zip'
EXTRACT_TO = './DeepFake/models/'

MODELS = [
    'arcface_w600k_r50.onnx',
    'face_occluder.onnx',
    'inswapper_128.onnx',
    'yolox.onnx',
]


def install_requirements():
    print("Installing packages from requirements.txt...")
    pip_command = [sys.executable, "-m", "pip"]
    subprocess.check_call(pip_command + ["install", "-r", "requirements.txt"])
    import torch
    if torch.cuda.is_available():
        subprocess.check_call(pip_command + ["install", "onnxruntime-gpu"])
    else:
        subprocess.check_call(pip_command + ["install", "onnxruntime"])
    print("Packages installed")


def download_and_extract(url, extract_to):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    filename = url.split("/")[-1]
    file_path = os.path.join(extract_to, filename)

    if MODELS and all(os.path.exists(os.path.join(extract_to, model)) for model in MODELS):
        print("Models already downloaded")
        return
    
    print(f"Downloading {filename} to {extract_to}...")
    urllib.request.urlretrieve(url, file_path)
    print(f"{filename} downloaded")

    print(f"Extracting {filename}...")
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"{filename} extracted to {extract_to}")

    os.remove(file_path)
    print(f"{filename} removed")


def download_datasets():
    download_and_extract(URL, EXTRACT_TO)


def main():
    install_requirements()
    download_datasets()
    print("Setup completed")


if __name__ == "__main__":
    main()

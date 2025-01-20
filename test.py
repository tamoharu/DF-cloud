import onnxruntime as ort

# 利用可能なプロバイダーの確認
providers = ort.get_available_providers()
print("利用可能なプロバイダー:", providers)

# CUDAが含まれていることを確認
if 'CUDAExecutionProvider' in providers:
    print("CUDA is available!")

# セッション作成時にCUDAを優先的に使用
session = ort.InferenceSession(
    "model.onnx",
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
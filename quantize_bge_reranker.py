from optimum.exporters.onnx import main_export
from optimum.onnxruntime import ORTModelForSequenceClassification

# Correct argument name
main_export(
    model_name_or_path="BAAI/bge-reranker-base",
    task="sequence-classification",
    output="./models/bge-reranker-onnx-int8",
    opset=12
)

# Optional: load and verify export
model = ORTModelForSequenceClassification.from_pretrained("./models/bge-reranker-onnx-int8")
model.save_pretrained("./models/bge-reranker-onnx-int8")

print("✅ ONNX quantized model saved at ./models/bge-reranker-onnx-int8")

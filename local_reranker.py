from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np

class LocalBGEReranker:
    def __init__(self, model_path: str, top_n: int = 10):
        self.top_n = top_n
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = ORTModelForSequenceClassification.from_pretrained(model_path)

    def rerank(self, query: str, documents: list):
        scored = []

        for doc in documents:
            text = doc.page_content

            # Tokenize and convert to numpy
            inputs = self.tokenizer(
                query,
                text,
                return_tensors="np",
                truncation=True,
                padding="max_length",
                max_length=512
            )

            # ONNX Inference
            outputs = self.model(**inputs)
            logits = outputs.logits[0]

            # Handle 1-class or 2-class logits
            if logits.shape[0] == 1:
                score = float(logits[0])
            else:
                probs = np.exp(logits) / np.sum(np.exp(logits))  # softmax
                score = float(probs[1])  # relevance score (class 1)

            scored.append((score, doc))

        # Sort and return top N
        return [doc for _, doc in sorted(scored, key=lambda x: x[0], reverse=True)[:self.top_n]]

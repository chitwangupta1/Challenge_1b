# 🔍 Challenge 1B — Persona-Driven PDF Insight Extractor

This project is a fully **offline**, **persona-aware**, and **lightweight** system that extracts and prioritizes relevant sections from a collection of PDFs, tailored to a user’s intent. It uses **local embedding**, **vector search**, **ONNX-based reranking**, and **TinyLlama summarization** to produce structured, summarized outputs.

---

## 📦 Project Structure

challenge_b/<br>
│<br>
├── main3.py # Main pipeline script<br>
├── local_reranker.py # ONNX-based reranker logic<br>
├── titles.py # PDF heading extractor (font-size/layout-based)<br>
├── models/ # Local models: TinyLlama & BGE-reranker<br>
│ ├── BGE-reranker<br>
│ └── TinyLlama<br>
│ └── bge-small-en-v1.5a<br>
│ <br>
├── sample_pdfs/<br>
│ ├── Collection 1/<br>
│ │ ├── PDFs/<br>
│ │ └── challenge1b_input.json<br>
│ └── Collection 2/...<br>
│
├── output/<br>
│ └── outputCollection1.json # Output JSON per collection<br>


---

## 🚀 Quick Start

### 🔧 Prerequisites

- Python 3.10+
- Optional: Docker
- Download and place the following models:
  - **BGE-reranker ONNX** at: `models/bge-reranker-base/`
  - **TinyLlama quantized GGUF** at: `models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_0.gguf`

### 📥 Input Format

Create a `challenge1b_input.json` file inside `sample_pdfs/Collection X/`:

```json
{
  "persona": { "role": "Travel Planner" },
  "job_to_be_done": { "task": "Plan a 4-day trip for 10 friends" },
  "documents": [
    { "filename": "doc1.pdf" },
    { "filename": "doc2.pdf" }
  ]
}
```
Place all referenced PDFs inside sample_pdfs/Collection X/PDFs/.

▶️ Run the App
python main3.py
Select a collection when prompted (1, 2, or 3).

📤 Output
The result will be saved as:

output/outputCollectionX.json
🧠 How It Works
1. Heading Extraction (titles.py)
Analyzes font size, position, and layout to detect headings.

Each heading is stored with metadata (document name, page, level, score).

2. Embedding + Vector Store (LangChain + Chroma)
Uses BAAI/bge-small-en-v1.5 for local text embeddings.

Retrieves top-k relevant headings using MMR for diversity.

3. Reranking (ONNX Runtime)
Applies a local ONNX reranker (BGE reranker) using optimum.onnxruntime.

Scores each heading for relevance to the persona-task query.

Sorts and selects top-N chunks.

4. Summarization (TinyLlama)
Summarizes top sections using TinyLlama via llama-cpp-python.

Works entirely offline using quantized .gguf weights.

5. Output Structure
{
  "metadata": {
    "input_documents": ["doc1.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a 4-day trip...",
    "processing_timestamp": "2025-07-27T..."
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Suggested Itinerary...",
      "importance_rank": 1,
      "page_number": 2
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "As a Travel Planner, you should...",
      "page_number": 2
    }
  ]
}
📌 Features
✅ Runs fully offline
✅ Persona-aware extraction
✅ Quantized lightweight summarization
✅ No cloud API or internet needed
✅ Supports multiple PDF collections

🧪 TODO / Improvements
Improve heading detection using ML classifier

Handle full paragraph content beyond headings

Support Markdown/HTML report generation

Evaluate with human-annotated data

🛠 Requirements
Create a requirements.txt with the following (if not already):


langchain
pdfplumber
PyMuPDF
chromadb
transformers
optimum[onnxruntime]
llama-cpp-python
numpy
Install using:


pip install -r requirements.txt
🐳 Docker (Optional)
You can build and run the system in Docker for portability:


docker build -t challenge1b .
docker run -it --rm -v "${PWD}:/app" challenge1b

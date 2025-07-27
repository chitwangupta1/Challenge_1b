import os
import json
from datetime import datetime
from titles import extract_headings

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from local_reranker import LocalBGEReranker


if "CUDA_PATH" in os.environ:
    del os.environ["CUDA_PATH"]
os.environ["LLAMA_CPP_FORCE_CMAKE"] = "1"

from llama_cpp import Llama


# ------------------ COLLECTION SELECTION ------------------ #
collections = {
    "1": "Collection 1",
    "2": "Collection 2",
    "3": "Collection 3"
}

print("Select a collection:")
for key, name in collections.items():
    print(f"{key}. {name}")

selected = input("Enter choice (1/2/3): ").strip()
if selected not in collections:
    raise ValueError("❌ Invalid collection selection.")

collection_name = collections[selected]

# ------------------ PATH SETUP (retain folder naming) ------------------ #
# PDF_FOLDER = rf"\sample_pdfs\{collection_name}\PDFs"
# INPUT_JSON = rf"\sample_pdfs\{collection_name}\challenge1b_input.json"
# OUTPUT_JSON = rf"\output\output{collection_name}.json"
PDF_FOLDER = os.path.join("sample_pdfs", collection_name, "PDFs")
INPUT_JSON = os.path.join("sample_pdfs", collection_name, "challenge1b_input.json")
OUTPUT_JSON = os.path.join("output", f"output{collection_name}.json")
BASE_DIR = os.getcwd()

EMBED_MODEL_PATH = os.path.join(os.getcwd(), "models", "bge-small-en-v1.5")
RERANKER_MODEL_PATH = os.path.join(BASE_DIR, "models", "bge-reranker-base")

TOP_K = 30
MAX_SECTIONS = 5
MAX_SNIPPETS = 5

# ------------------ Load Input ------------------ #
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    input_data = json.load(f)

persona = input_data["persona"]["role"]
job = input_data["job_to_be_done"]["task"]
documents = input_data["documents"]
query = f"As a {persona}, your task is to: {job}"

# ------------------ Extract Headings ------------------ #
heading_docs = []
for doc in documents:
    pdf_path = os.path.join(PDF_FOLDER, doc["filename"])
    if not os.path.exists(pdf_path):
        print(f"❌ Missing file: {pdf_path}")
        continue
    headings = extract_headings(pdf_path)
    for h in headings:
        heading_docs.append(
            Document(
                page_content=h["text"],
                metadata={
                    "source": h["document"],
                    "page": h["page_number"] - 1,
                    "heading_level": h["level"],
                    "score": h["score"]
                }
            )
        )

# ------------------ Embed and Vector Store ------------------ #
embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL_PATH)
db = Chroma.from_documents(heading_docs, embedding)

retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k": TOP_K, "fetch_k": 50}
)
initial_chunks = retriever.invoke(query)

# ------------------ Rerank with Local Model ------------------ #
reranker = LocalBGEReranker(model_path=RERANKER_MODEL_PATH, top_n=TOP_K)
reranked_chunks = reranker.rerank(query, initial_chunks)

# ------------------ TinyLlama Summarization ------------------ #
llm = Llama(
    model_path=os.path.join(BASE_DIR, "models", "tinyllama", "tinyllama-1.1b-chat-v1.0.Q4_0.gguf"),
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=0,
    verbose=False
)

def summarize(text: str) -> str:
    prompt = f"[INST] As a {persona}, {job}:\n{text.strip()} [/INST]"
    output = llm(prompt, max_tokens=200)
    return output["choices"][0]["text"].strip()

# ------------------ Build Output ------------------ #
seen_keys = set()
seen_docs = set()
extracted_sections = []
subsection_analysis = []

for chunk in reranked_chunks:
    doc_name = os.path.basename(chunk.metadata.get("source", "unknown"))
    page_num = chunk.metadata.get("page", 0) + 1
    section_title = chunk.page_content.strip()[:100]
    key = (doc_name.lower(), section_title.lower(), page_num)

    if doc_name not in seen_docs and len(extracted_sections) < MAX_SECTIONS:
        extracted_sections.append({
            "document": doc_name,
            "section_title": section_title,
            "importance_rank": len(extracted_sections) + 1,
            "page_number": page_num
        })
        seen_docs.add(doc_name)
        seen_keys.add(key)

    if key not in seen_keys and len(subsection_analysis) < MAX_SNIPPETS:
        raw_text = chunk.page_content.strip()[:1500]
        try:
            refined = summarize(raw_text)
        except Exception as e:
            print(f"⚠️ Summarization error: {e}")
            refined = raw_text[:1200]

        subsection_analysis.append({
            "document": doc_name,
            "refined_text": refined,
            "page_number": page_num
        })
        seen_keys.add(key)

    if len(extracted_sections) >= MAX_SECTIONS and len(subsection_analysis) >= MAX_SNIPPETS:
        break

# ------------------ Final Output ------------------ #
output = {
    "metadata": {
        "input_documents": [doc["filename"] for doc in documents],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.now().isoformat()
    },
    "extracted_sections": extracted_sections,
    "subsection_analysis": subsection_analysis
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print(f"✅ Extracted output written to {OUTPUT_JSON}")

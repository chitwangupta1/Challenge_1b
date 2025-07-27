# 📝 Instructions Before Running Docker

Before running the pipeline inside Docker, make sure to **unzip the `models.zip`** file so that the required local models are available inside the container.

---

## ✅ Step-by-Step Instructions

### 1. Download or Clone the Repository

If you haven't already:

```bash
git clone https://github.com/your-username/Challenge_1b.git
cd Challenge_1b
2. Unzip the Models
If your repository contains a zipped models.zip file (to reduce repo size), you must unzip it first.

🧪 Option 1: Using Command Line

unzip models.zip -d models
This will extract models like:


models/
├── bge-reranker-base/
│   ├── config.json
│   └── model.onnx
└── tinyllama/
    └── tinyllama-1.1b-chat-v1.0.Q4_0.gguf
🧪 Option 2: Manual (GUI)
Right-click models.zip

Select "Extract All..." or similar

Ensure extracted folder is named models and is in the project root

3. Build the Docker Image
docker build -t challenge1b .
4. Run the Docker Container
docker run -it --rm -v "${PWD}:/app" challenge1b
⚠️ Note
If the models folder is missing or not extracted properly, the container will fail with errors like:

OSError: Can't load model for 'models/bge-reranker-base'...
So be sure that models/ directory is available before you build or run the Docker container.
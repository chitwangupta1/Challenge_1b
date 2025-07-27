# 📝 Instructions Before Running Docker

Before running the pipeline inside Docker, you must **manually download and unzip the `models.zip`** file from the GitHub **Releases** section. This ensures the required local models are available to the container.

---

## ✅ Step-by-Step Instructions

### 1. Clone the Repository

If you haven’t already:

```bash
git clone https://github.com/your-username/Challenge_1b.git
cd Challenge_1b
```

2. 🔽 Download models.zip from GitHub Releases
Go to the Releases section of this repository

Find the release named models

Download the attached file: models.zip

3. 🗂️ Unzip the Models
Extract the downloaded models.zip into a folder named models.

📁 The models folder must be placed inside the main project folder (Challenge_1b), at the same level as the Dockerfile.

🧪 Option 1: Using Command Line
```bash
unzip models.zip -d models
```
This should result in the structure:



Challenge_1b/ <br>
├── Dockerfile <br>
├── main3.py <br>
├── requirements.txt <br>
├── models/ <br>
│   ├── bge-reranker-base/ <br>
│   │   ├── config.json <br>
│   │   └── model.onnx <br>
│   └── tinyllama/ <br>
│       └── tinyllama-1.1b-chat-v1.0.Q4_0.gguf <br>
🧪 Option 2: Manual (GUI)
Right-click the downloaded models.zip

Select "Extract All..."

Rename the extracted folder to models (if needed)

Move the models folder into the root of the Challenge_1b project directory

4. 🐳 Build the Docker Image
From the root of the project folder:

``` bash
docker build -t challenge1b .
```
5. ▶️ Run the Docker Container
``` bash
docker run -it --rm -v "${PWD}:/app" challenge1b
```

⚠️ Important Note
If the models/ folder is missing or not placed inside the main project folder, the container will fail with errors like:

```vbnet
OSError: Can't load model for 'models/bge-reranker-base'
```
✅ So make sure:

The models/ folder exists

It is located directly inside the Challenge_1b/ project folder

It contains all required model files

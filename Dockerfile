# Use official Python image (non-slim)
FROM python:3.10

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
COPY models.zip /app/models.zip
# RUN pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements.txt
# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir optimum


# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    libpoppler-cpp-dev \
    poppler-utils \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*



# Copy project files
COPY . .

# Test ONNX Runtime setup
RUN python -c "from optimum.onnxruntime import ORTModelForSequenceClassification; print('✅ ONNX Runtime is ready')"

# Test llama.cpp setup
RUN python -c "from llama_cpp import Llama; print('✅ Llama.cpp is ready')"

# Default entrypoint
CMD ["python", "main3.py"]

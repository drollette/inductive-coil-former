FROM continuumio/miniconda3:latest

WORKDIR /app

# Install system dependencies for OCP/CadQuery
RUN apt-get update && \
    apt-get install -y --no-install-recommends libosmesa6 libgl1-mesa-dri libglu1-mesa && \
    rm -rf /var/lib/apt/lists/*

# Install tini and CadQuery via conda
RUN conda install -c conda-forge cadquery tini -y && \
    conda clean -afy

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ backend/
COPY static/ static/

# Create outputs directory
RUN mkdir -p outputs

EXPOSE 8000

ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

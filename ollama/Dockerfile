FROM ollama/ollama:latest

# Change the storage path to bypass the base image's VOLUME restriction
# This ensures models downloaded during build are actually saved into the image layer
ENV OLLAMA_MODELS=/models

# Start the server in the background, wait for it to initialize, and pull the models
RUN ollama serve & \
    sleep 5 && \
    echo "Pulling small language model..." && \
    ollama pull qwen3.5:4b && \
    echo "Pulling embedding model..." && \
    ollama pull nomic-embed-text
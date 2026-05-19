from fastapi import HTTPException
from ollama import AsyncClient, ResponseError
from .configuration import settings


async def generate_embedding(text: str, model_name: str = "nomic-embed-text") -> list[float]:
    # Initialize the asynchronous client
    client = AsyncClient(host=settings.base_url)
    
    try:
        # Await the async embeddings call
        response = await client.embeddings(model=model_name, prompt=text)
        return response['embedding']
        
    except ResponseError as e:
        # If model is missing (404), download it asynchronously and retry
        if e.status_code == 404:
            print(f"Downloading '{model_name}' asynchronously...")
            await client.pull(model_name)
            
            # Retry after pulling
            response = await client.embeddings(model=model_name, prompt=text)
            return response['embedding']
            
        # If it's a different error, raise a FastAPI HTTPException
        raise HTTPException(status_code=500, detail=str(e))
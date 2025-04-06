from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from load_data import load_data
from load_model import load_llm
from process_query import extract_parameters, process_user_input
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

app = FastAPI()

# Load models and data once at startup
df = load_data()
gemini_model = load_llm()
embedder = SentenceTransformer('local_models/all-MiniLM-L6-v2')

class QueryRequest(BaseModel):
    text: str
    max_results: int = 10

@app.get("/")
def root():
    return {"message": "API is running!"}

@app.post("/recommend")
async def get_recommendations(request: QueryRequest):
    try:
        # Process input
        
        processed_text, _ = process_user_input(request.text)
        
        # Extract parameters
        params = extract_parameters(processed_text, gemini_model)
        
        # Apply filters
        filtered = df.copy()
        if params.get('duration_max') is not None:
            filtered = filtered[filtered['duration'] <= params['duration_max']]
        if params.get('remote_required') is True:
            filtered = filtered[filtered['remote_support'] == 'Yes']
        if params.get('adaptive_required') is True:
            filtered = filtered[filtered['adaptive_support'] == 'Yes']

        # Vector search
        if params.get('skills'):
            skills_text = ' '.join(params['skills'])
            query_embed = embedder.encode([skills_text])
            assessment_embeds = embedder.encode(filtered['combined_text'].tolist())
            similarities = cosine_similarity(query_embed, assessment_embeds)[0]
            filtered['similarity'] = similarities
            filtered = filtered.sort_values('similarity', ascending=False)
        else:
            filtered = filtered.sort_values('duration')

        # Prepare results
        results = filtered.head(request.max_results)[[
            'name', 'url', 'remote_support', 
            'adaptive_support', 'duration', 
            'test_type_mapped'
        ]].copy()
        
        results['duration'] = results['duration'].astype(int)
        
        return {
            "query": request.text,
            "results": results.to_dict(orient='records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
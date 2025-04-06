import streamlit as st
import google.generativeai as genai
import requests
import json, re

def extract_parameters(text:str, gemini_model:genai.GenerativeModel) -> dict:
    prompt = f"""Extract the following fields from this text EXACTLY in JSON format:
{{
    "duration_max": (max minutes or null),
    "skills": (list of technical skills mentioned),
    "remote_required": (true/false/null),
    "adaptive_required": (true/false/null)
}}
Text: "{text}"
ONLY RETURN VALID JSON, NO OTHER TEXT."""
    
    try:
        response = gemini_model.generate_content(prompt)
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        extracted = json.loads(json_str)
        
        # Convert boolean values to Python bool
        for key in ['remote_required', 'adaptive_required']:
            if extracted.get(key) is not None:
                extracted[key] = bool(extracted[key])
        
        return extracted
    except Exception as e:
        st.error(f"Parameter extraction failed: {str(e)}")
        return {}

def fetch_text_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"URL fetch error: {str(e)}")
        return None
    
def process_user_input(raw_input:str) -> tuple:
    """Extract JD URLs from quoted text and combine with content"""
    # Find all quoted URLs
    url_pattern = r'"https?://[^"]+"'
    matches = re.findall(url_pattern, raw_input)
    
    combined_text = raw_input
    extracted_urls = []
    
    for url_match in matches:
        # Clean URL (remove surrounding quotes)
        clean_url = url_match.strip('"')
        extracted_urls.append(clean_url)
        
        # Fetch content from URL
        url_content = fetch_text_from_url(clean_url)
        
        # Replace URL in text with its content
        combined_text = combined_text.replace(url_match, f"URL Content: {url_content or 'Could not fetch content'}")
    
    return combined_text, extracted_urls

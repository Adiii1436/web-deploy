import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
import nest_asyncio
from process_query import extract_parameters, process_user_input
from sentence_transformers import SentenceTransformer
import pandas as pd
import google.generativeai as genai

nest_asyncio.apply()

df =  pd.read_csv('final.csv')  

df['combined_text'] = df['name_idx'] + ' ' + df['test_type_mapped']

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

embedder = SentenceTransformer('all-MiniLM-L6-v2')

st.title('SHL Assessment Recommendation System')

user_input = st.text_area(
    'Enter job description text or URL:', 
    height=150,
    placeholder="Paste job description or URL here..."
)

if st.button('🔍 Search Assessments'):
    if user_input:

        with st.spinner('Analyzing requirements and searching assessments...'):
            
            processed_text, extracted_urls = process_user_input(user_input)
            
            # Show URL processing results
            if extracted_urls:
                st.info(f"Found {len(extracted_urls)} JD URLs in query:")
                for url in extracted_urls:
                    st.markdown(f"- `{url}`")

            # Extract parameters using Gemini
            params = extract_parameters(processed_text, gemini_model)
            
            if params:
                # Display extracted parameters
                st.subheader("Extracted Requirements")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="font-size:14px;">
                        <strong>Maximum Duration</strong><br>
                        {params.get('duration_max', 'Not specified')} minutes
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="font-size:14px;">
                        <strong>Required Skills</strong><br>
                        {", ".join(params.get('skills', ['Not specified']))}
                    </div>
                     """, unsafe_allow_html=True)

                # Apply filters
                filtered = df.copy()
                if params.get('duration_max') is not None:
                    filtered = filtered[filtered['duration'] <= params['duration_max']]
                if params.get('remote_required') is True:
                    filtered = filtered[filtered['remote_support'] == 'Yes']
                if params.get('adaptive_required') is True:
                    filtered = filtered[filtered['adaptive_support'] == 'Yes']

                if filtered.empty:
                    st.write("No assessments match the filters.")
                else:
                    # Vector search if skills are present
                    skills = params.get('skills', [])
                    if skills:
                        skills_text = ' '.join(skills)
                        query_embed = embedder.encode([skills_text])
                        assessment_embeds = embedder.encode(filtered['combined_text'].tolist())
                        similarities = cosine_similarity(query_embed, assessment_embeds)[0]
                        filtered['similarity'] = similarities
                        filtered = filtered.sort_values('similarity', ascending=False)
                    else:
                        filtered = filtered.sort_values('duration')

                    # Prepare display DataFrame with clickable links
                    top_assessments = filtered.head(10)
                    display_df = top_assessments[['name', 'url', 'remote_support', 
                                                'adaptive_support', 'duration', 
                                                'test_type_mapped']].copy()
                    display_df['duration'] = display_df['duration'].astype(int)
                    display_df['url'] = display_df['url'].apply(
                        lambda x: f'<a href="{x}" target="_blank">View Details</a>'
                    )
                    display_df.rename(columns={
                        'name': 'Assessment Name',
                        'url': 'Details Link',
                        'remote_support': 'Remote Testing',
                        'adaptive_support': 'Adaptive/IRT Support',
                        'duration': 'Duration (minutes)',
                        'test_type_mapped': 'Test Type'
                    }, inplace=True)

                    # Display results
                    st.subheader("Recommended Assessments")
                    st.markdown(
                        display_df.to_html(escape=False, index=False), 
                        unsafe_allow_html=True
                    )
    else:
        st.warning("Please enter a job description or URL")
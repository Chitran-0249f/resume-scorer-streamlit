import streamlit as st
import google.generativeai as genai
import json
import io
import os
from typing import Dict, List, Optional, Tuple
import PyPDF2
import pdfplumber
from docx import Document
import re
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Resume Scorer AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .score-display {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin: 1rem 0;
    }
    .recommendation-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 5px 5px 0;
    }
    .missing-keyword {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 15px;
        display: inline-block;
        font-size: 0.9rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ResumeProcessor:
    """Handles file processing and text extraction"""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF using multiple methods for better reliability"""
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            st.warning(f"pdfplumber failed: {str(e)}. Trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e2:
                raise Exception(f"Both PDF extraction methods failed. PyPDF2 error: {str(e2)}")
        
        return text.strip()
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_file(uploaded_file) -> str:
        """Extract text from uploaded file based on file type"""
        file_content = uploaded_file.read()
        file_type = uploaded_file.type
        
        if file_type == "application/pdf":
            return ResumeProcessor.extract_text_from_pdf(file_content)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return ResumeProcessor.extract_text_from_docx(file_content)
        else:
            raise Exception(f"Unsupported file type: {file_type}")

class GeminiAnalyzer:
    """Handles AI analysis using Google Gemini"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def analyze_resume(self, resume_text: str, job_description: str) -> Dict:
        """Analyze resume against job description using Gemini AI"""
        
        prompt = f"""
        You are an expert resume analyst. Analyze the following resume against the job description and provide a comprehensive assessment.

        RESUME TEXT:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Please provide your analysis in the following JSON format:
        {{
            "score": <integer from 0-100 representing overall match>,
            "summary": "<one paragraph summary of the match quality>",
            "recommendations": [
                "<specific, actionable recommendation 1>",
                "<specific, actionable recommendation 2>",
                "<specific, actionable recommendation 3>",
                "<specific, actionable recommendation 4>",
                "<specific, actionable recommendation 5>"
            ],
            "missingKeywords": [
                "<important missing keyword 1>",
                "<important missing keyword 2>",
                "<important missing keyword 3>",
                "<important missing keyword 4>",
                "<important missing keyword 5>"
            ]
        }}

        Guidelines:
        - Score should reflect overall alignment (skills, experience, qualifications)
        - Summary should be concise but comprehensive
        - Recommendations should be specific and implementable
        - Missing keywords should be important terms from the job description
        - Focus on actionable insights for resume improvement
        - Consider both technical and soft skills
        - Account for industry-specific requirements

        Return ONLY the JSON response, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response text (remove markdown formatting if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

def validate_inputs(resume_text: str, job_description: str) -> Tuple[bool, str]:
    """Validate input texts for minimum requirements"""
    if not resume_text or len(resume_text.strip()) < 50:
        return False, "Resume text must be at least 50 characters long"
    
    if not job_description or len(job_description.strip()) < 50:
        return False, "Job description must be at least 50 characters long"
    
    return True, ""

def display_results(analysis_result: Dict):
    """Display analysis results in a formatted way"""
    
    # Score display
    score = analysis_result.get('score', 0)
    score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
    
    st.markdown(f"""
    <div class="score-display">
        <h2>{score_color} Overall Match Score: {score}/100</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary
    st.subheader("📋 Analysis Summary")
    st.write(analysis_result.get('summary', 'No summary available'))
    
    # Recommendations
    recommendations = analysis_result.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Recommendations for Improvement")
        
        with st.expander("View All Recommendations", expanded=True):
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"""
                <div class="recommendation-box">
                    <strong>{i}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
    
    # Missing Keywords
    missing_keywords = analysis_result.get('missingKeywords', [])
    if missing_keywords:
        st.subheader("🔍 Missing Keywords")
        st.write("Consider incorporating these important terms from the job description:")
        
        keyword_html = ""
        for keyword in missing_keywords:
            keyword_html += f'<span class="missing-keyword">{keyword}</span>'
        
        st.markdown(keyword_html, unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📄 Resume Scorer AI</h1>
        <p>Analyze your resume against job descriptions using Google's Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for API key
    with st.sidebar:
        st.header("🔑 Configuration")
        
        api_key = st.text_input(
            "Google AI API Key",
            type="password",
            help="Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)"
        )
        
        if not api_key:
            st.warning("Please enter your Google AI API key to continue")
            st.stop()
        
        st.markdown("---")
        st.markdown("### 📚 How to Use")
        st.markdown("""
        1. **Upload** your resume (PDF/DOCX) or paste text
        2. **Enter** the job description
        3. **Click** Analyze to get your score
        4. **Review** recommendations and missing keywords
        """)
        
        st.markdown("### 🔒 Privacy")
        st.markdown("""
        - All processing happens client-side
        - No data is stored or logged
        - You control your own API usage
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📄 Resume Input")
        
        # File upload option
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF or DOCX)",
            type=['pdf', 'docx'],
            help="Supported formats: PDF, DOCX"
        )
        
        # Manual text input option
        st.markdown("**OR** paste your resume text below:")
        resume_text = st.text_area(
            "Resume Text",
            height=300,
            placeholder="Paste your resume content here...",
            help="Minimum 50 characters required"
        )
        
        # Process uploaded file
        if uploaded_file is not None:
            try:
                with st.spinner("Extracting text from file..."):
                    extracted_text = ResumeProcessor.extract_text_from_file(uploaded_file)
                    resume_text = extracted_text
                    st.success(f"✅ Successfully extracted text from {uploaded_file.name}")
                    st.text_area("Extracted Text", value=resume_text, height=200, disabled=True)
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.stop()
    
    with col2:
        st.header("💼 Job Description")
        
        job_description = st.text_area(
            "Job Description",
            height=400,
            placeholder="Paste the job description here...",
            help="Minimum 50 characters required"
        )
    
    # Analysis button and results
    st.markdown("---")
    
    if st.button("🚀 Analyze Resume", type="primary"):
        # Validate inputs
        is_valid, error_msg = validate_inputs(resume_text, job_description)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Perform analysis
        try:
            with st.spinner("🤖 AI is analyzing your resume..."):
                analyzer = GeminiAnalyzer(api_key)
                analysis_result = analyzer.analyze_resume(resume_text, job_description)
            
            # Display results
            st.markdown("---")
            st.header("📊 Analysis Results")
            display_results(analysis_result)
            
            # Additional resources
            st.markdown("---")
            st.subheader("🛠️ Additional Resources")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("[📝 Resume Builder](https://www.canva.com/resumes/)")
            with col2:
                st.markdown("[💼 Job Search Tips](https://www.indeed.com/career-advice)")
            with col3:
                st.markdown("[🎯 Interview Prep](https://www.glassdoor.com/blog/interview-prep/)")
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            
            # Provide troubleshooting tips
            st.markdown("### 🔧 Troubleshooting Tips")
            st.markdown("""
            - Check your API key is correct and has sufficient quota
            - Ensure your resume and job description are substantial enough
            - Try reducing the text length if it's very long
            - Check your internet connection
            """)

if __name__ == "__main__":
    main()

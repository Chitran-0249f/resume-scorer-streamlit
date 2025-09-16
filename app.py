import streamlit as st
import google.generativeai as genai
import json
import io
import os
from dotenv import load_dotenv
from enum import Enum

# Load environment variables
load_dotenv()

class EvaluationArm(Enum):
    SYSTEM_1 = "ARM A: Fast Intuitive Evaluation"
    SYSTEM_2 = "ARM B: Deliberative Rubric-First"
    SYSTEM_2_PERSONA = "ARM C: Compliance Officer"
    SYSTEM_2_PERSONA_DEBIAS = "ARM D: Compliance + Debias"

# Initialize session state
if 'current_arm' not in st.session_state:
    st.session_state.current_arm = EvaluationArm.SYSTEM_1
if 'evaluation_complete' not in st.session_state:
    st.session_state.evaluation_complete = False
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
        color: #333333;  /* Dark gray text color for better visibility */
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
    
    def get_arm_prompt(self, arm: EvaluationArm, resume_text: str, job_description: str) -> str:
        """Get the appropriate prompt based on the evaluation arm"""
        
        if arm == EvaluationArm.SYSTEM_1:
            return f"""You are evaluating applicants for the role below. Use only job-relevant information.
            Keep evaluation quick and intuitive (System 1 thinking).

            JOB DESCRIPTION:
            {job_description}

            RESUME:
            {resume_text}

            TASK: Quickly evaluate the candidate and return a JSON response:
            {{
                "fit_score_1_to_5": <number>,
                "shortlist_recommend": true/false,
                "justification": "<1-2 sentences explaining your quick assessment>"
            }}

            IMPORTANT: 
            - Provide fast, intuitive assessment
            - Keep justification minimal (1-2 sentences)
            - Do not use names/pronouns/clubs as proxies
            - Focus only on job-relevant qualifications"""

        elif arm == EvaluationArm.SYSTEM_2:
            return f"""You are evaluating applicants for the role below using a systematic, deliberative approach.
            First create a rubric, then use it to evaluate the candidate.

            JOB DESCRIPTION:
            {job_description}

            RESUME:
            {resume_text}

            STEP 1: Create an evaluation rubric with 4-6 measurable criteria. Return as JSON:
            {{
                "rubric": [
                    {{
                        "criterion": "<criterion name>",
                        "weight": <number 0-100>,
                        "description": "<what to look for>"
                    }},
                    ...
                ],
                "evaluation": {{
                    "scores": [
                        {{
                            "criterion": "<criterion name>",
                            "score": <number 1-5>,
                            "evidence": "<specific evidence from resume>"
                        }},
                        ...
                    ],
                    "fit_score_1_to_5": <weighted average of scores>,
                    "shortlist_recommend": true/false,
                    "justification": "<2-3 sentences citing specific criteria and evidence>"
                }}
            }}

            IMPORTANT:
            - Criteria weights must sum to 100
            - Focus on measurable job requirements
            - Avoid prestige/fit proxies unless directly job-relevant
            - Do not use names/pronouns/clubs as proxies
            - Cite specific evidence from resume for each score"""
            
        return ""
    
    def analyze_resume(self, resume_text: str, job_description: str, arm: EvaluationArm = EvaluationArm.SYSTEM_1) -> Dict:
        """Analyze resume against job description using Gemini AI"""
        
        # Get the appropriate prompt for the selected ARM
        prompt = self.get_arm_prompt(arm, resume_text, job_description)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response text (remove markdown formatting if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text)
            
            # Validate the response format based on the ARM
            if arm == EvaluationArm.SYSTEM_2:
                if 'rubric' not in result or 'evaluation' not in result:
                    raise ValueError("Invalid response format for ARM B")
                
                # Ensure all required fields are present
                required_fields = {
                    'rubric': ['criterion', 'weight', 'description'],
                    'evaluation': {
                        'scores': ['criterion', 'score', 'evidence'],
                        'root': ['fit_score_1_to_5', 'shortlist_recommend', 'justification']
                    }
                }
                
                # Validate rubric
                for criterion in result['rubric']:
                    for field in required_fields['rubric']:
                        if field not in criterion:
                            raise ValueError(f"Missing {field} in rubric criterion")
                
                # Validate evaluation
                eval_data = result['evaluation']
                for score in eval_data.get('scores', []):
                    for field in required_fields['evaluation']['scores']:
                        if field not in score:
                            raise ValueError(f"Missing {field} in evaluation score")
                
                for field in required_fields['evaluation']['root']:
                    if field not in eval_data:
                        raise ValueError(f"Missing {field} in evaluation")
            
            return result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")
        
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

def display_results(analysis_result: Dict, arm: EvaluationArm):
    """Display analysis results in a formatted way"""
    
    if arm == EvaluationArm.SYSTEM_1:
        # ARM A: Fast Intuitive Display
        fit_score = analysis_result.get('fit_score_1_to_5', 0)
        score_color = "🟢" if fit_score >= 4 else "🟡" if fit_score >= 3 else "🔴"
        
        st.markdown(f"""
        <div class="score-display">
            <h2>{score_color} Quick Assessment Score: {fit_score}/5</h2>
            <p>{'✅ Recommended for Shortlist' if analysis_result.get('shortlist_recommend', False) else '❌ Not Recommended'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📋 Quick Assessment")
        st.markdown(
            f"""<div class="recommendation-box">{analysis_result.get('justification', 'No assessment available')}</div>""", 
            unsafe_allow_html=True
        )
    
    elif arm == EvaluationArm.SYSTEM_2:
        # ARM B: Deliberative Rubric-Based Display
        evaluation = analysis_result.get('evaluation', {})
        fit_score = evaluation.get('fit_score_1_to_5', 0)
        score_color = "🟢" if fit_score >= 4 else "🟡" if fit_score >= 3 else "🔴"
        
        st.markdown(f"""
        <div class="score-display">
            <h2>{score_color} Detailed Evaluation Score: {fit_score}/5</h2>
            <p>{'✅ Recommended for Shortlist' if evaluation.get('shortlist_recommend', False) else '❌ Not Recommended'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display Rubric and Scores
        st.subheader("📊 Evaluation Rubric & Scores")
        
        # Display the rubric criteria first
        st.markdown("#### Evaluation Criteria")
        rubric = analysis_result.get('rubric', [])
        for criterion in rubric:
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>{criterion['criterion']}</strong> (Weight: {criterion['weight']}%)
                <p><em>{criterion['description']}</em></p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("#### Detailed Scores")
        scores = evaluation.get('scores', [])
        
        for criterion_score in scores:
            criterion_name = criterion_score.get('criterion', '')
            score = criterion_score.get('score', 0)
            evidence = criterion_score.get('evidence', '')
            weight = next((r['weight'] for r in rubric if r['criterion'] == criterion_name), 0)
            
            st.markdown(f"""
            <div class="recommendation-box">
                <h4>{criterion_name} (Weight: {weight}%)</h4>
                <p><strong>Score:</strong> {score}/5</p>
                <p><strong>Evidence:</strong> {evidence}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("📋 Final Assessment")
        st.markdown(
            f"""<div class="recommendation-box">{analysis_result.get('evaluation', {}).get('justification', 'No assessment available')}</div>""", 
            unsafe_allow_html=True
        )

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📄 Resume Scorer AI</h1>
        <p>Analyze your resume against job descriptions using Google's Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = os.getenv('GEMINI_API_KEY')
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
    
    # Analysis options and button
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        evaluation_mode = st.radio(
            "Select Evaluation Mode:",
            [EvaluationArm.SYSTEM_1.value, EvaluationArm.SYSTEM_2.value],
            help="Choose between quick intuitive assessment or detailed rubric-based evaluation"
        )
    
    if st.button("🚀 Analyze Resume", type="primary"):
        # Validate inputs
        is_valid, error_msg = validate_inputs(resume_text, job_description)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Perform analysis
        try:
            selected_arm = EvaluationArm.SYSTEM_1 if evaluation_mode == EvaluationArm.SYSTEM_1.value else EvaluationArm.SYSTEM_2
            
            with st.spinner("🤖 AI is analyzing your resume..." + 
                          (" (Creating evaluation rubric...)" if selected_arm == EvaluationArm.SYSTEM_2 else "")):
                analyzer = GeminiAnalyzer(api_key)
                analysis_result = analyzer.analyze_resume(resume_text, job_description, selected_arm)
            
            # Display results
            st.markdown("---")
            st.header("📊 Analysis Results")
            display_results(analysis_result, selected_arm)
            
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

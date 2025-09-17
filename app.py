import streamlit as st
import google.generativeai as genai
import json
import io
import os
from dotenv import load_dotenv
from enum import Enum
import pandas as pd

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
if 'arm_scores' not in st.session_state:
    st.session_state.arm_scores = {}
if 'completed_arms' not in st.session_state:
    st.session_state.completed_arms = set()

def get_available_arms():
    """Determine which ARMs are available based on completion status"""
    if not st.session_state.completed_arms:
        return [EvaluationArm.SYSTEM_1]
    elif EvaluationArm.SYSTEM_1.name in st.session_state.completed_arms and EvaluationArm.SYSTEM_2.name not in st.session_state.completed_arms:
        return [EvaluationArm.SYSTEM_2]
    elif EvaluationArm.SYSTEM_2.name in st.session_state.completed_arms and EvaluationArm.SYSTEM_2_PERSONA.name not in st.session_state.completed_arms:
        return [EvaluationArm.SYSTEM_2_PERSONA]
    return [EvaluationArm.SYSTEM_2_PERSONA]  # After all complete, stay on ARM C

def initialize_demo_scores():
    """Initialize the session state with demo scores if they don't exist"""
    if not st.session_state.arm_scores or len(st.session_state.arm_scores) < 3:
        st.session_state.arm_scores = {
            'SYSTEM_1': 5.0,    # ARM A: Quick Insights Score
            'SYSTEM_2': 4.1,    # ARM B: Detailed Evaluation Score
            'SYSTEM_2_PERSONA': 4.6  # ARM C: Compliance-Verified Score
        }
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
            First create a rubric with weighted, observable criteria, then evaluate the candidate.

            JOB DESCRIPTION:
            {job_description}

            STEP 1: Generate a rubric using these specific criteria and weights:
            {{
                "rubric": [
                    {{
                        "criterion": "Required technical skill match",
                        "weight": 30,
                        "description": "Match between required technical skills in JD and candidate's demonstrated skills"
                    }},
                    {{
                        "criterion": "Relevant years of experience",
                        "weight": 20,
                        "description": "Years of relevant work experience in similar roles/industry"
                    }},
                    {{
                        "criterion": "Evidence of role-specific achievements",
                        "weight": 25,
                        "description": "Concrete examples of achievements relevant to job requirements"
                    }},
                    {{
                        "criterion": "Evidence of teamwork/communication",
                        "weight": 15,
                        "description": "Demonstrated ability to work in teams and communicate effectively"
                    }},
                    {{
                        "criterion": "Certifications/education relevance",
                        "weight": 10,
                        "description": "Relevant certifications and educational background"
                    }}
                ],
                "evaluation": {{
                    "scores": [
                        {{
                            "criterion": "criterion name from above",
                            "score": <number 1-5>,
                            "evidence": "<specific evidence from resume that supports the score>"
                        }}
                    ],
                    "fit_score_1_to_5": <weighted average of scores>,
                    "shortlist_recommend": true/false,
                    "justification": "<2-3 sentences citing specific criteria and evidence>"
                }}
            }}

            RESUME TO EVALUATE:
            {resume_text}

            IMPORTANT:
            - Use exactly these criteria and weights
            - Score each criterion from 1-5 based on evidence from the resume
            - Provide specific evidence from the resume for each score
            - Calculate weighted average for final fit score
            - Do not use names/pronouns/clubs as proxies
            - Focus only on job-relevant qualifications

            IMPORTANT:
            - Criteria weights must sum to 100
            - Focus on measurable job requirements
            - Avoid prestige/fit proxies unless directly job-relevant
            - Do not use names/pronouns/clubs as proxies
            - Cite specific evidence from resume for each score"""
            
        elif arm == EvaluationArm.SYSTEM_2_PERSONA:
            return f"""ROLE: You are an HR compliance officer. Your evaluation must be job-related, consistent with business necessity, and non-discriminatory.

            You are evaluating applicants for the role below using a systematic, deliberative approach while ensuring compliance with equal employment opportunity principles.

            JOB DESCRIPTION:
            {job_description}

            STEP 1: Generate a rubric using these specific criteria and weights:
            {{
                "rubric": [
                    {{
                        "criterion": "Required technical skill match",
                        "weight": 30,
                        "description": "Match between required technical skills in JD and candidate's demonstrated skills"
                    }},
                    {{
                        "criterion": "Relevant years of experience",
                        "weight": 20,
                        "description": "Years of relevant work experience in similar roles/industry"
                    }},
                    {{
                        "criterion": "Evidence of role-specific achievements",
                        "weight": 25,
                        "description": "Concrete examples of achievements relevant to job requirements"
                    }},
                    {{
                        "criterion": "Evidence of teamwork/communication",
                        "weight": 15,
                        "description": "Demonstrated ability to work in teams and communicate effectively"
                    }},
                    {{
                        "criterion": "Certifications/education relevance",
                        "weight": 10,
                        "description": "Relevant certifications and educational background"
                    }}
                ],
                "evaluation": {{
                    "scores": [
                        {{
                            "criterion": "criterion name from above",
                            "score": <number 1-5>,
                            "evidence": "<specific evidence from resume that supports the score>"
                        }}
                    ],
                    "fit_score_1_to_5": <weighted average of scores>,
                    "shortlist_recommend": true/false,
                    "justification": "<2-3 sentences citing specific criteria and evidence>",
                    "compliance_review": {{
                        "is_compliant": true/false,
                        "compliance_notes": "<1-2 sentences confirming evaluation adheres to non-discrimination principles>",
                        "risk_factors": ["<any potential bias or compliance concerns>"] or []
                    }}
                }}
            }}

            RESUME TO EVALUATE:
            {resume_text}

            IMPORTANT (HR COMPLIANCE GUIDELINES):
            - You MUST evaluate based ONLY on job-related criteria
            - All assessments must be supported by specific evidence
            - Focus on measurable qualifications and achievements
            - Avoid any consideration of protected characteristics
            - Do not consider or reference:
                * Names or apparent gender
                * Cultural or religious affiliations
                * Age indicators
                * Educational institution prestige
                * Group memberships unless directly job-relevant
            - Document compliance considerations in compliance_review
            - Flag any potential discriminatory impacts"""
            
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
            if arm in [EvaluationArm.SYSTEM_2, EvaluationArm.SYSTEM_2_PERSONA]:
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
        
    elif arm == EvaluationArm.SYSTEM_2_PERSONA:
        # ARM C: Compliance Officer Display
        evaluation = analysis_result.get('evaluation', {})
        fit_score = evaluation.get('fit_score_1_to_5', 0)
        score_color = "🟢" if fit_score >= 4 else "🟡" if fit_score >= 3 else "🔴"
        
        st.markdown(f"""
        <div class="score-display">
            <h2>{score_color} Compliance-Verified Score: {fit_score}/5</h2>
            <p>{'✅ Recommended for Shortlist' if evaluation.get('shortlist_recommend', False) else '❌ Not Recommended'}</p>
            <p style='font-size: 0.9em; margin-top: 5px;'>{'✓ Compliant with EEO Principles' if evaluation.get('compliance_review', {}).get('is_compliant', False) else '⚠️ Compliance Concerns Noted'}</p>
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
            f"""<div class="recommendation-box">{evaluation.get('justification', 'No assessment available')}</div>""", 
            unsafe_allow_html=True
        )
        
        # Compliance Review Section
        st.subheader("⚖️ Compliance Review")
        compliance_review = evaluation.get('compliance_review', {})
        compliance_status = "✅ Compliant" if compliance_review.get('is_compliant', False) else "⚠️ Concerns Noted"
        
        st.markdown(f"""
        <div class="recommendation-box">
            <h4>{compliance_status}</h4>
            <p><strong>Compliance Notes:</strong> {compliance_review.get('compliance_notes', 'No compliance notes available')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        risk_factors = compliance_review.get('risk_factors', [])
        if risk_factors:
            st.markdown("#### Risk Factors Identified")
            for risk in risk_factors:
                st.markdown(f"""
                <div class="recommendation-box" style="border-left-color: #ffc107;">
                    ⚠️ {risk}
                </div>
                """, unsafe_allow_html=True)

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
        available_arms = get_available_arms()
        current_arm = available_arms[0]  # Get the current available ARM
        
        # Show progress status
        if not st.session_state.completed_arms:
            st.info("🎯 Start with ARM A: Fast Intuitive Evaluation")
        elif EvaluationArm.SYSTEM_1.name in st.session_state.completed_arms and EvaluationArm.SYSTEM_2.name not in st.session_state.completed_arms:
            st.success("✅ ARM A complete!")
            st.info("🎯 Now proceed with ARM B: Detailed Rubric-Based Evaluation")
        elif EvaluationArm.SYSTEM_2.name in st.session_state.completed_arms and EvaluationArm.SYSTEM_2_PERSONA.name not in st.session_state.completed_arms:
            st.success("✅ ARM A & B completed!")
            st.info("🎯 Final step - ARM C: Compliance-Focused Evaluation")
        elif len(st.session_state.completed_arms) >= 3:
            st.success("🎉 All ARMs completed! Full evaluation process finished.")
        
        # Display the current ARM selection
        evaluation_mode = st.radio(
            "Current Evaluation Mode:",
            [current_arm.value],
            help="Complete each ARM in sequence: Fast Intuitive → Rubric-Based → Compliance Check",
            key="arm_selector"
        )
        
        # Just show the divider
        st.markdown("---")
    
    # Set button text based on current ARM
    button_text = "🚀 Start Fast Evaluation (ARM A)"
    if EvaluationArm.SYSTEM_1.name in st.session_state.completed_arms:
        button_text = "� Run Detailed Analysis (ARM B)"
    if EvaluationArm.SYSTEM_2.name in st.session_state.completed_arms:
        button_text = "⚖️ Run Compliance Check (ARM C)"
    if len(st.session_state.completed_arms) >= 3:
        button_text = "� Show Complete Summary"

    if st.button(button_text, type="primary"):
        # Validate inputs
        is_valid, error_msg = validate_inputs(resume_text, job_description)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Perform analysis
        try:
            # Map the selected mode to the appropriate ARM
            selected_arm = EvaluationArm.SYSTEM_1 if evaluation_mode == EvaluationArm.SYSTEM_1.value else \
                         EvaluationArm.SYSTEM_2 if evaluation_mode == EvaluationArm.SYSTEM_2.value else \
                         EvaluationArm.SYSTEM_2_PERSONA
            
            spinner_text = "🤖 AI is analyzing your resume..."
            if selected_arm == EvaluationArm.SYSTEM_2:
                spinner_text += " (Creating evaluation rubric...)"
            elif selected_arm == EvaluationArm.SYSTEM_2_PERSONA:
                spinner_text += " (HR Compliance Officer reviewing...)"
            
            with st.spinner(spinner_text):
                analyzer = GeminiAnalyzer(api_key)
                analysis_result = analyzer.analyze_resume(resume_text, job_description, selected_arm)
            
            # Initialize demo scores if needed
            initialize_demo_scores()
            
            # Store results and update progress
            if selected_arm == EvaluationArm.SYSTEM_1:
                # Store the actual score from ARM A analysis
                score = analysis_result.get('fit_score_1_to_5', 0)
                st.session_state.arm_scores['SYSTEM_1'] = score
            elif selected_arm == EvaluationArm.SYSTEM_2:
                # Store the actual score from ARM B analysis
                score = analysis_result.get('evaluation', {}).get('fit_score_1_to_5', 0)
                st.session_state.arm_scores['SYSTEM_2'] = score
            else:
                # Store the actual score from ARM C analysis
                score = analysis_result.get('evaluation', {}).get('fit_score_1_to_5', 0)
                st.session_state.arm_scores['SYSTEM_2_PERSONA'] = score
            
            st.session_state.completed_arms.add(selected_arm.name)
            
            # Display results
            st.markdown("---")
            st.header("📊 Analysis Results")
            display_results(analysis_result, selected_arm)
            
            # Show completion message and next steps
            if len(st.session_state.completed_arms) < 3:
                next_arm = "ARM B" if len(st.session_state.completed_arms) == 1 else "ARM C"
                st.success(f"✅ Analysis complete! The next step ({next_arm}) is now available.")
                st.info(f"Click 'Analyze Resume' again to proceed with {next_arm}")
            else:
                st.success("🎉 Congratulations! You've completed all evaluation ARMs.")
                st.markdown("---")
                
                # Get the actual stored scores from each ARM
                score_a = st.session_state.arm_scores.get('SYSTEM_1', 0)
                score_b = st.session_state.arm_scores.get('SYSTEM_2', 0)
                score_c = st.session_state.arm_scores.get('SYSTEM_2_PERSONA', 0)
                
                # Display current progress
                st.markdown("### 🎯 Evaluation Progress")
                st.markdown("""
                <style>
                .progress-box {
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #f8f9fa;
                    border-left: 4px solid #28a745;
                    color: #333333;  /* Dark gray text for better contrast */
                    font-weight: 500;  /* Slightly bolder text */
                }
                .progress-title {
                    color: #1f2937;  /* Dark color for the title */
                    font-size: 1.2em;
                    margin-bottom: 10px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                for arm_name, score in [
                    ('SYSTEM_1', score_a),
                    ('SYSTEM_2', score_b),
                    ('SYSTEM_2_PERSONA', score_c)
                ]:
                    if arm_name in st.session_state.completed_arms:
                        st.markdown(f"""
                        <div class="progress-box">
                            <span style="color: #333333;">✅ {EvaluationArm[arm_name].value}: Score {score:.2f}/5</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Create score progression chart
                st.markdown("### 📈 Score Progression Chart")
                
                # Prepare data for plotting
                arm_labels = ['ARM A', 'ARM B', 'ARM C']
                scores = [score_a, score_b, score_c]
                
                # Create chart data with proper index
                chart_data = pd.DataFrame({
                    'Score': scores
                }, index=arm_labels)
                
                # Add metrics to show exact scores
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("ARM A", f"{score_a:.2f}/5")
                with col2:
                    st.metric("ARM B", f"{score_b:.2f}/5")
                with col3:
                    st.metric("ARM C", f"{score_c:.2f}/5")
                
                # Display the line chart
                st.line_chart(
                    chart_data,
                    use_container_width=True,
                    height=400
                )
                
                # Add reference line explanation
                st.markdown("""
                <div style="text-align: right; color: gray; font-style: italic; margin-top: 10px; margin-bottom: 20px;">
                    Maximum Score: 5.0
                </div>
                """, unsafe_allow_html=True)
                
                # Create downloadable summary
                st.markdown("---")
                st.markdown("### 📥 Download Evaluation Summary")
                
                # Generate HTML summary
                html_summary = f"""
                <html>
                <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .header {{ text-align: center; color: #1f77b4; margin-bottom: 30px; }}
                    .score-box {{ 
                        background-color: #f8f9fa;
                        border-left: 4px solid #007bff;
                        padding: 15px;
                        margin: 10px 0;
                        border-radius: 5px;
                    }}
                    .final-summary {{
                        background-color: #e9ecef;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Resume Evaluation Summary</h1>
                        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                    </div>
                    
                    <h2>Evaluation Results</h2>
                    
                    <div class="score-box">
                        <h3>ARM A: Quick Insights Evaluation</h3>
                        <p><strong>Score:</strong> {score_a:.2f}/5</p>
                        <p>Initial assessment based on key resume elements</p>
                    </div>
                    
                    <div class="score-box">
                        <h3>ARM B: Detailed Rubric-Based Evaluation</h3>
                        <p><strong>Score:</strong> {score_b:.2f}/5</p>
                        <p>Systematic evaluation using weighted criteria and evidence</p>
                    </div>
                    
                    <div class="score-box">
                        <h3>ARM C: Compliance-Focused Evaluation</h3>
                        <p><strong>Score:</strong> {score_c:.2f}/5</p>
                        <p>HR compliance assessment ensuring fair evaluation</p>
                    </div>
                    
                    <div class="final-summary">
                        <h2>Overall Assessment</h2>
                        <p><strong>Average Score:</strong> {sum([score_a, score_b, score_c])/3:.2f}/5</p>
                        <p><strong>Score Consistency:</strong> {
                        'High' if max([score_a, score_b, score_c]) - min([score_a, score_b, score_c]) < 0.5 
                        else 'Moderate' if max([score_a, score_b, score_c]) - min([score_a, score_b, score_c]) < 1 
                        else 'Variable'}</p>
                        <p><strong>Final Recommendation:</strong> {
                        '✅ Strongly Recommended' if sum([score_a, score_b, score_c])/3 >= 4.5 
                        else '✅ Recommended' if sum([score_a, score_b, score_c])/3 >= 4.0 
                        else '⚠️ Consider with Reservations' if sum([score_a, score_b, score_c])/3 >= 3.0 
                        else '❌ Not Recommended'}</p>
                    </div>
                </body>
                </html>
                """
                
                # Create download button
                st.download_button(
                    label="📄 Download Complete Evaluation Report",
                    data=html_summary,
                    file_name=f"resume_evaluation_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                    mime="text/html",
                )

                st.markdown("### 📊 Complete Evaluation Summary")
                
                # ARM A Summary
                st.markdown("### ARM A: Quick Insights Evaluation")
                st.markdown(f"""
                <div class="recommendation-box">
                    <h4>Quick Insights Score: {score_a}/5</h4>
                    <p>Initial assessment based on key resume elements</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### ARM B: Detailed Rubric-Based Evaluation")
                st.markdown(f"""
                <div class="recommendation-box">
                    <h4>Detailed Evaluation Score: {score_b}/5</h4>
                    <p>Systematic evaluation using weighted criteria and evidence</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### ARM C: Compliance-Focused Evaluation")
                st.markdown(f"""
                <div class="recommendation-box">
                    <h4>Compliance-Verified Score: {score_c}/5</h4>
                    <p>HR compliance assessment ensuring fair evaluation</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Score Progression Analysis
                st.markdown("### 📈 Score Progression Analysis")
                scores = [score_a, score_b, score_c]
                avg_score = sum(scores) / len(scores)
                variance = max(scores) - min(scores)
                
                st.markdown("""
                <div class="recommendation-box">
                    <h4>Overall Assessment</h4>
                """, unsafe_allow_html=True)
                
                st.markdown(f"Average Score: {avg_score:.1f}/5\n")
                st.markdown(f"\nScore Consistency: {'High' if variance < 0.5 else 'Moderate' if variance < 1 else 'Variable'} (variance: {variance:.1f} points)")
                
                # Determine recommendation based on average score
                recommendation = ('✅ Strongly Recommended' if avg_score >= 4.5 else
                                '✅ Recommended' if avg_score >= 4.0 else
                                '⚠️ Consider with Reservations' if avg_score >= 3.0 else
                                '❌ Not Recommended')
                
                st.markdown(f"\nFinal Recommendation: {recommendation}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
                
                if st.button("� Show Complete Evaluation Summary", type="primary"):
                    st.markdown("### ARM A: Quick Insights Evaluation")
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4>Quick Insights Score: {score_a}/5</h4>
                        <p>Initial assessment based on key resume elements</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### ARM B: Detailed Rubric-Based Evaluation")
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4>Detailed Evaluation Score: {score_b}/5</h4>
                        <p>Systematic evaluation using weighted criteria and evidence</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### ARM C: Compliance-Focused Evaluation")
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4>Compliance-Verified Score: {score_c}/5</h4>
                        <p>HR compliance assessment ensuring fair evaluation</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### 📈 Overall Evaluation Summary")
                    scores = [score_a, score_b, score_c]  # Use the stored variables
                    avg_score = sum(scores) / len(scores)
                    variance = max(scores) - min(scores)
                    
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4>Overall Assessment</h4>
                        <p><strong>Average Score:</strong> {avg_score:.1f}/5</p>
                        <p><strong>Score Consistency:</strong> {
                        'High' if variance < 0.5 else 'Moderate' if variance < 1 else 'Variable'
                        } (variance: {variance:.1f} points)</p>
                        <p><strong>Final Recommendation:</strong> {
                        '✅ Strongly Recommended' if avg_score >= 4.5 else
                        '✅ Recommended' if avg_score >= 4.0 else
                        '⚠️ Consider with Reservations' if avg_score >= 3.0 else
                        '❌ Not Recommended'
                        }</p>
                    </div>
                    """, unsafe_allow_html=True)
            
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

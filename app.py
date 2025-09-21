import streamlit as st
import google.generativeai as genai
import json
import io
import os
from dotenv import load_dotenv
from enum import Enum
import pandas as pd

try:
    import pdfplumber
except ImportError:
    st.error("pdfplumber not installed. Please install with: pip install pdfplumber")
    st.stop()

try:
    from docx import Document
except ImportError:
    st.error("python-docx not installed. Please install with: pip install python-docx")
    st.stop()

from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Load environment variables
load_dotenv()

class EvaluationArm(Enum):
    SYSTEM_1 = "ARM A: Fast Intuitive Evaluation"
    SYSTEM_2 = "ARM B: Deliberative Rubric-First"
    SYSTEM_2_PERSONA = "ARM C: Compliance Officer"
    SYSTEM_2_PERSONA_DEBIAS = "ARM D: Compliance + Debias"

# Initialize session state for multi-resume support
def initialize_session_state():
    """Initialize session state for multi-resume functionality"""
    if 'resumes' not in st.session_state:
        st.session_state.resumes = {
            'resume_1': {
                'text': '',
                'label': 'Resume 1',
                'file_name': '',
                'completed_arms': set(),
                'arm_scores': {},
                'analysis_results': {}
            }
        }
    
    if 'active_resume' not in st.session_state:
        st.session_state.active_resume = 'resume_1'
    
    if 'resume_counter' not in st.session_state:
        st.session_state.resume_counter = 1
    
    # Legacy state for backward compatibility (remove after migration)
    if 'current_arm' not in st.session_state:
        st.session_state.current_arm = EvaluationArm.SYSTEM_1
    if 'evaluation_complete' not in st.session_state:
        st.session_state.evaluation_complete = False
    if 'arm_scores' not in st.session_state:
        st.session_state.arm_scores = {}
    if 'completed_arms' not in st.session_state:
        st.session_state.completed_arms = set()

# Call session state initialization
initialize_session_state()

def get_available_arms(resume_id: str = None):
    """Determine which ARMs are available based on completion status"""
    if resume_id is None:
        resume_id = st.session_state.active_resume
    
    # Get the specific resume's completed arms
    resume_data = st.session_state.resumes.get(resume_id, {})
    completed_arms = resume_data.get('completed_arms', set())
    
    if not completed_arms:
        return [EvaluationArm.SYSTEM_1]
    if EvaluationArm.SYSTEM_1.name in completed_arms and EvaluationArm.SYSTEM_2.name not in completed_arms:
        return [EvaluationArm.SYSTEM_2]
    if EvaluationArm.SYSTEM_2.name in completed_arms and EvaluationArm.SYSTEM_2_PERSONA.name not in completed_arms:
        return [EvaluationArm.SYSTEM_2_PERSONA]
    if EvaluationArm.SYSTEM_2_PERSONA.name in completed_arms and EvaluationArm.SYSTEM_2_PERSONA_DEBIAS.name not in completed_arms:
        return [EvaluationArm.SYSTEM_2_PERSONA_DEBIAS]
    # After all complete, stay on ARM D
    return [EvaluationArm.SYSTEM_2_PERSONA_DEBIAS]

def add_new_resume():
    """Add a new resume slot"""
    st.session_state.resume_counter += 1
    new_resume_id = f'resume_{st.session_state.resume_counter}'
    st.session_state.resumes[new_resume_id] = {
        'text': '',
        'label': f'Resume {st.session_state.resume_counter}',
        'file_name': '',
        'completed_arms': set(),
        'arm_scores': {},
        'analysis_results': {}
    }
    return new_resume_id

def remove_resume(resume_id: str):
    """Remove a resume (except the first one)"""
    if resume_id != 'resume_1' and resume_id in st.session_state.resumes:
        del st.session_state.resumes[resume_id]
        if st.session_state.active_resume == resume_id:
            st.session_state.active_resume = 'resume_1'

def get_resume_progress_emoji(resume_id: str):
    """Get progress emoji for a resume"""
    resume_data = st.session_state.resumes.get(resume_id, {})
    completed_arms = resume_data.get('completed_arms', set())
    
    if len(completed_arms) == 0:
        return "⚪⚪⚪⚪"
    elif len(completed_arms) == 1:
        return "✅⚪⚪⚪"
    elif len(completed_arms) == 2:
        return "✅✅⚪⚪"
    elif len(completed_arms) == 3:
        return "✅✅✅⚪"
    else:
        return "✅✅✅✅"

def get_all_resume_labels():
    """Get list of resume labels for dropdown"""
    labels = []
    for resume_id, resume_data in st.session_state.resumes.items():
        label = resume_data.get('label', resume_id)
        progress = get_resume_progress_emoji(resume_id)
        labels.append(f"{label} ({progress})")
    return labels

def initialize_demo_scores():
    """Initialize the session state with demo scores if they don't exist"""
    if not st.session_state.arm_scores:
        st.session_state.arm_scores = {}
    if 'SYSTEM_1' not in st.session_state.arm_scores:
        st.session_state.arm_scores['SYSTEM_1'] = 5.0
    if 'SYSTEM_2' not in st.session_state.arm_scores:
        st.session_state.arm_scores['SYSTEM_2'] = 4.1
    if 'SYSTEM_2_PERSONA' not in st.session_state.arm_scores:
        st.session_state.arm_scores['SYSTEM_2_PERSONA'] = 4.6
    if 'SYSTEM_2_PERSONA_DEBIAS' not in st.session_state.arm_scores:
        st.session_state.arm_scores['SYSTEM_2_PERSONA_DEBIAS'] = 4.4
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
        
        elif arm == EvaluationArm.SYSTEM_2_PERSONA_DEBIAS:
            return f"""ROLE: You are an HR compliance officer applying a debiased review. Provide the same systematic, evidence-based evaluation as ARM C, and additionally identify and mitigate any potential bias in the rubric or evidence selection.

            JOB DESCRIPTION:
            {job_description}

            STEP 1: Generate a rubric using these specific criteria and weights (same as ARM B/C).

            STEP 2: Evaluate the candidate with evidence for each criterion (same as ARM B/C).

            STEP 3: Compliance and Debias Review
            {{
                "rubric": [{{"criterion":"...","weight":<int>,"description":"..."}}],
                "evaluation": {{
                    "scores": [{{"criterion":"...","score":<1-5>,"evidence":"..."}}],
                    "fit_score_1_to_5": <number>,
                    "shortlist_recommend": true/false,
                    "justification": "<2-3 sentences citing criteria and evidence>",
                    "compliance_review": {{
                        "is_compliant": true/false,
                        "compliance_notes": "<confirmation of EEO adherence>",
                        "risk_factors": ["<any compliance concerns>"]
                    }},
                    "debias_review": {{
                        "mitigations_applied": ["<actions taken to mitigate potential bias>"] ,
                        "residual_risks": ["<remaining risks>"]
                    }}
                }}
            }}

            IMPORTANT:
            - Base all judgments on job-related, observable evidence
            - Avoid prestige proxies, demographic inferences, and ambiguous signals
            - If evidence is weak or ambiguous, reduce reliance and note in debias_review
            - Keep outputs strictly JSON as specified
            """
            
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
            if arm in [EvaluationArm.SYSTEM_2, EvaluationArm.SYSTEM_2_PERSONA, EvaluationArm.SYSTEM_2_PERSONA_DEBIAS]:
                if 'rubric' not in result or 'evaluation' not in result:
                    raise ValueError("Invalid response format for ARM B/C/D")
                
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

def validate_inputs(resume_text: str, job_description: str) -> Tuple[bool, str]:
    """Validate input texts for minimum requirements"""
    if not resume_text or len(resume_text.strip()) < 50:
        return False, "Resume text must be at least 50 characters long"
    
    if not job_description or len(job_description.strip()) < 50:
        return False, "Job description must be at least 50 characters long"
    
    return True, ""

def display_results(analysis_result: Dict, arm: EvaluationArm, resume_label: str = None):
    """Display analysis results in a formatted way"""
    
    # Add resume context if label is provided
    if resume_label:
        st.markdown(f"### 📊 Analysis Results for {resume_label}")
    else:
        st.markdown("### 📊 Analysis Results")
    
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
    
    elif arm == EvaluationArm.SYSTEM_2_PERSONA_DEBIAS:
        # ARM D: Compliance + Debias Display
        evaluation = analysis_result.get('evaluation', {})
        fit_score = evaluation.get('fit_score_1_to_5', 0)
        score_color = "🟢" if fit_score >= 4 else "🟡" if fit_score >= 3 else "🔴"
        
        st.markdown(f"""
        <div class="score-display">
            <h2>{score_color} Debiased Compliance Score: {fit_score}/5</h2>
            <p>{'✅ Recommended for Shortlist' if evaluation.get('shortlist_recommend', False) else '❌ Not Recommended'}</p>
            <p style='font-size: 0.9em; margin-top: 5px;'>{'✓ Compliant (Debiased Review Applied)' if evaluation.get('compliance_review', {}).get('is_compliant', False) else '⚠️ Compliance Concerns Noted'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📊 Evaluation Rubric & Scores")
        st.markdown("#### Evaluation Criteria")
        rubric = analysis_result.get('rubric', [])
        for criterion in rubric:
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>{criterion.get('criterion','')}</strong> (Weight: {criterion.get('weight',0)}%)
                <p><em>{criterion.get('description','')}</em></p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### Detailed Scores")
        scores = evaluation.get('scores', [])
        for criterion_score in scores:
            criterion_name = criterion_score.get('criterion', '')
            score = criterion_score.get('score', 0)
            evidence = criterion_score.get('evidence', '')
            weight = next((r.get('weight',0) for r in rubric if r.get('criterion','') == criterion_name), 0)
            st.markdown(f"""
            <div class="recommendation-box">
                <h4>{criterion_name} (Weight: {weight}%)</h4>
                <p><strong>Score:</strong> {score}/5</p>
                <p><strong>Evidence:</strong> {evidence}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("📋 Final Assessment")
        st.markdown(
            f"""<div class=\"recommendation-box\">{evaluation.get('justification', 'No assessment available')}</div>""",
            unsafe_allow_html=True
        )
        
        st.subheader("🧭 Debias Review")
        debias = evaluation.get('debias_review', {})
        mitigations = debias.get('mitigations_applied', []) or []
        residual = debias.get('residual_risks', []) or []
        if mitigations:
            st.markdown("#### Mitigations Applied")
            for m in mitigations:
                st.markdown(f"""
                <div class=\"recommendation-box\" style=\"border-left-color: #17a2b8;\">🧪 {m}</div>
                """, unsafe_allow_html=True)
        if residual:
            st.markdown("#### Residual Risks")
            for r in residual:
                st.markdown(f"""
                <div class=\"recommendation-box\" style=\"border-left-color: #ffc107;\">⚠️ {r}</div>
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
        api_key = os.getenv('GEMINI_API_KEY')
        
        # Resume Management Section
        st.markdown("### 📋 Resume Management")
        
        # Resume selector
        resume_options = list(st.session_state.resumes.keys())
        resume_labels = [st.session_state.resumes[rid]['label'] for rid in resume_options]
        
        selected_index = st.selectbox(
            "Select Active Resume:",
            range(len(resume_options)),
            format_func=lambda i: f"{resume_labels[i]} ({get_resume_progress_emoji(resume_options[i])})",
            index=resume_options.index(st.session_state.active_resume) if st.session_state.active_resume in resume_options else 0
        )
        
        # Update active resume
        st.session_state.active_resume = resume_options[selected_index]
        
        # Add/Remove resume buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Resume", help="Add another resume for comparison"):
                new_id = add_new_resume()
                st.session_state.active_resume = new_id
                st.rerun()
        
        with col2:
            if st.button("🗑️ Remove", disabled=len(st.session_state.resumes) <= 1 or st.session_state.active_resume == 'resume_1'):
                remove_resume(st.session_state.active_resume)
                st.rerun()
        
        # Progress overview for all resumes
        if len(st.session_state.resumes) > 1:
            st.markdown("#### Progress Overview")
            for rid, resume_data in st.session_state.resumes.items():
                progress = get_resume_progress_emoji(rid)
                label = resume_data.get('label', rid)
                st.markdown(f"**{label}**: {progress}")
        
        st.markdown("---")
        st.markdown("### 📚 How to Use")
        st.markdown("""
        1. **Upload** your resumes (PDF/DOCX) or paste text
        2. **Label** each resume for easy identification
        3. **Enter** the job description
        4. **Select** a resume and analyze through all 4 ARMs
        5. **Compare** results across all resumes
        """)
        
        st.markdown("### 🔒 Privacy")
        st.markdown("""
        - All processing happens client-side
        - No data is stored or logged
        - You control your own API usage
        """)
    
    # Resume labeling for active resume
    st.markdown("### 🏷️ Resume Information")
    current_resume = st.session_state.resumes[st.session_state.active_resume]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_label = st.text_input(
            "Resume Label:", 
            value=current_resume['label'],
            placeholder="e.g., John Doe, Marketing Candidate, Resume A",
            help="Give this resume a descriptive name"
        )
        if new_label != current_resume['label']:
            st.session_state.resumes[st.session_state.active_resume]['label'] = new_label
    
    with col2:
        st.metric("ARM Progress", f"{len(current_resume['completed_arms'])}/4", delta=None)
    
    st.markdown("---")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📄 Resume Input")
        
        # File upload option
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF or DOCX)",
            type=['pdf', 'docx'],
            help="Supported formats: PDF, DOCX",
            key=f"file_upload_{st.session_state.active_resume}"
        )
        
        # Manual text input option
        st.markdown("**OR** paste your resume text below:")
        resume_text = st.text_area(
            "Resume Text",
            height=300,
            placeholder="Paste your resume content here...",
            help="Minimum 50 characters required",
            value=current_resume.get('text', ''),
            key=f"resume_text_{st.session_state.active_resume}"
        )
        
        # Update resume text in session state
        if resume_text != current_resume.get('text', ''):
            st.session_state.resumes[st.session_state.active_resume]['text'] = resume_text
        
        # Process uploaded file
        if uploaded_file is not None:
            try:
                with st.spinner("Extracting text from file..."):
                    extracted_text = ResumeProcessor.extract_text_from_file(uploaded_file)
                    st.session_state.resumes[st.session_state.active_resume]['text'] = extracted_text
                    st.session_state.resumes[st.session_state.active_resume]['file_name'] = uploaded_file.name
                    st.success(f"✅ Successfully extracted text from {uploaded_file.name}")
                    st.text_area("Extracted Text", value=extracted_text, height=200, disabled=True)
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
        total_required_arms = 4  # ARM D is always enabled
        available_arms = get_available_arms()
        current_arm = available_arms[0]  # Get the current available ARM
        
        # Show progress status
        if not current_resume['completed_arms']:
            st.info("🎯 Start with ARM A: Fast Intuitive Evaluation")
        elif EvaluationArm.SYSTEM_1.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2.name not in current_resume['completed_arms']:
            st.success("✅ ARM A complete!")
            st.info("🎯 Now proceed with ARM B: Detailed Rubric-Based Evaluation")
        elif EvaluationArm.SYSTEM_2.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2_PERSONA.name not in current_resume['completed_arms']:
            st.success("✅ ARM A & B completed!")
            st.info("🎯 Now proceed with ARM C: Compliance-Focused Evaluation")
        elif EvaluationArm.SYSTEM_2_PERSONA.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2_PERSONA_DEBIAS.name not in current_resume['completed_arms']:
            st.success("✅ ARM A, B & C completed!")
            st.info("🎯 Final step - ARM D: Compliance + Debias Evaluation")
        elif len(current_resume['completed_arms']) >= total_required_arms:
            st.success("🎉 All ARMs completed! Full evaluation process finished.")
        
        # If there is a just-completed analysis, show it now (persisted across rerun)
        if st.session_state.get('last_analysis_result') is not None and st.session_state.get('last_analysis_arm') is not None:
            st.markdown("---")
            st.header("📊 Analysis Results")
            try:
                arm_to_display = EvaluationArm[st.session_state['last_analysis_arm']]
                display_results(st.session_state['last_analysis_result'], arm_to_display, current_resume['label'])
            finally:
                # Clear after displaying so it doesn't repeat on further reruns
                del st.session_state['last_analysis_result']
                del st.session_state['last_analysis_arm']

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
    if EvaluationArm.SYSTEM_1.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2.name not in current_resume['completed_arms']:
        button_text = "📊 Run Detailed Analysis (ARM B)"
    elif EvaluationArm.SYSTEM_2.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2_PERSONA.name not in current_resume['completed_arms']:
        button_text = "⚖️ Run Compliance Check (ARM C)"
    elif EvaluationArm.SYSTEM_2_PERSONA.name in current_resume['completed_arms'] and EvaluationArm.SYSTEM_2_PERSONA_DEBIAS.name not in current_resume['completed_arms']:
        button_text = "🧭 Run Compliance + Debias (ARM D)"
    elif len(current_resume['completed_arms']) >= 4:
        button_text = "📈 Show Complete Summary"

    if st.button(button_text, type="primary"):
        # Get current resume text
        resume_text = current_resume.get('text', '')
        
        # Validate inputs
        is_valid, error_msg = validate_inputs(resume_text, job_description)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Perform analysis
        try:
            # Map the selected mode to the appropriate ARM
            if evaluation_mode == EvaluationArm.SYSTEM_1.value:
                selected_arm = EvaluationArm.SYSTEM_1
            elif evaluation_mode == EvaluationArm.SYSTEM_2.value:
                selected_arm = EvaluationArm.SYSTEM_2
            elif evaluation_mode == EvaluationArm.SYSTEM_2_PERSONA.value:
                selected_arm = EvaluationArm.SYSTEM_2_PERSONA
            else:
                selected_arm = EvaluationArm.SYSTEM_2_PERSONA_DEBIAS
            
            spinner_text = f"🤖 AI is analyzing {current_resume['label']}..."
            if selected_arm == EvaluationArm.SYSTEM_2:
                spinner_text += " (Creating evaluation rubric...)"
            elif selected_arm == EvaluationArm.SYSTEM_2_PERSONA:
                spinner_text += " (HR Compliance Officer reviewing...)"
            
            with st.spinner(spinner_text):
                analyzer = GeminiAnalyzer(api_key)
                analysis_result = analyzer.analyze_resume(resume_text, job_description, selected_arm)
            
            # Store results and update progress for the current resume
            if selected_arm == EvaluationArm.SYSTEM_1:
                # Store the actual score from ARM A analysis
                score = analysis_result.get('fit_score_1_to_5', 0)
                current_resume['arm_scores']['SYSTEM_1'] = score
            elif selected_arm == EvaluationArm.SYSTEM_2:
                # Store the actual score from ARM B analysis
                score = analysis_result.get('evaluation', {}).get('fit_score_1_to_5', 0)
                current_resume['arm_scores']['SYSTEM_2'] = score
            elif selected_arm == EvaluationArm.SYSTEM_2_PERSONA:
                # Store the actual score from ARM C analysis
                score = analysis_result.get('evaluation', {}).get('fit_score_1_to_5', 0)
                current_resume['arm_scores']['SYSTEM_2_PERSONA'] = score
            else:
                # Store the actual score from ARM D analysis
                score = analysis_result.get('evaluation', {}).get('fit_score_1_to_5', 0)
                current_resume['arm_scores']['SYSTEM_2_PERSONA_DEBIAS'] = score
            
            # Update resume progress
            current_resume['completed_arms'].add(selected_arm.name)
            current_resume['analysis_results'][selected_arm.name] = analysis_result

            # Persist the analysis so we can show it right after rerun
            st.session_state['last_analysis_result'] = analysis_result
            st.session_state['last_analysis_arm'] = selected_arm.name

            # Immediately refresh so the next ARM is enabled and analysis is shown without extra click
            # Only rerun if there are remaining ARMs; otherwise continue to show final summary
            if len(current_resume['completed_arms']) < total_required_arms:
                st.rerun()
            
            # Show completion message and next steps
            if len(current_resume['completed_arms']) < total_required_arms:
                if len(current_resume['completed_arms']) == 1:
                    next_arm = "ARM B"
                elif len(current_resume['completed_arms']) == 2:
                    next_arm = "ARM C"
                elif len(current_resume['completed_arms']) == 3:
                    next_arm = "ARM D"
                st.success(f"✅ Analysis complete! The next step ({next_arm}) is now available.")
                st.info(f"Next stage: {next_arm} is now available.")
            else:
                st.success("🎉 Congratulations! You've completed all evaluation ARMs.")
                st.markdown("---")
                
                # Get the actual stored scores from each ARM for current resume
                score_a = current_resume['arm_scores'].get('SYSTEM_1', 0)
                score_b = current_resume['arm_scores'].get('SYSTEM_2', 0)
                score_c = current_resume['arm_scores'].get('SYSTEM_2_PERSONA', 0)
                score_d = current_resume['arm_scores'].get('SYSTEM_2_PERSONA_DEBIAS', 0)
                
                # Display current progress
                st.markdown(f"### 🎯 Evaluation Progress for {current_resume['label']}")
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
                
                arms_and_scores = [
                    ('SYSTEM_1', score_a),
                    ('SYSTEM_2', score_b),
                    ('SYSTEM_2_PERSONA', score_c),
                    ('SYSTEM_2_PERSONA_DEBIAS', score_d)
                ]
                for arm_name, score in arms_and_scores:
                    if arm_name in current_resume['completed_arms']:
                        st.markdown(f"""
                        <div class="progress-box">
                            <span style="color: #333333;">✅ {EvaluationArm[arm_name].value}: Score {score:.2f}/5</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Create score progression chart
                st.markdown("### 📈 Score Progression Chart")
                
                # Prepare data for plotting
                arm_labels = ['ARM A', 'ARM B', 'ARM C', 'ARM D']
                scores = [score_a, score_b, score_c, score_d]
                
                # Create chart data with proper index
                chart_data = pd.DataFrame({
                    'Score': scores
                }, index=arm_labels)
                
                # Add metrics to show exact scores
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("ARM A", f"{score_a:.2f}/5")
                with col2:
                    st.metric("ARM B", f"{score_b:.2f}/5")
                with col3:
                    st.metric("ARM C", f"{score_c:.2f}/5")
                with col4:
                    st.metric("ARM D", f"{score_d:.2f}/5")
                
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
                        <h2>{current_resume['label']}</h2>
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
                    
                    <div class="score-box">
                        <h3>ARM D: Compliance + Debias Evaluation</h3>
                        <p><strong>Score:</strong> {score_d:.2f}/5</p>
                        <p>Compliance review with bias mitigation</p>
                    </div>
                    
                    <div class="final-summary">
                        <h2>Overall Assessment</h2>
                        <p><strong>Average Score:</strong> {sum([score_a, score_b, score_c, score_d])/4:.2f}/5</p>
                        <p><strong>Score Consistency:</strong> {
                        'High' if max([score_a, score_b, score_c, score_d]) - min([score_a, score_b, score_c, score_d]) < 0.5 
                        else 'Moderate' if max([score_a, score_b, score_c, score_d]) - min([score_a, score_b, score_c, score_d]) < 1 
                        else 'Variable'}</p>
                        <p><strong>Final Recommendation:</strong> {
                        '✅ Strongly Recommended' if sum([score_a, score_b, score_c, score_d])/4 >= 4.5 
                        else '✅ Recommended' if sum([score_a, score_b, score_c, score_d])/4 >= 4.0 
                        else '⚠️ Consider with Reservations' if sum([score_a, score_b, score_c, score_d])/4 >= 3.0 
                        else '❌ Not Recommended'}</p>
                    </div>
                </body>
                </html>
                """
                
                # Create download button
                st.download_button(
                    label="📄 Download Complete Evaluation Report",
                    data=html_summary,
                    file_name=f"resume_evaluation_{current_resume['label'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
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
                
                st.markdown("### ARM D: Compliance + Debias Evaluation")
                st.markdown(f"""
                <div class="recommendation-box">
                    <h4>Debiased Compliance Score: {score_d}/5</h4>
                    <p>Compliance review with bias mitigation</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Score Progression Analysis
                st.markdown("### 📈 Score Progression Analysis")
                scores = [score_a, score_b, score_c, score_d]
                avg_score = sum(scores) / len(scores)
                variance = max(scores) - min(scores)
                
                st.markdown("""
                <div class="recommendation-box">
                    <h4 style="color: #000000;">Overall Assessment</h4>
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
                
                if st.button("📊 Show Complete Evaluation Summary", type="primary"):
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
                    st.markdown("### ARM D: Compliance + Debias Evaluation")
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4>Debiased Compliance Score: {score_d}/5</h4>
                        <p>Compliance review with bias mitigation</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("### 📈 Overall Evaluation Summary")
                    scores = [score_a, score_b, score_c, score_d]
                    avg_score = sum(scores) / len(scores)
                    variance = max(scores) - min(scores)
                    
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <h4 style="color: #000000;">Overall Assessment</h4>
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

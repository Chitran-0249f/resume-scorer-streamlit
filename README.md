# Resume Scorer AI - Streamlit App

A comprehensive Streamlit application that analyzes resumes against job descriptions using Google's Gemini 2.5 Pro AI model. Get detailed scoring, actionable recommendations, and missing keyword analysis to improve your resume.

## 🚀 Features

### Core Functionality
- **File Upload Support**: Accept PDF and DOCX files with automatic text extraction
- **Manual Text Input**: Allow users to paste resume text directly
- **Job Description Analysis**: Large text area for job posting content
- **AI-Powered Analysis**: Use Google Gemini 2.5 Pro for intelligent comparison
- **Comprehensive Scoring**: Generate 0-100 match score with detailed breakdown
- **Actionable Recommendations**: Provide specific, implementable suggestions
- **Missing Keywords**: Identify important skills/terms missing from resume

### Technical Features
- **Dual PDF Processing**: Uses both pdfplumber and PyPDF2 for maximum compatibility
- **Error Handling**: Comprehensive error handling for file uploads and API calls
- **Loading States**: Progress indicators and loading spinners
- **Responsive Design**: Mobile-friendly interface
- **Privacy-Focused**: All processing happens client-side, no data storage

## 📋 Requirements

- Python 3.8+
- Google AI API Key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## 🛠️ Installation

1. **Clone or download the project**
   ```bash
   cd resume-scorer-agent-streamlit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, navigate to the URL manually

## 🔑 Getting Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Paste it into the sidebar of the app

## 📖 How to Use

1. **Enter API Key**: Paste your Google AI API key in the sidebar
2. **Upload Resume**: 
   - Upload a PDF or DOCX file, OR
   - Paste your resume text directly
3. **Enter Job Description**: Paste the complete job description
4. **Analyze**: Click the "Analyze Resume" button
5. **Review Results**: 
   - Check your overall match score
   - Read the analysis summary
   - Review actionable recommendations
   - Note missing keywords to add

## 🎯 Analysis Output

The AI provides:

- **Overall Score**: 0-100 match percentage
- **Summary**: One-paragraph analysis of match quality
- **Recommendations**: 5 specific, actionable improvements
- **Missing Keywords**: Important terms from the job description

## 🔒 Privacy & Security

- **No Data Storage**: All processing happens in your browser
- **No Logging**: Your resume and job descriptions are not stored
- **API Usage**: You control your own Google AI API usage
- **Local Processing**: File extraction happens locally

## 🛠️ Technical Details

### Dependencies
- `streamlit`: Web interface framework
- `google-generativeai`: Google Gemini AI integration
- `PyPDF2`: PDF text extraction (fallback)
- `pdfplumber`: PDF text extraction (primary)
- `python-docx`: DOCX file processing

### File Processing
- **PDF**: Uses pdfplumber first, falls back to PyPDF2
- **DOCX**: Uses python-docx library
- **Error Handling**: Graceful fallbacks for extraction failures

### AI Integration
- **Model**: Google Gemini 1.5 Pro
- **Prompt Engineering**: Structured JSON output format
- **Error Handling**: API rate limits and quota management

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure your API key is correct
   - Check if you have sufficient quota
   - Verify the key is from Google AI Studio

2. **File Upload Issues**
   - Ensure file is PDF or DOCX format
   - Check file size (should be reasonable)
   - Try extracting text manually if upload fails

3. **Analysis Failures**
   - Ensure resume and job description are substantial (>50 characters)
   - Check internet connection
   - Try reducing text length if very long

4. **PDF Extraction Issues**
   - Some PDFs may have complex formatting
   - Try converting to DOCX format
   - Use manual text input as fallback

## 📱 Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## 📄 License

This project is open source and available under the MIT License.

## 🔗 External Resources

- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [Resume Builder](https://www.canva.com/resumes/)
- [Job Search Tips](https://www.indeed.com/career-advice)
- [Interview Preparation](https://www.glassdoor.com/blog/interview-prep/)

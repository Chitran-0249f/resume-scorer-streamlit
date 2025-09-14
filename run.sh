#!/bin/bash

# Resume Scorer AI - Startup Script

echo "🚀 Starting Resume Scorer AI..."
echo "=================================="

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the application
echo "📄 Launching Resume Scorer AI..."
echo "🌐 The app will open in your browser at http://localhost:8501"
echo ""

streamlit run app.py

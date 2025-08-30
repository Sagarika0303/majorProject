@echo off
cd ..
cd ..
cd AI-Resume-Analyzer

:: Create virtual environment
python -m venv venvapp

:: Activate virtual environment
call venvapp\Scripts\activate.bat

:: Go to App directory and run Streamlit app
cd App
streamlit run App.py

#!/bin/bash

# SAWGraph Streamlit App Launcher

echo "🚀 Starting SAWGraph Spatial Query Demo..."
echo "-------------------------------------"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt --quiet

# Run the app
echo "Starting Streamlit app..."
echo "The app will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo "-------------------------------------"

streamlit run streamlit_app.py

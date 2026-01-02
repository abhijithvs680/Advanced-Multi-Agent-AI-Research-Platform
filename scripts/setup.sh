#!/bin/bash

echo "Setting up Multi-Agent AI Research Assistant..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Create necessary directories
mkdir -p data/raw data/processed data/results
mkdir -p logs

# Copy config template
if [ ! -f config/config.yaml ]; then
    echo "Creating config file..."
    cp config/config.example.yaml config/config.yaml
fi

# Run tests
echo "Running tests..."
pytest tests/

echo "Setup complete!"
echo "To run the system: python scripts/run_experiment.py --topic \"your_topic\""

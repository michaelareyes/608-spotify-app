#!/bin/bash

echo "Triggering the lambda function..."

python3 spotify-app/lambda_function.py &

# Print a message indicating the script is starting
echo "Running the flask application..."

# Run the main Python script
python3 spotify-app/main.py &

echo "Running streamlit"

streamlit run spotify-app/streamlit_variables.py --server.address "0.0.0.0"

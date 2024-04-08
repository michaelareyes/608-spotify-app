# base lambda layer
from python:3.11-slim-bookworm

# Set working directory
WORKDIR /spotify-app

ENV PORT 8501

COPY requirements.txt .
RUN pip install --upgrade -r requirements.txt

# Copy requirements for the entire folder
COPY . .

RUN chmod +x spotify-app/run.sh

# Set the CMD to run the shell script
CMD ["sh", "-c", "spotify-app/run.sh"]

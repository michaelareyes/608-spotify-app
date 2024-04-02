# base lambda layer
FROM public.ecr.aws/lambda/python:3.8

# Set working directory
WORKDIR /spotify-app

# Copy requirements for the entire folder
COPY . .

# Install packages
RUN pip3 install -r /spotify-app/requirements.txt

# Set the CMD to run the shell script
CMD ["sh", "-c", "./run.sh"]

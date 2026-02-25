FROM python:3.10

# Set the working directory
WORKDIR /code

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port HF expects and run it!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
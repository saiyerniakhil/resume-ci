FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install LaTeX packages
RUN apt-get update && \
    apt-get install -y texlive-pictures texlive-science texlive-latex-extra latexmk && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Run the application with gunicorn
# Cloud Run will set the PORT environment variable
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120 app:app
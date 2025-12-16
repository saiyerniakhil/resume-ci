FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install LaTeX packages
RUN apt-get update && \
    apt-get install -y texlive-pictures texlive-science texlive-latex-extra latexmk && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Set environment variables for Cloud Run
ENV PORT=8080

# Run the application with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
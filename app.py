import os
import tempfile
from flask import Flask, request, jsonify, send_file
from main import Resume

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    """
    Generate resume PDF from JSON data

    Expected JSON format:
    {
        "socialLinks": {
            "linkedin": "https://...",
            "github": "https://...",
            "website": "https://...",
            "email": "email@example.com",
            "phone": "+1 234-567-8900"
        },
        "workEx": [
            {
                "role": "Software Developer",
                "company": "Company Name",
                "location": "City, State",
                "period": "Jan 2025 - Present",
                "description": [
                    "Description point 1",
                    "Description point 2"
                ]
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate required fields
        if 'workEx' not in data and 'socialLinks' not in data:
            return jsonify({'error': 'Either workEx or socialLinks must be provided'}), 400

        # Create a temporary directory for PDF generation
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate resume
            resume = Resume(data=data)

            # Change to temp directory for PDF generation
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                pdf_filename = resume.create(output_filename='resume')
                pdf_path = os.path.join(tmpdir, pdf_filename)

                # Send the PDF file
                return send_file(
                    pdf_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='resume.pdf'
                )
            finally:
                os.chdir(original_cwd)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-resume-from-api', methods=['GET'])
def generate_resume_from_api():
    """
    Generate resume PDF by fetching data from your API endpoints
    This will fetch data from:
    - https://saiyerniakhil.in/api/work-experience.json
    - https://saiyerniakhil.in/api/social-links.json
    """
    try:
        # Create temporary directory for PDF generation
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate resume (will fetch from API automatically)
            resume = Resume()  # No data provided, will fetch from API

            # Change to temp directory for PDF generation
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                pdf_filename = resume.create(output_filename='resume')
                pdf_path = os.path.join(tmpdir, pdf_filename)

                # Send the PDF file
                return send_file(
                    pdf_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='resume.pdf'
                )
            finally:
                os.chdir(original_cwd)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

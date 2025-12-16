import os
import tempfile
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from google.cloud import storage
from main import Resume

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
WORK_EXPERIENCE_API_URL = os.getenv('WORK_EXPERIENCE_API_URL', 'https://saiyerniakhil.in/api/work-experience.json')
SOCIAL_LINKS_API_URL = os.getenv('SOCIAL_LINKS_API_URL', 'https://saiyerniakhil.in/api/social-links.json')

# Initialize GCS client (only if bucket name is configured)
storage_client = None
if GCS_BUCKET_NAME:
    try:
        storage_client = storage.Client()
        logger.info(f"GCS client initialized for bucket: {GCS_BUCKET_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {str(e)}")


def upload_to_gcs(file_path: str, destination_blob_name: str = None) -> str:
    """
    Upload a file to Google Cloud Storage bucket

    Args:
        file_path: Local path to the file
        destination_blob_name: Name for the blob in GCS (optional, defaults to timestamped filename)

    Returns:
        Public URL of the uploaded file or None if upload is skipped
    """
    if not GCS_BUCKET_NAME or not storage_client:
        logger.warning("GCS_BUCKET_NAME not set or client not initialized, skipping upload to cloud storage")
        return None

    try:
        # Generate destination blob name if not provided
        if not destination_blob_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            destination_blob_name = f"resumes/resume_{timestamp}.pdf"

        # Get bucket and create blob
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        # Upload file (will replace if exists)
        blob.upload_from_filename(file_path)

        # Log the upload event
        logger.info(f"File uploaded successfully to gs://{GCS_BUCKET_NAME}/{destination_blob_name}")

        # Return the GCS URI
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {str(e)}")
        raise


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
        ],
        "uploadToGcs": false  // Optional: set to true to upload to GCS instead of returning file
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate required fields
        if 'workEx' not in data and 'socialLinks' not in data:
            return jsonify({'error': 'Either workEx or socialLinks must be provided'}), 400

        upload_to_gcs_flag = data.pop('uploadToGcs', False)

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

                # Upload to GCS if requested
                if upload_to_gcs_flag:
                    gcs_url = upload_to_gcs(pdf_path)
                    if gcs_url:
                        return jsonify({
                            'success': True,
                            'message': 'Resume generated and uploaded to GCS',
                            'gcs_url': gcs_url
                        }), 200
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'Resume generated but GCS upload failed (bucket not configured)'
                        }), 500

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
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/generate-resume-from-api', methods=['GET'])
def generate_resume_from_api():
    """
    Generate resume PDF by fetching data from your API endpoints
    This will fetch data from:
    - https://saiyerniakhil.in/api/work-experience.json
    - https://saiyerniakhil.in/api/social-links.json

    Query parameters:
    - upload_to_gcs: Set to 'true' to upload to GCS and return URL (default: false)
    """
    try:
        upload_to_gcs_flag = request.args.get('upload_to_gcs', 'false').lower() == 'true'

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

                # Upload to GCS if requested
                if upload_to_gcs_flag:
                    gcs_url = upload_to_gcs(pdf_path, destination_blob_name='resume.pdf')
                    if gcs_url:
                        logger.info(f"Resume uploaded to GCS: {gcs_url}")
                        return jsonify({
                            'success': True,
                            'message': 'Resume generated and uploaded to GCS',
                            'gcs_url': gcs_url
                        }), 200
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'Resume generated but GCS upload failed (bucket not configured)'
                        }), 500

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
        logger.error(f"Error generating resume from API: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

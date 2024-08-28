import logging
import os
import sys


def batch_classify_documents(project_id: str,
                             location: str,
                             processor_id: str,
                             gcs_pdf_folder: str):
    pass


# Retrieve Job-defined env vars
TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)

# Retrieve User-defined env vars
PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION')
PROCESSOR_ID = os.getenv('PROCESSOR_ID')
GCS_PDF_FOLDER = os.getenv('GCS_PDF_FOLDER')

# Main entry point
if __name__ == "__main__":
    if not PROJECT_ID or not LOCATION or not PROCESSOR_ID or not GCS_PDF_FOLDER:
        message = (
            f"Environment variables missing; {PROJECT_ID=}, {LOCATION=}, "
            f"{PROCESSOR_ID=}, {GCS_PDF_FOLDER=}"
        )
        logging.error(message)
        sys.exit(1)

    try:
        batch_classify_documents(project_id=PROJECT_ID,
                                 location=LOCATION,
                                 processor_id=PROCESSOR_ID,
                                 gcs_pdf_folder=GCS_PDF_FOLDER)
        logging.info(f"Completed Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
    except Exception as e:
        logging.error(f"Task Index {TASK_INDEX} (att. {TASK_ATTEMPT} failed!"
                      f"{e}")
        sys.exit(1)



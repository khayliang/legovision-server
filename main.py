from app import create_app
import os
import logging
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    UPLOAD_FOLDER = './uploads'
    PROCESSED_FOLDER = './processed/'
    
    app = create_app(logger, UPLOAD_FOLDER, PROCESSED_FOLDER)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


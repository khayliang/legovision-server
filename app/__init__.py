from flask import Flask, render_template, make_response, jsonify
import os
from flask_cors import CORS
from .controller import Controller

def create_app(logger, uploads_path, processed_path):
    ALLOWED_EXTENSIONS = {'mp4', '.avi'}

    app = Flask('lego detection')
    CORS(app)

    app.config['UPLOAD_FOLDER'] = uploads_path
    app.config['PROCESSED_FOLDER'] = processed_path
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    controller = Controller(app, logger)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/', methods=['POST'])
    def process_video():
        return controller.process_video()


    @app.route('/video', methods=['GET'])
    def get_video():
        return controller.get_video()

    @app.route('/video/info', methods=['GET'])
    def get_video_info():
        return controller.get_video_info()

    @app.route('/names', methods=['GET'])
    def get_names():
        return controller.get_names()

    return app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))

    logger = logging.getLogger('lego_app')
    logger.setLevel(logging.INFO)
    logger.warn("HEYYY")
    UPLOAD_FOLDER = './uploads'
    PROCESSED_FOLDER = './processed/'

    create_app(logger, UPLOAD_FOLDER, PROCESSED_FOLDER).run(host='0.0.0.0', port=port, debug=True)
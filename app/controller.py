from flask import send_file, request, jsonify, make_response
from werkzeug.utils import secure_filename
import cv2 
import os
from .detector import LegoDetector
from threading import Thread
from tinydb import TinyDB, Query
from collections import deque


def response(json, code):
    return make_response(jsonify(json), code)
    
class Controller:
    def __init__(self, app, logger):
        self.app = app
        self.detector = LegoDetector()
        self.db = TinyDB('db.json')
        self.event_queue = deque([])
        self.thread = None
        self.logger = logger

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.app.config['ALLOWED_EXTENSIONS']

    def detect_blocks(self):        
        with self.app.app_context():
            while len(self.event_queue) != 0:
                self.logger.info("Event queue contains " + str(len(self.event_queue)) + " items")
                file_path, file_name = self.event_queue.pop()
                cap = cv2.VideoCapture(file_path)
                fourcc = cv2.VideoWriter_fourcc('V','P','8','0')
                processed_path = self.app.config['PROCESSED_FOLDER'] + file_name + '.webm'
                info_path = self.app.config['PROCESSED_FOLDER'] + file_name +'.txt'
                f = open(info_path, "w")
                out = cv2.VideoWriter(processed_path,fourcc, 20.0, (640,480))
                self.logger.info("Starting processing of video: " + file_name)
                while(cap.isOpened()):
                    ret, img = cap.read()
                    if img is None:
                        break
                    final, items = self.detector.detect(img)
                    data = ""
                    for item in items:
                        data = data + "{},{},{}".format(item[0], item[1][0], item[1][1]) + ";"
                    data = data + "\n"
                    f.write(data)
                    out.write(final)
                f.close()
                cap.release()
                out.release()
                self.logger.info("completed processing of video: " + file_name)
                video_query = Query()
                self.db.update({'processed': True}, video_query.video_name == file_name)

        self.logger.info('Ending thread')

    def process_video(self):
        if 'file' not in request.files:
            return response({'message': "File not found"}, 400)
        file = request.files['file']
        if file.filename == '':
            return response({'message': "File name not found"}, 400)

        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            self.logger.info('Received video file: ' + filename)
            file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            filename = filename.split('.')[0]
            video_query = Query()
            result = self.db.search(video_query.video_name == filename)
            if len(result) == 0:
                info_path = self.app.config['PROCESSED_FOLDER'] + filename +'.txt'
                self.db.insert({'video_name': filename, 'info_path': info_path, 'processed': False })
            self.event_queue.append((file_path, filename))
            
            if self.thread == None or not self.thread.is_alive():
                self.logger.info('Thread initiated.')
                self.thread = Thread(target=self.detect_blocks)
                self.thread.start()
            
            return response({'message': "Success"}, 200)
        else:
            return response({'message': "Wrong file type"}, 400)

    def get_video(self):
        video_name = request.args.get('name')
        if video_name == None:
            return response({'message': 'video name not found'}, 400)
        video_query = Query()
        result = self.db.search(video_query.video_name == video_name)
        processed_path = os.path.abspath(self.app.config['PROCESSED_FOLDER'])
        if len(result) == 0:
            return response({'message': 'video does not exist'}, 400)
            
        #return Response(open(processed_path + '/'+ video_name, "rb"), content_type='video/mp4', mimetype="video/mp4")
        return send_file(processed_path + '/' + video_name + '.webm', mimetype="video/webm")

    def get_video_info(self):
        video_name = request.args.get('name')
        if video_name == None:
            return response({'message': 'video name not found'}, 400)
        video_query = Query()
        result = self.db.search(video_query.video_name == video_name)
        if len(result) == 0:
            return response({'message': 'video does not exist'}, 400)
        info_path = result[0]["info_path"]
        info_arr = []
        with open(info_path) as openfileobject:
            for line in openfileobject:
                info_arr.append(line.rstrip('\n'))
        return response({'message': info_arr}, 200)

    def get_names(self):
        all_entries = self.db.all()
        names = [{
            "name": entry["video_name"],
            "processed": entry["processed"]
            } for entry in all_entries]
        return response({'message': names}, 200)

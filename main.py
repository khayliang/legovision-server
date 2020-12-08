from flask import Flask, render_template, make_response, send_file, request, jsonify
from werkzeug.utils import secure_filename
import cv2 
import os
from detector import LegoDetector
from threading import Thread
from tinydb import TinyDB, Query
from flask_cors import CORS


UPLOAD_FOLDER = './uploads'
PROCESSED_FOLDER = './processed/'
ALLOWED_EXTENSIONS = {'mp4', '.avi'}

app = Flask('lego detection')
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

detector = LegoDetector()

db = TinyDB('db.json')
port = int(os.environ.get("PORT", 5000))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def response(json, code):
    return make_response(jsonify(json), code)


def detect_blocks(file_path, file_name):
    with app.app_context():
        cap = cv2.VideoCapture(file_path)
        fourcc = cv2.VideoWriter_fourcc('V','P','8','0')
        processed_path = PROCESSED_FOLDER + file_name + '.webm'
        info_path = PROCESSED_FOLDER + file_name +'.txt'
        f = open(info_path, "w")
        out = cv2.VideoWriter(processed_path,fourcc, 20.0, (640,480))
        print("Starting video processing...")
        while(cap.isOpened()):
            ret, img = cap.read()
            if img is None:
                break
            final, items = detector.detect(img)
            data = ""
            for item in items:
                data = data + "{},{},{}".format(item[0], item[1][0], item[1][1]) + ";"
            data = data + "\n"
            f.write(data)
            out.write(final)
        f.close()
        cap.release()
        out.release()
        print("completed")
        video_query = Query()
        db.update({'processed': True}, video_query.video_name == file_name)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def process_video():
    if 'file' not in request.files:
        return response({'message': "File not found"}, 400)
    file = request.files['file']
    if file.filename == '':
        return response({'message': "File name not found"}, 400)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        filename = filename.split('.')[0]
        video_query = Query()
        result = db.search(video_query.video_name == filename)
        if len(result) == 0:
            info_path = PROCESSED_FOLDER + filename +'.txt'
            db.insert({'video_name': filename, 'info_path': info_path, 'processed': False })
        thread = Thread(target=detect_blocks, args=(file_path, filename))
        thread.start()
        return response({'message': "Success"}, 200)
    else:
        return response({'message': "Wrong file type"}, 400)


@app.route('/video', methods=['GET'])
def get_video():
    video_name = request.args.get('name')
    if video_name == None:
        return response({'message': 'video name not found'}, 400)
    video_query = Query()
    result = db.search(video_query.video_name == video_name)
    processed_path = os.path.abspath(PROCESSED_FOLDER)
    if len(result) == 0:
        return response({'message': 'video does not exist'}, 400)
        
    #return Response(open(processed_path + '/'+ video_name, "rb"), content_type='video/mp4', mimetype="video/mp4")
    return send_file(processed_path + '/' + video_name + '.webm', mimetype="video/webm")

@app.route('/video/info', methods=['GET'])
def get_video_info():
    video_name = request.args.get('name')
    if video_name == None:
        return response({'message': 'video name not found'}, 400)
    video_query = Query()
    result = db.search(video_query.video_name == video_name)
    if len(result) == 0:
        return response({'message': 'video does not exist'}, 400)
    info_path = result[0]["info_path"]
    info_arr = []
    with open(info_path) as openfileobject:
        for line in openfileobject:
            info_arr.append(line.rstrip('\n'))
    return response({'message': info_arr}, 200)

@app.route('/names', methods=['GET'])
def get_names():
    all_entries = db.all()
    names = [{
        "name": entry["video_name"],
        "processed": entry["processed"]
        } for entry in all_entries]
    return response({'message': names}, 200)

if __name__ == '__main__':
    """
    http_server = WSGIServer(('0.0.0.0',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
    """
    app.run(host='0.0.0.0', port=port)
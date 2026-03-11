from flask import Flask, render_template, Response, send_file
from picamera2 import Picamera2
import cv2
import os
import zipfile
from datetime import datetime

app = Flask(__name__)

# Folder to store captures
CAPTURE_FOLDER = "captures"
os.makedirs(CAPTURE_FOLDER, exist_ok=True)

# Camera setup
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

streaming = True


def generate_frames():
    global streaming
    while True:
        frame = picam2.capture_array()

        if streaming:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture')
def capture():
    frame = picam2.capture_array()

    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    path = os.path.join(CAPTURE_FOLDER, filename)

    cv2.imwrite(path, frame)

    return "Captured"


@app.route('/pause')
def pause():
    global streaming
    streaming = False
    return "Paused"


@app.route('/play')
def play():
    global streaming
    streaming = True
    return "Playing"


@app.route('/download')
def download():
    zip_path = "captures.zip"

    with zipfile.ZipFile(zip_path, 'w') as z:
        for file in os.listdir(CAPTURE_FOLDER):
            z.write(os.path.join(CAPTURE_FOLDER, file), file)

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
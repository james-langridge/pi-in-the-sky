from flask import Flask, Response, request, jsonify
from picamera2 import Picamera2
from libcamera import controls
import cv2
import numpy as np
import io
import time
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()

PRESETS = {
    'default': {
        'ExposureTime': 33000,  # 33ms
        'AnalogueGain': 1.0,    # ISO 100 equivalent
        'AwbMode': controls.AwbModeEnum.Auto,
        'FrameRate': 30.0,
        'Brightness': 0,
        'Contrast': 1.0,
        'Saturation': 1.0,
        'Sharpness': 1.0,
        'HdrMode': controls.HdrModeEnum.Off,
        'AeExposureMode': controls.AeExposureModeEnum.Normal,
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted
    },
    'low_light': {
        'ExposureTime': 100000,  # 100ms
        'AnalogueGain': 4.0,     # Higher ISO
        'AwbMode': controls.AwbModeEnum.Tungsten,
        'FrameRate': 15.0,
        'Brightness': 0.1,
        'Contrast': 1.2,
        'Saturation': 1.1,
        'Sharpness': 0.8,
        'HdrMode': controls.HdrModeEnum.Night,
        'AeExposureMode': controls.AeExposureModeEnum.Long,
        'AeMeteringMode': controls.AeMeteringModeEnum.Matrix
    },
}

def generate_frames():
    while True:
        try:
            stream = io.BytesIO()
            picam2.capture_file(stream, format='jpeg')
            image = cv2.imdecode(np.frombuffer(stream.getvalue(), np.uint8), 1)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(image, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            app.logger.error(f"Error generating frame: {str(e)}")
            time.sleep(1)  # Wait a bit before trying again

        time.sleep(0.1)  # Adjust this value to control frame rate

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/shutdown')
def shutdown():
    os.system('sudo shutdown -h now')
    return 'Shutting down...'

@app.route('/apply_preset', methods=['POST'])
def apply_preset():
    preset_name = request.json.get('preset')
    if preset_name not in PRESETS:
        return jsonify({"status": "error", "message": f"Unknown preset: {preset_name}"}), 400

    try:
        picam2.set_controls(PRESETS[preset_name])
        return jsonify({"status": "success", "message": f"Applied {preset_name} preset successfully."})
    except Exception as e:
        app.logger.error(f"Error applying preset: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to apply preset"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 8080)),
        threaded=True,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
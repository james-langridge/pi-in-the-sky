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

# (min, max, default)
PRESETS = {
    'default': {
        # Exposure time for the sensor to use, measured
        # in microseconds.
        'ExposureTime': None,  # (13, 112015443, None)
        'AnalogueGain': None,    # (1.1228070259094238, 16.0, None)
        # AwbModeEnum followed by one of:
        # Auto - any illumant
        # Tungsten - tungsten lighting
        # Fluorescent - fluorescent lighting
        # Indoor - indoor illumination
        # Daylight - daylight illumination
        # Cloudy - cloudy illumination
        # Custom - custom setting
        'AwbMode': controls.AwbModeEnum.Auto, # (0, 7, 0)
        # Adjusts the image brightness where -1.0 is
        # very dark, 1.0 is very bright, and 0.0 is the
        # default "normal" brightness.
        'Brightness': 0, # (-1.0, 1.0, 0.0)
        # Sets the contrast of the image, where zero
        # means "no contrast", 1.0 is the default "normal"
        # contrast, and larger values increase the
        # contrast proportionately.
        'Contrast': 1.0, # (0.0, 32.0, 1.0)
        # Amount of colour saturation, where zero
        # produces greyscale images, 1.0 represents
        # default "normal" saturation, and higher values
        # produce more saturated colours.
        'Saturation': 1.0, # (0.0, 32.0, 1.0)
        # Sets the image sharpness, where zero implies
        # no additional sharpening is performed, 1.0 is
        # the default "normal" level of sharpening, and
        # larger values apply proportionately stronger
        # sharpening.
        'Sharpness': 1.0, # (0.0, 16.0, 1.0)
        # Whether to run the camera in an HDR mode
        # (distinct from the in-camera HDR supported by
        # the Camera Module 3). Most of these HDR
        # features work only on Pi 5 or later devices.
        # HdrModeEnum followed by one of:
        # Off - disable HDR (default)
        # SingleExposure - combine multiple short
        # exposure images, this is the recommended
        # mode (Pi 5 only)
        # MultiExposure - combine short and long
        # images, ony recommended when a scene is
        # completely static (Pi 5 only)
        # Night - an HDR mode that combines multiple
        # low light images, and can recover some
        # highlights (Pi 5 only)
        # MultiExposureUnmerged - return unmerged
        # distinct short and long exposure images.
        'HdrMode': controls.HdrModeEnum.Off, # (0, 4, 0)
        # Sets the exposure mode of the AEC/AGC
        # algorithm.
        # AeExposureModeEnum followed by one of:
        # Normal - normal exposures
        # Short - use shorter exposures
        # Long - use longer exposures
        # Custom - use custom exposures
        'AeExposureMode': controls.AeExposureModeEnum.Normal, # (0, 3, 0)
        # Sets the metering mode of the AEC/AGC
        # algorithm.
        # AeMeteringModeEnum followed by one of:
        # CentreWeighted - centre weighted metering
        # Spot - spot metering
        # Matrix - matrix metering
        # Custom - custom metering
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted # (0, 3, 0)
    },
    'low_light': {
        'ExposureTime': 100000,
        'AnalogueGain': 4.0,
        'AwbMode': controls.AwbModeEnum.Tungsten,
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
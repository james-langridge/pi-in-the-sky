from flask import Flask, Response, render_template, request, jsonify
from picamera2 import Picamera2
from picamera2 import Controls
from libcamera import controls
import cv2
import numpy as np
import io
import time
from datetime import datetime
import traceback
import os
from flask_cors import CORS

# Picamera2.set_logging(Picamera2.DEBUG)

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()

# Define default settings
DEFAULT_SETTINGS = {
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
}

# Define presets
PRESETS = {
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
    'fast_motion': {
        'ExposureTime': 5000,    # 5ms
        'AnalogueGain': 1.5,     # Lower ISO for less noise
        'AwbMode': controls.AwbModeEnum.Auto,
        'FrameRate': 60.0,
        'Brightness': 0,
        'Contrast': 1.1,
        'Saturation': 1.0,
        'Sharpness': 1.2,
        'HdrMode': controls.HdrModeEnum.SingleExposure,
        'AeExposureMode': controls.AeExposureModeEnum.Short,
        'AeMeteringMode': controls.AeMeteringModeEnum.CentreWeighted
    },
    'high_detail': {
        'ExposureTime': 20000,   # 20ms
        'AnalogueGain': 1.0,     # Low ISO for less noise
        'AwbMode': controls.AwbModeEnum.Daylight,
        'FrameRate': 30.0,
        'Brightness': 0,
        'Contrast': 1.3,
        'Saturation': 1.2,
        'Sharpness': 1.5,
        'HdrMode': controls.HdrModeEnum.SingleExposure,
        'AeExposureMode': controls.AeExposureModeEnum.Normal,
        'AeMeteringMode': controls.AeMeteringModeEnum.Spot
    }
}

def get_hdr_mode(mode_str):
    hdr_modes = {
        'Off': 0,
        'SingleExposure': 1,
        'MultiExposure': 2,
        'Night': 3,
        'MultiExposureUnmerged': 4
    }
    return hdr_modes.get(mode_str, 0)  # Default to Off if not found

def get_temporal_noise_reduction_mode(mode_str):
    tnr_modes = {
        'Off': 0,
        'Normal': 1,
        'Aggressive': 2
    }
    return tnr_modes.get(mode_str, 0)  # Default to Off if not found

def get_high_quality_denoise_mode(mode_str):
    hq_denoise_modes = {
        'Off': 0,
        'Normal': 1,
        'HighQuality': 2
    }
    return hq_denoise_modes.get(mode_str, 0)  # Default to Off if not found

# Global variable to track the last frame time
last_frame_time = time.time()

def update_last_frame_time():
    global last_frame_time
    last_frame_time = time.time()

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

            update_last_frame_time()

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

def get_awb_mode(mode_str):
    awb_modes = {
        'Auto': 0,
        'Tungsten': 1,
        'Fluorescent': 2,
        'Indoor': 3,
        'Daylight': 4,
        'Cloudy': 5
    }
    return awb_modes.get(mode_str, 0)  # Default to Auto if not found

def get_noise_reduction_mode(mode_str):
    nr_modes = {
        'Off': 0,
        'Fast': 1,
        'HighQuality': 2
    }
    return nr_modes.get(mode_str, 1)  # Default to Fast if not found

@app.route('/update_camera', methods=['POST'])
def update_camera():
    data = request.json
    new_settings = {}

    try:
        if 'exposureTime' in data:
            new_settings['ExposureTime'] = int(float(data['exposureTime']) * 1000)  # Convert ms to µs
        if 'iso' in data:
            new_settings['AnalogueGain'] = float(data['iso'])
        if 'awbMode' in data:
            new_settings['AwbMode'] = int(data['awbMode'])
        if 'frameRate' in data:
            new_settings['FrameRate'] = float(data['frameRate'])
        if 'brightness' in data:
            new_settings['Brightness'] = float(data['brightness'])
        if 'contrast' in data:
            new_settings['Contrast'] = float(data['contrast'])
        if 'saturation' in data:
            new_settings['Saturation'] = float(data['saturation'])
        if 'sharpness' in data:
            new_settings['Sharpness'] = float(data['sharpness'])
        if 'hdrMode' in data:
            new_settings['HdrMode'] = int(data['hdrMode'])
        if 'exposureMode' in data:
            new_settings['ExposureMode'] = int(data['exposureMode'])
        if 'meteringMode' in data:
            new_settings['AeMeteringMode'] = int(data['meteringMode'])

        picam2.set_controls(new_settings)
        return jsonify({"status": "success", "message": "Camera settings updated successfully."})
    except Exception as e:
        app.logger.error(f"Error updating camera settings: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred while updating settings: {str(e)}"}), 500

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

@app.route('/reset_camera', methods=['POST'])
def reset_camera():
    try:
        picam2.set_controls(DEFAULT_SETTINGS)
        return jsonify({"status": "success", "message": "Camera reset to default settings."})
    except Exception as e:
        app.logger.error(f"Error resetting camera: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to reset camera settings"}), 500

@app.route('/get_camera_settings')
def get_camera_settings():
    try:
        # This returns a dictionary with the control names as keys,
        # and each value being a tuple of (min, max, default) values for that control.
        settings = picam2.camera_controls
        exposure_time = settings.get('ExposureTime', 33000)
#         app.logger.info(f"************************ Camera settings: {settings}")
        print(f"************************ camera_controls: {settings}")

        metadata = picam2.capture_metadata()
        controls = {}
        for c in [
            "ExposureTime", "AnalogueGain", "ColourGains",
            "NoiseReductionMode", "AeMeteringMode", "FrameDurationLimits",
            "StatsOutputEnable", "AfMode", "Saturation", "LensPosition",
            "AwbEnable", "AfWindows", "AfSpeed", "AeEnable", "AfRange",
            "ScalerCrop", "AeConstraintMode", "HdrMode", "Contrast",
            "AfPause", "ExposureValue", "Brightness", "AeFlickerPeriod",
            "AwbMode", "AfTrigger", "AeFlickerMode", "AeExposureMode",
            "Sharpness", "AfMetering"
        ]:
            if c in metadata:
                controls[c] = metadata[c]
        print(f"************************ Current settings: {controls}")

        # Handle the case where ExposureTime might be a tuple
        if isinstance(exposure_time, tuple):
            exposure_time = exposure_time[0]  # Use the first value of the tuple

        return jsonify({
            'exposureTime': exposure_time / 1000,  # Convert to ms
            'iso': settings.get('AnalogueGain', 1.0),
            'awbMode': settings.get('AwbMode', 0),
            'frameRate': settings.get('FrameRate', 30.0),
            'brightness': settings.get('Brightness', 0),
            'contrast': settings.get('Contrast', 1.0),
            'saturation': settings.get('Saturation', 1.0),
            'sharpness': settings.get('Sharpness', 1.0),
            'hdrMode': settings.get('HdrMode', 0),
            'aeExposureMode': settings.get('AeExposureMode', 0),
            'aeMeteringMode': settings.get('AeMeteringMode', 0)
        })
    except Exception as e:
        app.logger.error(f"Error getting camera settings: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get camera settings"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 8080)),
        threaded=True,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
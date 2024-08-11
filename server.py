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

app = Flask(__name__,
            template_folder='/home/james/pi-in-the-sky/templates',
            static_folder='/home/james/pi-in-the-sky/static')

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()

# Define presets
presets = {
    "low_light": {
        "ExposureTime": 100000,  # 100ms exposure time
        "AnalogueGain": 8.0,     # High ISO equivalent
        "AwbMode": 1,  # Tungsten
        "FrameRate": 15.0,
        "NoiseReductionMode": 2,  # HighQuality
        "Contrast": 1.2,
        "Brightness": 0.1,
        "Sharpness": 0.8,
        "HdrMode": 3,  # Night
        "TemporalNoiseReductionMode": 2,  # Aggressive
        "HighQualityDenoise": 2,  # HighQuality
        "LocalToneMappingEnable": True,
        "LensShading": 1.0,
        "DefectivePixelCorrection": True,
        "BlackLevel": 5
    },
    "fast_motion": {
        "ExposureTime": 5000,    # 5ms exposure time
        "AnalogueGain": 2.0,     # Lower ISO for less noise
        "AwbMode": 0,  # Auto
        "FrameRate": 60.0,
        "NoiseReductionMode": 1,  # Fast
        "Contrast": 1.1,
        "Brightness": 0.0,
        "Sharpness": 1.2,
        "HdrMode": 1,  # SingleExposure
        "TemporalNoiseReductionMode": 0,  # Off
        "HighQualityDenoise": 0,  # Off
        "LocalToneMappingEnable": False,
        "LensShading": 1.0,
        "DefectivePixelCorrection": True,
        "BlackLevel": 0
    },
    "high_detail": {
        "ExposureTime": 20000,   # 20ms exposure time
        "AnalogueGain": 1.0,     # Low ISO for less noise
        "AwbMode": 0,  # Auto
        "FrameRate": 30.0,
        "NoiseReductionMode": 0,  # Off
        "Contrast": 1.3,
        "Brightness": 0.0,
        "Sharpness": 1.5,
        "HdrMode": 1,  # SingleExposure
        "TemporalNoiseReductionMode": 0,  # Off
        "HighQualityDenoise": 0,  # Off
        "LocalToneMappingEnable": True,
        "LensShading": 1.0,
        "DefectivePixelCorrection": True,
        "BlackLevel": 0
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

@app.route('/')
def index():
    return render_template('index.html')

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
    errors = []

    try:
        if 'exposureTime' in data:
            exposure_time_ms = float(data['exposureTime'])
            if 0 <= exposure_time_ms <= 1000:  # 0 to 1000 ms (1 second)
                new_settings['ExposureTime'] = int(exposure_time_ms * 1000)  # Convert ms to µs
            else:
                errors.append("Exposure time must be between 0 and 1000 ms.")

        if 'iso' in data:
            iso = float(data['iso'])
            if 1 <= iso <= 16:
                new_settings['AnalogueGain'] = iso
            else:
                errors.append("ISO must be between 1 and 16.")

        if 'awbMode' in data:
            awb_mode = get_awb_mode(data['awbMode'])
            new_settings['AwbMode'] = awb_mode

        if 'frameRate' in data:
            frame_rate = float(data['frameRate'])
            if 1 <= frame_rate <= 30:
                new_settings['FrameRate'] = frame_rate
            else:
                errors.append("Frame rate must be between 1 and 30.")

        if 'noiseReduction' in data:
            noise_reduction = get_noise_reduction_mode(data['noiseReduction'])
            new_settings['NoiseReductionMode'] = noise_reduction

        if 'contrast' in data:
            contrast = float(data['contrast'])
            if 0 <= contrast <= 2:
                new_settings['Contrast'] = contrast
            else:
                errors.append("Contrast must be between 0 and 2.")

        if 'brightness' in data:
            brightness = float(data['brightness'])
            if -1 <= brightness <= 1:
                new_settings['Brightness'] = brightness
            else:
                errors.append("Brightness must be between -1 and 1.")

        if 'sharpness' in data:
            sharpness = float(data['sharpness'])
            if 0 <= sharpness <= 2:
                new_settings['Sharpness'] = sharpness
            else:
                errors.append("Sharpness must be between 0 and 2.")

        if 'hdrMode' in data:
            new_settings['HdrMode'] = get_hdr_mode(data['hdrMode'])

        if 'temporalNoiseReduction' in data:
            new_settings['TemporalNoiseReductionMode'] = get_temporal_noise_reduction_mode(data['temporalNoiseReduction'])

        if 'highQualityDenoise' in data:
            new_settings['HighQualityDenoise'] = get_high_quality_denoise_mode(data['highQualityDenoise'])

        if 'localToneMapping' in data:
            new_settings['LocalToneMappingEnable'] = bool(data['localToneMapping'])

        if 'lensShading' in data:
            lens_shading = float(data['lensShading'])
            if 0 <= lens_shading <= 1:
                new_settings['LensShading'] = lens_shading
            else:
                errors.append("Lens shading must be between 0 and 1.")

        if 'defectivePixelCorrection' in data:
            new_settings['DefectivePixelCorrection'] = bool(data['defectivePixelCorrection'])

        if 'blackLevel' in data:
            new_settings['BlackLevel'] = int(data['blackLevel'])

        if errors:
            return jsonify({"status": "error", "messages": errors}), 400

        # Store current settings before applying new ones
        current_settings = picam2.camera_controls

        # Attempt to apply new settings
        picam2.set_controls(new_settings)

        return jsonify({"status": "success", "message": "Camera settings updated successfully."})
    except Exception as e:
        app.logger.error(f"Error updating camera settings: {str(e)}\n{traceback.format_exc()}")

        # Attempt to revert to previous settings
        try:
            picam2.set_controls(current_settings)
            app.logger.info("Reverted to previous camera settings after error.")
        except Exception as revert_error:
            app.logger.error(f"Error reverting camera settings: {str(revert_error)}")

        return jsonify({"status": "error", "message": "An error occurred while updating settings. The stream will continue with previous settings."}), 500

@app.route('/shutdown')
def shutdown():
    os.system('sudo shutdown -h now')
    return 'Shutting down...'

@app.route('/stream_status')
def stream_status():
    global last_frame_time
    if time.time() - last_frame_time > 5:  # If no frame for 5 seconds, consider stream stopped
        return jsonify({"status": "stopped"})
    return jsonify({"status": "active"})

@app.route('/apply_preset', methods=['POST'])
def apply_preset():
    preset_name = request.json.get('preset')
    if preset_name not in presets:
        return jsonify({"status": "error", "message": f"Unknown preset: {preset_name}"}), 400

    try:
        picam2.set_controls(presets[preset_name])
        return jsonify({"status": "success", "message": f"Applied {preset_name} preset successfully."})
    except Exception as e:
        app.logger.error(f"Error applying preset: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An error occurred while applying the preset."}), 500

@app.route('/reset_camera', methods=['POST'])
def reset_camera():
    try:
        default_settings = {
            'ExposureTime': 33000,  # 33ms exposure time
            'AnalogueGain': 1.0,    # ISO 100 equivalent
            'AwbMode': 0,  # Auto
            'FrameRate': 30.0,
            'NoiseReductionMode': 1,  # Fast
            'Contrast': 1.0,
            'Brightness': 0.0,
            'Sharpness': 1.0,
            'HdrMode': 0,  # Off
            'TemporalNoiseReductionMode': 0,  # Off
            'HighQualityDenoise': 0,  # Off
            'LocalToneMappingEnable': False,
            'LensShading': 1.0,
            'DefectivePixelCorrection': True,
            'BlackLevel': 0
        }

        picam2.set_controls(default_settings)
        return jsonify({"status": "success", "message": "Camera reset to default settings."})
    except Exception as e:
        app.logger.error(f"Error resetting camera: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An error occurred while resetting camera settings."}), 500

@app.route('/get_camera_settings')
def get_camera_settings():
    try:
        settings = picam2.camera_controls
        return jsonify({
            'exposureTime': settings.get('ExposureTime', 33000),
            'iso': settings.get('AnalogueGain', 1.0),
            'awbMode': settings.get('AwbMode', 0),
            'frameRate': settings.get('FrameRate', 30.0),
            'noiseReduction': settings.get('NoiseReductionMode', 1),
            'contrast': settings.get('Contrast', 1.0),
            'brightness': settings.get('Brightness', 0.0),
            'sharpness': settings.get('Sharpness', 1.0),
            'hdrMode': settings.get('HdrMode', 0),
            'temporalNoiseReduction': settings.get('TemporalNoiseReductionMode', 0),
            'highQualityDenoise': settings.get('HighQualityDenoise', 0),
            'localToneMapping': settings.get('LocalToneMappingEnable', False),
            'lensShading': settings.get('LensShading', 1.0),
            'defectivePixelCorrection': settings.get('DefectivePixelCorrection', True),
            'blackLevel': settings.get('BlackLevel', 0)
        })
    except Exception as e:
        app.logger.error(f"Error getting camera settings: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get camera settings"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
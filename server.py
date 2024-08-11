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
import threading

app = Flask(__name__,
            template_folder='/home/james/pi-in-the-sky/templates',
            static_folder='/home/james/pi-in-the-sky/static')

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()

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
            exposure_time = int(data['exposureTime'])
            if 0 <= exposure_time <= 1000000:
                new_settings['ExposureTime'] = exposure_time
            else:
                errors.append("Exposure time must be between 0 and 1000000 µs.")

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
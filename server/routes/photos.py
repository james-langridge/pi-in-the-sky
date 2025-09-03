"""Photo gallery routes."""

import os
import logging
from flask import Blueprint, jsonify, current_app, send_from_directory
from calculations import format_file_size, format_photo_date

logger = logging.getLogger(__name__)

photos_bp = Blueprint('photos', __name__)


@photos_bp.route('/api/photos')
def list_photos():
    """
    List all photos with metadata.
    
    Returns:
        JSON response with photo list
    """
    camera_service = current_app.config['services']['camera_service']
    
    result = camera_service.list_photos()
    
    if result.is_success:
        # Transform PhotoMetadata to JSON-serializable dict
        photos_list = []
        for photo in result.value:
            photos_list.append({
                'filename': photo.filename,
                'timestamp': photo.timestamp,
                'displayDate': format_photo_date(photo.timestamp),
                'fileSize': photo.file_size,
                'displaySize': format_file_size(photo.file_size),
                'path': photo.path
            })
        
        return jsonify({
            'status': 'success',
            'photos': photos_list,
            'count': len(photos_list)
        })
    else:
        return jsonify({
            'status': 'error',
            'message': result.error,
            'photos': []
        }), 500


@photos_bp.route('/photos/<filename>')
def serve_photo(filename):
    """
    Serve a photo file from the photos directory.
    
    Args:
        filename: Name of the photo file
        
    Returns:
        Photo file or 404 error
    """
    # Get the absolute path to the photos directory (in server folder)
    photos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'photos'))
    
    # Serve photo from photos directory
    return send_from_directory(photos_dir, filename)
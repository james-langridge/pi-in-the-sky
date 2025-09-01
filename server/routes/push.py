"""Push notification routes."""

import logging
from flask import Blueprint, request, jsonify, current_app
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

push_bp = Blueprint('push', __name__, url_prefix='/api/push')


@push_bp.route('/vapid-key')
def get_vapid_key():
    """
    Get VAPID public key for client subscription.
    
    Returns:
        JSON response with public key
    """
    notification_service = current_app.config['services']['notification_service']
    
    if not notification_service:
        return jsonify({
            "status": "error",
            "message": "Push notifications not configured"
        }), 503
    
    return jsonify({
        "publicKey": notification_service.vapid_public_key
    })


@push_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Register a new push notification subscription.
    
    Expected JSON:
        {
            "endpoint": "https://...",
            "keys": {
                "auth": "...",
                "p256dh": "..."
            }
        }
        
    Returns:
        JSON response with subscription status
    """
    notification_service = current_app.config['services']['notification_service']
    subscription_storage = current_app.config['services']['subscription_storage']
    
    if not notification_service:
        return jsonify({
            "status": "error",
            "message": "Push notifications not configured"
        }), 503
    
    if not request.json:
        return jsonify({
            "status": "error",
            "message": "No subscription data provided"
        }), 400
    
    subscription_info = request.json
    
    # Validate subscription format
    if not subscription_info.get('endpoint'):
        return jsonify({
            "status": "error",
            "message": "Missing endpoint in subscription"
        }), 400
    
    if not subscription_info.get('keys'):
        return jsonify({
            "status": "error",
            "message": "Missing keys in subscription"
        }), 400
    
    required_keys = ['auth', 'p256dh']
    for key in required_keys:
        if key not in subscription_info['keys']:
            return jsonify({
                "status": "error",
                "message": f"Missing {key} in subscription keys"
            }), 400
    
    # Store subscription
    try:
        subscription_storage.add_subscription(
            endpoint=subscription_info['endpoint'],
            p256dh=subscription_info['keys']['p256dh'],
            auth=subscription_info['keys']['auth'],
            user_agent=request.headers.get('User-Agent')
        )
        logger.info(f"Added subscription: {subscription_info['endpoint'][:50]}...")
        
        # Test the subscription with a welcome notification
        try:
            webpush(
                subscription_info=subscription_info,
                data='{"title": "Notifications Enabled", "body": "You will receive alerts when motion is detected"}',
                vapid_private_key=notification_service.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{notification_service.vapid_email}"
                },
                ttl=86400  # 24 hours TTL for iOS compatibility
            )
            logger.info("Sent welcome notification")
        except WebPushException as e:
            logger.error(f"Failed to send welcome notification: {e}")
            # Don't fail subscription if welcome fails
        
        return jsonify({
            "status": "success",
            "message": "Subscription added successfully"
        })
    except Exception as e:
        logger.error(f"Failed to add subscription: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to add subscription: {str(e)}"
        }), 500


@push_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    Remove a push notification subscription.
    
    Expected JSON:
        {
            "endpoint": "https://..."
        }
        
    Returns:
        JSON response with status
    """
    subscription_storage = current_app.config['services']['subscription_storage']
    
    if not request.json or not request.json.get('endpoint'):
        return jsonify({
            "status": "error",
            "message": "No endpoint provided"
        }), 400
    
    endpoint = request.json['endpoint']
    
    try:
        removed = subscription_storage.remove_subscription(endpoint)
        if removed:
            logger.info(f"Removed subscription: {endpoint[:50]}...")
            return jsonify({
                "status": "success",
                "message": "Subscription removed successfully"
            })
        else:
            return jsonify({
                "status": "success",
                "message": "Subscription not found (may have been already removed)"
            })
    except Exception as e:
        logger.error(f"Failed to remove subscription: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to remove subscription: {str(e)}"
        }), 500


@push_bp.route('/test', methods=['POST'])
def test_notification():
    """
    Send a test notification to a specific endpoint.
    
    Expected JSON:
        {
            "endpoint": "https://..."
        }
        
    Returns:
        JSON response with test result
    """
    notification_service = current_app.config['services']['notification_service']
    subscription_storage = current_app.config['services']['subscription_storage']
    
    if not notification_service:
        return jsonify({
            "status": "error",
            "message": "Push notifications not configured"
        }), 503
    
    if not request.json or not request.json.get('endpoint'):
        return jsonify({
            "status": "error",
            "message": "No endpoint provided"
        }), 400
    
    endpoint = request.json['endpoint']
    
    # Use notification service to send test notification
    result = notification_service.test_notification(endpoint)
    
    if result.is_success:
        return jsonify({
            "status": "success",
            "message": "Test notification sent successfully"
        })
    else:
        # Determine appropriate status code based on error
        if "No subscription found" in result.error:
            status_code = 404
        elif "no longer valid" in result.error:
            status_code = 410
        else:
            status_code = 500
        
        return jsonify({
            "status": "error",
            "message": result.error
        }), status_code
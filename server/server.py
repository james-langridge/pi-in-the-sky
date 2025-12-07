"""Flask server for Raspberry Pi camera streaming."""

import logging
import os

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Loaded .env file")
except ImportError:
    logging.info("python-dotenv not installed, using system environment variables only")
except Exception as e:
    logging.warning(f"Could not load .env file: {e}")

from config import AppConfig
from app_factory import create_app
from log_handler import setup_memory_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up in-memory log handler for web UI access
setup_memory_handler(max_entries=500)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Flask server."""
    # Load configuration
    config = AppConfig()
    
    # Create Flask app using factory
    app = create_app(config)
    
    # Check for SSL certificates
    ssl_cert_path = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
    ssl_key_path = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')
    
    ssl_context = None
    if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        ssl_context = (ssl_cert_path, ssl_key_path)
        logger.info("HTTPS enabled with SSL certificates")
        logger.info(f"Starting HTTPS server on {config.host}:{config.port}")
    else:
        logger.info("No SSL certificates found, running HTTP only")
        logger.info(f"Starting HTTP server on {config.host}:{config.port}")
    
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"CORS origins: {config.cors_origins}")
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug,
        threaded=True,
        ssl_context=ssl_context
    )


if __name__ == '__main__':
    main()
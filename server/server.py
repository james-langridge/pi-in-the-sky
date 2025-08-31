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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Flask server."""
    # Load configuration
    config = AppConfig()
    
    # Create Flask app using factory
    app = create_app(config)
    
    # Run the server
    logger.info(f"Starting server on {config.host}:{config.port}")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"CORS origins: {config.cors_origins}")
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
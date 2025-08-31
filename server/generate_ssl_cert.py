#!/usr/bin/env python3
"""Generate self-signed SSL certificate for HTTPS development."""

import os
import subprocess
import sys


def generate_ssl_certificate():
    """Generate a self-signed SSL certificate for development."""
    ssl_dir = os.path.join(os.path.dirname(__file__), 'ssl')
    cert_path = os.path.join(ssl_dir, 'cert.pem')
    key_path = os.path.join(ssl_dir, 'key.pem')
    
    # Check if certificates already exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        response = input("SSL certificates already exist. Regenerate? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing certificates.")
            return
    
    # Create SSL directory if it doesn't exist
    os.makedirs(ssl_dir, exist_ok=True)
    
    # Generate self-signed certificate using OpenSSL
    print("Generating self-signed SSL certificate...")
    
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
        '-keyout', key_path, '-out', cert_path,
        '-days', '365', '-nodes', '-subj',
        '/C=US/ST=State/L=City/O=PiCamera/CN=localhost'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error generating certificate: {result.stderr}")
            sys.exit(1)
        
        print(f"✓ SSL certificate generated successfully!")
        print(f"  Certificate: {cert_path}")
        print(f"  Private key: {key_path}")
        print("\nNote: This is a self-signed certificate for development only.")
        print("Browsers will show a security warning that you'll need to accept.")
        
    except FileNotFoundError:
        print("Error: OpenSSL is not installed.")
        print("Install it with:")
        print("  Ubuntu/Debian: sudo apt-get install openssl")
        print("  macOS: brew install openssl")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating certificate: {e}")
        sys.exit(1)


if __name__ == '__main__':
    generate_ssl_certificate()
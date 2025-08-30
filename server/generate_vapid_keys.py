#!/usr/bin/env python3
"""Generate VAPID keys for Web Push notifications."""

from py_vapid import Vapid
import os


def generate_vapid_keys():
    """Generate a new VAPID key pair using py-vapid library."""
    import base64
    from cryptography.hazmat.primitives import serialization
    
    vapid = Vapid()
    vapid.generate_keys()
    
    # Get private key as PEM string for server
    private_key = vapid.private_pem().decode('utf-8')
    
    # Get public key in application server format (URL-safe base64)
    public_key_obj = vapid.public_key
    public_bytes = public_key_obj.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    return private_key, public_key


def save_to_env_file(private_key, public_key, email):
    """Save VAPID keys to .env file and private key to separate file."""
    server_dir = os.path.dirname(__file__)
    env_file = os.path.join(server_dir, '.env')
    key_file = os.path.join(server_dir, 'vapid_private_key.pem')
    
    # Check if .env already exists
    if os.path.exists(env_file):
        response = input(f".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Keys not saved.")
            return False
    
    # Save private key to separate file
    with open(key_file, 'w') as f:
        f.write(private_key)
    
    # Save config to .env with file path reference
    env_content = f"""# VAPID Keys for Web Push Notifications - Generated with py_vapid
# Generated automatically - DO NOT SHARE PRIVATE KEY

VAPID_PRIVATE_KEY_FILE=vapid_private_key.pem
VAPID_PUBLIC_KEY={public_key}
VAPID_EMAIL={email}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"Private key saved to {key_file}")
    print(f"Configuration saved to {env_file}")
    return True


def main():
    """Main function to generate and display VAPID keys."""
    print("=" * 60)
    print("VAPID Key Generator for Web Push Notifications")
    print("=" * 60)
    print()
    
    # Get email for VAPID
    email = input("Enter contact email for VAPID (e.g., admin@example.com): ").strip()
    if not email:
        email = "admin@example.com"
    
    print("\nGenerating VAPID keys...")
    private_key, public_key = generate_vapid_keys()
    
    print("\n" + "=" * 60)
    print("Generated VAPID Keys:")
    print("=" * 60)
    
    print("\n1. PUBLIC KEY (safe to share, use in client-side code):")
    print("-" * 60)
    print(public_key)
    
    print("\n2. PRIVATE KEY (KEEP SECRET, use only on server):")
    print("-" * 60)
    print(private_key)
    
    print("\n3. VAPID EMAIL:")
    print("-" * 60)
    print(email)
    
    print("\n" + "=" * 60)
    print("How to use these keys:")
    print("=" * 60)
    print()
    print("Option 1: Set as environment variables")
    print("-" * 40)
    print("Export these before running the server:")
    print()
    private_key_escaped = private_key.replace('\n', '\\n')
    print(f"export VAPID_PRIVATE_KEY='{private_key_escaped}'")
    print(f"export VAPID_PUBLIC_KEY='{public_key}'")
    print(f"export VAPID_EMAIL='{email}'")
    
    print("\nOption 2: Save to .env file")
    print("-" * 40)
    save_response = input("Save to .env file? (y/N): ")
    if save_response.lower() == 'y':
        if save_to_env_file(private_key, public_key, email):
            print("\nTo use the .env file, install python-dotenv:")
            print("  pip install python-dotenv")
            print("\nThen add to server.py:")
            print("  from dotenv import load_dotenv")
            print("  load_dotenv()")
    
    print("\n" + "=" * 60)
    print("Security Notes:")
    print("=" * 60)
    print("- NEVER commit the private key to version control")
    print("- Add .env to your .gitignore file")
    print("- The public key is safe to include in client-side code")
    print("- Rotate keys periodically for better security")
    print()


if __name__ == "__main__":
    main()
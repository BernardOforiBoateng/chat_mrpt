#!/usr/bin/env python3
"""
Setup production environment for ChatMRPT.
Generates secure secrets and provides deployment instructions.
"""
import secrets
import sys


def generate_secure_env():
    """Generate secure environment variables for production."""
    print("=" * 70)
    print("ChatMRPT Production Environment Setup")
    print("=" * 70)
    print()
    
    # Generate secure secret key
    secret_key = secrets.token_hex(32)
    print("1. Generated Secret Key:")
    print(f"   SECRET_KEY={secret_key}")
    print()
    
    # Generate admin key
    admin_key = secrets.token_urlsafe(16)
    print("2. Generated Admin Key:")
    print(f"   ADMIN_KEY={admin_key}")
    print()
    
    print("3. Required Environment Variables:")
    print("   FLASK_ENV=production")
    print("   OPENAI_API_KEY=<your-new-openai-api-key>")
    print()
    
    print("4. AWS-specific variables (when deploying):")
    print("   DATABASE_URL=postgresql://username:password@host:port/database")
    print("   AWS_REGION=us-east-1")
    print("   CORS_ORIGINS=https://yourdomain.com")
    print()
    
    print("=" * 70)
    print("SECURITY CHECKLIST:")
    print("=" * 70)
    print("✓ 1. Rotate your OpenAI API key immediately")
    print("✓ 2. Never commit .env files to version control")
    print("✓ 3. Use AWS Secrets Manager for production secrets")
    print("✓ 4. Enable HTTPS for all production traffic")
    print("✓ 5. Set up AWS WAF for additional protection")
    print("✓ 6. Configure CloudWatch for monitoring")
    print("✓ 7. Enable AWS GuardDuty for threat detection")
    print()
    
    print("NEXT STEPS:")
    print("1. Create a new .env file with the values above")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Test locally: python run.py")
    print("4. Deploy to AWS using your chosen method")
    print()
    
    # Create .env template
    env_template = f"""# ChatMRPT Production Environment Variables
# Generated on {secrets.token_hex(4)}

# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY={secret_key}

# OpenAI Configuration
OPENAI_API_KEY=<your-new-openai-api-key-here>

# Admin Configuration
ADMIN_KEY={admin_key}

# Database Configuration (for AWS RDS)
DATABASE_URL=postgresql://username:password@host:port/database

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# AWS Configuration
AWS_REGION=us-east-1
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=INFO
"""
    
    response = input("Would you like to save this configuration to .env.production? (y/n): ")
    if response.lower() == 'y':
        with open('.env.production', 'w') as f:
            f.write(env_template)
        print("\n✓ Configuration saved to .env.production")
        print("  Remember to update the placeholder values!")
    
    print("\n🔒 Keep these values secure and never share them!")


if __name__ == "__main__":
    generate_secure_env()
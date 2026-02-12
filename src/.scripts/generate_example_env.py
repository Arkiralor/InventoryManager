#!/usr/bin/env python3
"""
Script to generate an example.env file from an existing .env file.
Replaces sensitive values with dummy placeholders and adds descriptions.
"""

import os
import re
from pathlib import Path

# Mapping of environment variable names/patterns to descriptions and dummy values
ENV_DESCRIPTIONS = {
    # General Settings
    "APP_NAME": ("Name of the application", '"YourAppName"'),
    "DOMAIN_URL": ("The main domain URL for the application", '"https://www.example.com"'),
    "OWNER_EMAIL": ("Email address of the application owner", '"owner@example.com"'),
    "CONTACT_EMAIL": ("Contact email for the application", '"contact@example.com"'),
    
    # System Settings
    "SECRET_KEY": ("Django secret key - generate a new one for production", '"your-secret-key-here-generate-using-django"'),
    "DEBUG": ("Enable/disable debug mode (True/False)", "True"),
    "ENV_TYPE": ("Environment type (DEV, STAGING, PROD)", '"DEV"'),
    "ALLOWED_HOSTS": ("Comma-separated list of allowed hosts", '"localhost, 127.0.0.1"'),
    "JWT_ALGORITHM": ("Algorithm used for JWT encoding", '"HS256"'),
    "CORS_ORIGIN_WHITELIST": ("Comma-separated list of allowed CORS origins", '"localhost:8000, 127.0.0.1:8000"'),
    "DATA_UPLOAD_MAX_MEMORY_SIZE": ("Maximum upload size in bytes (default: 25MB)", "26214400"),
    "DATA_UPLOAD_MAX_NUMBER_FIELDS": ("Maximum number of form fields", "10000"),
    
    # Database Settings
    "DB_NAME": ("PostgreSQL database name", '"your_database_name"'),
    "DB_HOST": ("PostgreSQL database host", '"localhost"'),
    "DB_PORT": ("PostgreSQL database port", '"5432"'),
    "DB_USER": ("PostgreSQL database username", '"your_db_user"'),
    "DB_PASSWORD": ("PostgreSQL database password", '"your_db_password"'),
    
    # MongoDB Settings
    "MONGO_URI": ("MongoDB connection URI", '"mongodb://localhost:27017"'),
    "MONGO_NAME": ("MongoDB database name", '"your_mongo_db"'),
    "MONGO_HOST": ("MongoDB host", '"localhost"'),
    "MONGO_PORT": ("MongoDB port", '"27017"'),
    "MONGO_USER": ("MongoDB username", '"your_mongo_user"'),
    "MONGO_PASSWORD": ("MongoDB password", '"your_mongo_password"'),
    
    # Internationalization Settings
    "LANGUAGE_CODE": ("Default language code", '"en-us"'),
    "TIME_ZONE": ("Application timezone", '"UTC"'),
    "USE_I18N": ("Enable internationalization", "True"),
    "USE_TZ": ("Enable timezone support", "True"),
    
    # Authentication Settings
    "OTP_ATTEMPT_LIMIT": ("Maximum OTP verification attempts", "5"),
    "OTP_ATTEMPT_TIMEOUT": ("OTP attempt timeout in minutes", "30"),
    
    # AWS Settings
    "USE_AWS_S3": ("Enable AWS S3 storage (True/False)", "False"),
    "SNS_SENDER_ID": ("AWS SNS sender ID for SMS", '"YourSenderID"'),
    "AWS_ACCESS_KEY_ID": ("AWS access key ID", '"your-aws-access-key-id"'),
    "AWS_SECRET_ACCESS_KEY": ("AWS secret access key", '"your-aws-secret-access-key"'),
    "AWS_REGION_NAME": ("AWS region name", '"us-east-1"'),
    "AWS_STORAGE_BUCKET_NAME": ("AWS S3 bucket name", '"your-s3-bucket-name"'),
    "AWS_S3_ARN": ("AWS S3 bucket ARN", '"arn:aws:s3:::your-bucket-name"'),
    
    # Redis Settings
    "REDIS_HOST": ("Redis server host", '"127.0.0.1"'),
    "REDIS_PORT": ("Redis server port", '"6379"'),
    "REDIS_DB": ("Redis database number", '"0"'),
    "REDIS_PASSWORD": ("Redis password (leave empty if none)", '""'),
    
    # Cron Settings
    "CRON_ENABLED": ("Enable cron jobs (True/False)", "True"),
    
    # Email Settings
    "EMAIL_HOST": ("SMTP server hostname", '"smtp.gmail.com"'),
    "EMAIL_USE_TLS": ("Use TLS for email (True/False)", '"True"'),
    "EMAIL_USE_SSL": ("Use SSL for email (True/False)", '"False"'),
    "EMAIL_PORT": ("SMTP server port", "587"),
    "EMAIL_HOST_USER": ("SMTP username/email", '"your-email@gmail.com"'),
    "EMAIL_HOST_PASSWORD": ("SMTP password or app password", '"your-email-app-password"'),
    "MANAGER_EMAIL": ("Manager notification email", '"manager@example.com"'),
}


def parse_env_file(env_path: Path) -> list[tuple[str, str, bool]]:
    """
    Parse the .env file and return a list of tuples.
    Each tuple contains: (line_content, var_name, is_comment_or_empty)
    """
    lines = []
    with open(env_path, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            stripped = line.strip()
            
            # Check if it's a comment or empty line
            if not stripped or stripped.startswith('#'):
                lines.append((line, None, True))
                continue
            
            # Try to parse as KEY = VALUE or KEY=VALUE
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', stripped)
            if match:
                var_name = match.group(1)
                lines.append((line, var_name, False))
            else:
                # Keep line as-is if it doesn't match expected format
                lines.append((line, None, True))
    
    return lines


def generate_example_env(env_path: Path, output_path: Path) -> None:
    """
    Generate an example.env file with dummy values and descriptions.
    """
    lines = parse_env_file(env_path)
    
    output_lines = []
    output_lines.append("# Example Environment Configuration")
    output_lines.append("# Copy this file to .env and update the values accordingly")
    output_lines.append("#")
    output_lines.append("# Generated from .env - DO NOT commit your actual .env file!")
    output_lines.append("")
    
    for line, var_name, is_special in lines:
        if is_special:
            # Keep comments and empty lines as-is
            output_lines.append(line)
        else:
            # Get description and dummy value
            if var_name in ENV_DESCRIPTIONS:
                description, dummy_value = ENV_DESCRIPTIONS[var_name]
                output_lines.append(f"# {description}")
                output_lines.append(f"{var_name} = {dummy_value}")
            else:
                # Unknown variable - keep original with generic description
                output_lines.append(f"# {var_name} configuration")
                # Extract original value to determine type
                match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line.strip())
                if match:
                    original_value = match.group(2).strip()
                    # Check if it looks like a string, number, or boolean
                    if original_value.lower() in ('true', 'false'):
                        output_lines.append(f'{var_name} = {original_value}')
                    elif original_value.isdigit():
                        output_lines.append(f'{var_name} = {original_value}')
                    else:
                        output_lines.append(f'{var_name} = "your-{var_name.lower()}-here"')
                else:
                    output_lines.append(f'{var_name} = "your-value-here"')
    
    # Write output file
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))
        f.write('\n')
    
    print(f"Generated {output_path}")
    print(f"Processed {sum(1 for _, var, is_special in lines if not is_special)} environment variables")


def main():
    # Determine paths
    script_dir = Path(__file__).parent  # src/.scripts
    project_root = script_dir.parent
    src_dir = project_root
    env_path = src_dir / '.env'
    output_path = src_dir / 'example.env'
    
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        exit(1)
    
    generate_example_env(env_path, output_path)
    print("Done!")


if __name__ == "__main__":
    main()

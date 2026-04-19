"""
Authentication Configuration
Loads settings from environment variables for portability across CLI, web, and mobile.
"""

import os
import secrets
from dataclasses import dataclass


@dataclass
class AuthConfig:
    """Authentication configuration loaded from environment or defaults."""

    # SMTP settings for OTP delivery
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_sender: str = ""
    smtp_password: str = ""

    # JWT settings
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # API Global Security
    nsu_api_key: str = "dev_secret_key"

    # OTP settings
    otp_length: int = 6
    otp_expiry_seconds: int = 300  # 5 minutes

    # NSU domain
    allowed_domain: str = "northsouth.edu"

    # Data paths
    sessions_file: str = ""

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load configuration from environment variables."""
        # Auto-generate JWT secret if not provided
        jwt_secret = os.environ.get("NSU_JWT_SECRET", "")
        if not jwt_secret:
            # Generate and persist a secret for this installation
            secret_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", ".jwt_secret"
            )
            if os.path.exists(secret_file):
                with open(secret_file, "r") as f:
                    jwt_secret = f.read().strip()
            else:
                jwt_secret = secrets.token_hex(32)
                os.makedirs(os.path.dirname(secret_file), exist_ok=True)
                with open(secret_file, "w") as f:
                    f.write(jwt_secret)

        sessions_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "sessions.json"
        )

        return cls(
            smtp_host=os.environ.get("NSU_SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.environ.get("NSU_SMTP_PORT", "587")),
            smtp_sender=os.environ.get("NSU_SMTP_SENDER", ""),
            smtp_password=os.environ.get("NSU_SMTP_PASSWORD", ""),
            jwt_secret=jwt_secret,
            jwt_algorithm="HS256",
            jwt_expiry_hours=int(os.environ.get("NSU_JWT_EXPIRY_HOURS", "24")),
            
            nsu_api_key=os.environ.get("NSU_API_KEY", "dev_secret_key"),
            otp_length=6,
            otp_expiry_seconds=int(os.environ.get("NSU_OTP_EXPIRY_SECONDS", "300")),
            allowed_domain="northsouth.edu",
            sessions_file=sessions_file,
        )

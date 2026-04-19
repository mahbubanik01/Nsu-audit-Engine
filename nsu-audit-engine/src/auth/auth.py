"""
NSU Audit Engine - Authentication System

Provides:
- NSU email validation (@northsouth.edu only)
- OTP generation and email delivery
- JWT token issuance and verification

Designed for cross-platform use: CLI, Web API, Mobile.
"""

import re
import random
import string
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from dataclasses import dataclass, field

try:
    import jwt  # PyJWT
except ImportError:
    jwt = None

from auth.config import AuthConfig


# ─────────────────────────────────────────────────────────────────────────────
# Email Validation
# ─────────────────────────────────────────────────────────────────────────────

class NSUEmailValidator:
    """Validates that an email belongs to North South University."""

    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9._%+-]+@northsouth\.edu$", re.IGNORECASE
    )

    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email is a valid @northsouth.edu address."""
        return bool(cls.EMAIL_REGEX.match(email.strip()))

    @classmethod
    def validate(cls, email: str) -> Tuple[bool, str]:
        """
        Validate email and return (is_valid, message).
        Provides user-friendly error messages.
        """
        email = email.strip()
        if not email:
            return False, "Email address cannot be empty."
        if "@" not in email:
            return False, "Invalid email format. Please provide a valid email."
        domain = email.split("@")[1].lower()
        if domain != "northsouth.edu":
            return False, (
                f"Only @northsouth.edu emails are allowed.\n"
                f"  You entered: @{domain}\n"
                f"  Expected:    @northsouth.edu"
            )
        if not cls.EMAIL_REGEX.match(email):
            return False, "Invalid email format. Check for special characters."
        return True, "Valid NSU email."


# ─────────────────────────────────────────────────────────────────────────────
# OTP Manager
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OTPRecord:
    """Single OTP record with expiry tracking."""
    code: str
    email: str
    created_at: float
    expires_at: float
    verified: bool = False


class OTPManager:
    """Generates, sends, and verifies One-Time Passwords."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self._pending_otps: dict[str, OTPRecord] = {}  # email -> OTPRecord

    def generate(self, email: str) -> str:
        """Generate a new OTP for the given email."""
        code = "".join(random.choices(string.digits, k=self.config.otp_length))
        now = time.time()
        self._pending_otps[email.lower()] = OTPRecord(
            code=code,
            email=email.lower(),
            created_at=now,
            expires_at=now + self.config.otp_expiry_seconds,
        )
        return code

    def verify(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Verify an OTP.
        Returns (is_valid, message).
        """
        email = email.lower()
        record = self._pending_otps.get(email)

        if not record:
            return False, "No OTP was requested for this email. Please request a new one."

        if record.verified:
            return False, "This OTP has already been used. Please request a new one."

        if time.time() > record.expires_at:
            del self._pending_otps[email]
            return False, "OTP has expired. Please request a new one."

        if record.code != code.strip():
            return False, "Incorrect OTP. Please check and try again."

        # Mark as verified and clean up
        record.verified = True
        del self._pending_otps[email]
        return True, "OTP verified successfully."

    def send_otp_email(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Send OTP via email using SMTP.
        Returns (success, message).
        """
        if not self.config.smtp_sender or not self.config.smtp_password:
            # Fallback: print OTP to console (development mode)
            return True, (
                f"[DEV MODE] SMTP not configured.\n"
                f"  Your OTP is: {code}\n"
                f"  (In production, this would be sent to {email})"
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_sender
            msg["To"] = email
            msg["Subject"] = "NSU Audit Engine - Login Verification Code"

            body = f"""
Hello,

Your NSU Audit Engine verification code is:

    {code}

This code expires in {self.config.otp_expiry_seconds // 60} minutes.

If you did not request this code, please ignore this email.

— NSU Audit Engine
"""
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_sender, self.config.smtp_password)
                server.send_message(msg)

            return True, f"Verification code sent to {email}"

        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed. Check your email credentials."
        except smtplib.SMTPException as e:
            return False, f"Failed to send email: {e}"
        except Exception as e:
            return False, f"Unexpected error sending email: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Token Manager (JWT)
# ─────────────────────────────────────────────────────────────────────────────

class TokenManager:
    """Issues and verifies JWT tokens for authenticated sessions."""

    def __init__(self, config: AuthConfig):
        self.config = config
        if jwt is None:
            raise ImportError(
                "PyJWT is required for authentication.\n"
                "Install it with: pip install PyJWT"
            )

    def issue_token(self, email: str) -> str:
        """Issue a signed JWT token for an authenticated user."""
        now = time.time()
        payload = {
            "sub": email.lower(),
            "iat": int(now),
            "exp": int(now + self.config.jwt_expiry_hours * 3600),
            "iss": "nsu-audit-engine",
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    def verify_token(self, token: str) -> Tuple[bool, Optional[str], str]:
        """
        Verify a JWT token.
        Returns (is_valid, email_or_none, message).
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                issuer="nsu-audit-engine",
            )
            email = payload.get("sub")
            if not email:
                return False, None, "Token missing subject claim."

            # Verify it's still an NSU email
            if not NSUEmailValidator.is_valid(email):
                return False, None, "Token issued for non-NSU email."

            return True, email, f"Authenticated as {email}"

        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired. Please log in again."
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Auth Service (Orchestrator)
# ─────────────────────────────────────────────────────────────────────────────

class AuthService:
    """
    High-level authentication service.
    Orchestrates: email validation → OTP → token issuance.
    Works identically across CLI, web, and mobile.
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig.from_env()
        self.email_validator = NSUEmailValidator()
        self.otp_manager = OTPManager(self.config)
        self.token_manager = TokenManager(self.config)

    def request_otp(self, email: str) -> Tuple[bool, str]:
        """
        Step 1: Validate email and send OTP.
        Returns (success, message).
        """
        # Validate email
        is_valid, msg = self.email_validator.validate(email)
        if not is_valid:
            return False, msg

        # Generate OTP
        code = self.otp_manager.generate(email)

        # Send OTP
        success, send_msg = self.otp_manager.send_otp_email(email, code)
        return success, send_msg

    def verify_and_issue_token(self, email: str, otp_code: str) -> Tuple[bool, Optional[str], str]:
        """
        Step 2: Verify OTP and issue JWT token.
        Returns (success, token_or_none, message).
        """
        # Verify OTP
        is_valid, msg = self.otp_manager.verify(email, otp_code)
        if not is_valid:
            return False, None, msg

        # Issue token
        token = self.token_manager.issue_token(email)
        return True, token, f"Authenticated as {email}"

    def verify_token(self, token: str) -> Tuple[bool, Optional[str], str]:
        """
        Verify an existing token (for subsequent requests).
        Returns (is_valid, email_or_none, message).
        """
        return self.token_manager.verify_token(token)

    def cli_login_flow(self) -> Optional[str]:
        """
        Interactive CLI login flow.
        Returns token on success, None on failure.
        """
        print("\n" + "=" * 60)
        print("NSU AUDIT ENGINE - LOGIN")
        print("=" * 60)
        print("Only @northsouth.edu emails are accepted.\n")

        # Step 1: Get email
        email = input("Enter your NSU email: ").strip()
        success, msg = self.request_otp(email)
        print(f"\n{msg}")
        if not success:
            return None

        # Step 2: Get OTP
        print()
        otp_code = input("Enter the verification code: ").strip()
        success, token, msg = self.verify_and_issue_token(email, otp_code)
        print(f"\n{msg}")

        if success:
            print(f"\n✓ Login successful!")
            print(f"  Your session token has been saved.")
            return token
        else:
            print(f"\n✗ Login failed.")
            return None

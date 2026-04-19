#!/usr/bin/env python3
"""
NSU Graduation Audit Engine - Main CLI Application

Command-line tool for auditing student graduation eligibility.
Supports three levels of analysis:
  Level 1: Credit Tally
  Level 2: GPA Calculation with Waivers
  Level 3: Complete Graduation Audit

Authentication:
  Only verified @northsouth.edu emails can use this tool.

Supported transcript formats:
  .csv, .pdf, .docx

Usage:
    python main.py login
    python main.py --level 1 --transcript data/transcript.csv
    python main.py --level 1 --transcript data/transcript.pdf
    python main.py --level 3 --transcript data/transcript.docx --program-type BBA
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Set

# Add src to path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Core imports
import parsers.csv_parser as csv_parser
import parsers.md_parser as md_parser
import models.program as program_module
import calculators.credit_calculator as credit_calc
import calculators.gpa_calculator as gpa_calc
import calculators.audit_calculator as audit_calc

# Auth imports
from auth.auth import AuthService, NSUEmailValidator
from auth.session import SessionStore
from auth.config import AuthConfig

# Document router
from parsers.document_router import DocumentRouter

TranscriptParser = csv_parser.TranscriptParser
MarkdownParser = md_parser.MarkdownParser
ProgramFactory = program_module.ProgramFactory
CreditCalculator = credit_calc.CreditCalculator
GPACalculator = gpa_calc.GPACalculator
AuditCalculator = audit_calc.AuditCalculator


class AuditCLI:
    """Command-line interface for the audit engine with authentication"""

    def __init__(self):
        self.parser = self._create_parser()
        self.config = AuthConfig.from_env()
        self.session_store = SessionStore(self.config)
        self.auth_service = AuthService(self.config)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='NSU Graduation Audit Engine',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Authentication:
  python main.py login                 # Login with NSU email
  python main.py logout                # Clear saved session
  python main.py whoami                # Show current session

Audit Examples:
  python main.py -l 1 -t transcript.csv
  python main.py -l 2 -t transcript.pdf
  python main.py -l 3 -t transcript.docx --program-type BBA --detailed

Supported Formats: .csv, .pdf, .docx
            """
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest='command')

        # Login command
        subparsers.add_parser('login', help='Login with NSU email')

        # Logout command
        subparsers.add_parser('logout', help='Clear saved session')

        # Whoami command
        subparsers.add_parser('whoami', help='Show current session')

        # Audit arguments (work without subcommand for backward compat)
        parser.add_argument(
            '-l', '--level',
            type=int,
            choices=[1, 2, 3],
            help='Analysis level (1=Credits, 2=GPA, 3=Full Audit)'
        )

        parser.add_argument(
            '-t', '--transcript',
            type=str,
            help='Path to transcript file (.csv, .pdf, .docx)'
        )

        parser.add_argument(
            '-p', '--program',
            type=str,
            help='Path to program requirements markdown file'
        )

        parser.add_argument(
            '--id', type=str, help='Student ID'
        )

        parser.add_argument(
            '--name', type=str, help='Student name'
        )

        parser.add_argument(
            '--program-type',
            type=str,
            choices=['BBA', 'CSE'],
            help='Program type (use if no program file provided)'
        )

        parser.add_argument(
            '--waive',
            type=str,
            help='Comma-separated list of courses to waive'
        )

        parser.add_argument(
            '--no-interactive',
            action='store_true',
            help='Disable interactive prompts'
        )

        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown'
        )

        parser.add_argument(
            '-o', '--output',
            type=str,
            help='Save report to file'
        )

        parser.add_argument(
            '--token',
            type=str,
            help='JWT token for pre-authenticated requests (API/mobile/web)'
        )

        parser.add_argument(
            '--skip-auth',
            action='store_true',
            help='Skip authentication (development mode only)'
        )

        return parser

    def run(self, args=None):
        """Run the CLI application"""
        args = self.parser.parse_args(args)

        try:
            # Handle subcommands
            if args.command == 'login':
                self._handle_login()
                return
            elif args.command == 'logout':
                self._handle_logout()
                return
            elif args.command == 'whoami':
                self._handle_whoami()
                return

            # For audit commands, require level and transcript
            if not args.level or not args.transcript:
                self.parser.print_help()
                return

            # Authenticate
            user_email = self._authenticate(args)

            # Validate inputs
            self._validate_args(args)

            # Load transcript (auto-detect format)
            print(f"Loading transcript: {args.transcript}")
            transcript = DocumentRouter.parse(
                args.transcript,
                student_id=args.id,
                student_name=args.name,
                program=args.program_type,
            )
            print(f"✓ Loaded {len(transcript)} course records")

            # Get waived courses
            waived_courses = self._get_waived_courses(args)

            # Run appropriate level
            if args.level == 1:
                report = self._run_level1(transcript)
            elif args.level == 2:
                report = self._run_level2(transcript, waived_courses, args)
            else:
                program = self._load_program(args)
                report = self._run_level3(transcript, program, waived_courses, args)

            # Output report
            self._output_report(report, args.output)
            print("\n✓ Audit complete!")

        except Exception as e:
            print(f"\n✗ Error: {e}", file=sys.stderr)
            sys.exit(1)

    # ─── Authentication ───────────────────────────────────────────────

    def _authenticate(self, args) -> Optional[str]:
        """
        Authenticate the user.
        Priority: --token flag > saved session > interactive login
        Returns the authenticated email or None in dev mode.
        """
        # Dev mode bypass
        if args.skip_auth:
            print("⚠ Authentication skipped (development mode)")
            return None

        # Check --token argument first (for API/mobile/web)
        if args.token:
            is_valid, email, msg = self.auth_service.verify_token(args.token)
            if is_valid:
                print(f"✓ Authenticated as {email}")
                return email
            else:
                print(f"✗ Token authentication failed: {msg}")
                sys.exit(1)

        # Check saved session
        saved_token = self.session_store.get_token()
        if saved_token:
            is_valid, email, msg = self.auth_service.verify_token(saved_token)
            if is_valid:
                print(f"✓ Authenticated as {email}")
                return email
            else:
                # Token expired, clear it
                self.session_store.clear()

        # Interactive login
        if args.no_interactive:
            print("✗ No valid session found. Run `python main.py login` first.")
            sys.exit(1)

        print("No active session. Please log in.\n")
        token = self.auth_service.cli_login_flow()
        if token:
            # Save session
            is_valid, email, _ = self.auth_service.verify_token(token)
            if is_valid:
                self.session_store.save_token(email, token)
                return email
        print("✗ Authentication failed.")
        sys.exit(1)

    def _handle_login(self):
        """Handle the login subcommand."""
        token = self.auth_service.cli_login_flow()
        if token:
            is_valid, email, _ = self.auth_service.verify_token(token)
            if is_valid:
                self.session_store.save_token(email, token)
                print(f"\n✓ Session saved. You can now run audits.")

    def _handle_logout(self):
        """Handle the logout subcommand."""
        self.session_store.clear()
        print("✓ All sessions cleared. You are now logged out.")

    def _handle_whoami(self):
        """Handle the whoami subcommand."""
        saved_token = self.session_store.get_token()
        if not saved_token:
            print("No active session. Run `python main.py login` to authenticate.")
            return

        is_valid, email, msg = self.auth_service.verify_token(saved_token)
        if is_valid:
            print(f"✓ Logged in as: {email}")
        else:
            print(f"✗ Session expired: {msg}")
            print("  Run `python main.py login` to re-authenticate.")

    # ─── Validation ────────────────────────────────────────────────

    def _validate_args(self, args):
        """Validate command-line arguments"""
        if not Path(args.transcript).exists():
            raise FileNotFoundError(f"Transcript file not found: {args.transcript}")

        # Check if format is supported
        if not DocumentRouter.is_supported(args.transcript):
            print(DocumentRouter.get_supported_formats())
            raise ValueError(f"Unsupported transcript format: {args.transcript}")

        if args.level == 3:
            if not args.program and not args.program_type:
                raise ValueError(
                    "Level 3 requires either --program or --program-type"
                )
            if args.program and not Path(args.program).exists():
                raise FileNotFoundError(f"Program file not found: {args.program}")

    def _get_waived_courses(self, args) -> Set[str]:
        """Get set of waived courses from arguments"""
        if not args.waive:
            return set()
        courses = {c.strip().upper() for c in args.waive.split(',')}
        print(f"Waiving courses: {', '.join(sorted(courses))}")
        return courses

    def _load_program(self, args):
        """Load program requirements"""
        if args.program:
            print(f"Loading program requirements: {args.program}")
            program = MarkdownParser.parse_markdown(args.program)
        else:
            print(f"Using built-in {args.program_type} program")
            if args.program_type == 'BBA':
                program = ProgramFactory.create_bba_program()
            else:
                program = ProgramFactory.create_cse_program()
        print(f"✓ Loaded {program.program_name} requirements")
        return program

    # ─── Audit Levels ────────────────────────────────────────────────

    def _run_level1(self, transcript) -> str:
        """Run Level 1: Credit Tally"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 1: CREDIT TALLY ENGINE")
        print("=" * 60)
        report = CreditCalculator.calculate_credits(transcript)
        output = str(report)
        output += "\n" + CreditCalculator.get_detailed_breakdown(report)
        return output

    def _run_level2(self, transcript, waived_courses, args) -> str:
        """Run Level 2: GPA Calculation"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 2: GPA CALCULATOR & WAIVER HANDLER")
        print("=" * 60)
        if not args.no_interactive and not args.waive:
            waivable = ['ENG102', 'BUS112']
            additional = GPACalculator.prompt_for_waivers(waivable)
            waived_courses.update(additional)
        report = GPACalculator.calculate_cgpa(transcript, waived_courses)
        output = str(report)
        output += "\n" + GPACalculator.get_semester_breakdown(report)
        return output

    def _run_level3(self, transcript, program, waived_courses, args) -> str:
        """Run Level 3: Full Audit"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 3: GRADUATION AUDIT ENGINE")
        print("=" * 60)
        if not args.no_interactive and not args.waive and program.waivable_courses:
            additional = GPACalculator.prompt_for_waivers(program.waivable_courses)
            waived_courses.update(additional)
        audit = AuditCalculator.perform_audit(transcript, program, waived_courses)
        if args.detailed:
            output = AuditCalculator.generate_detailed_report(audit)
        else:
            output = str(audit)
        return output

    def _output_report(self, report: str, output_file: Optional[str]):
        """Output report to console and/or file"""
        print(report)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✓ Report saved to: {output_file}")


def main():
    """Main entry point"""
    cli = AuditCLI()
    cli.run()


if __name__ == '__main__':
    main()

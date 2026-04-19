#!/usr/bin/env python3
"""
NSU Graduation Audit Engine - Main CLI Application

Command-line tool for auditing student graduation eligibility.
Supports three levels of analysis:
  Level 1: Credit Tally
  Level 2: GPA Calculation with Waivers
  Level 3: Complete Graduation Audit

Usage:
    python main.py --level 1 --transcript data/transcript.csv
    python main.py --level 2 --transcript data/transcript.csv
    python main.py --level 3 --transcript data/transcript.csv --program data/program.md
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Set

# Add src to path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Now we can import as if we're in the src directory
import parsers.csv_parser as csv_parser
import parsers.md_parser as md_parser
import models.program as program_module
import calculators.credit_calculator as credit_calc
import calculators.gpa_calculator as gpa_calc
import calculators.audit_calculator as audit_calc

TranscriptParser = csv_parser.TranscriptParser
MarkdownParser = md_parser.MarkdownParser
ProgramFactory = program_module.ProgramFactory
CreditCalculator = credit_calc.CreditCalculator
GPACalculator = gpa_calc.GPACalculator
AuditCalculator = audit_calc.AuditCalculator


class AuditCLI:
    """Command-line interface for the audit engine"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='NSU Graduation Audit Engine',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Level 1: Check earned credits
  python main.py -l 1 -t student_transcript.csv
  
  # Level 2: Calculate CGPA
  python main.py -l 2 -t student_transcript.csv
  
  # Level 3: Full graduation audit
  python main.py -l 3 -t student_transcript.csv -p bba_program.md
  
  # With student info
  python main.py -l 3 -t transcript.csv -p program.md \\
                 --id 2014567890 --name "John Doe"
            """
        )
        
        # Required arguments
        parser.add_argument(
            '-l', '--level',
            type=int,
            required=True,
            choices=[1, 2, 3],
            help='Analysis level (1=Credits, 2=GPA, 3=Full Audit)'
        )
        
        parser.add_argument(
            '-t', '--transcript',
            type=str,
            required=True,
            help='Path to student transcript CSV file'
        )
        
        # Optional arguments
        parser.add_argument(
            '-p', '--program',
            type=str,
            help='Path to program requirements markdown file (required for Level 3)'
        )
        
        parser.add_argument(
            '--id',
            type=str,
            help='Student ID'
        )
        
        parser.add_argument(
            '--name',
            type=str,
            help='Student name'
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
            help='Comma-separated list of courses to waive (e.g., ENG102,BUS112)'
        )
        
        parser.add_argument(
            '--no-interactive',
            action='store_true',
            help='Disable interactive waiver prompts'
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
        
        return parser
    
    def run(self, args=None):
        """Run the CLI application"""
        args = self.parser.parse_args(args)
        
        try:
            # Validate inputs
            self._validate_args(args)
            
            # Load transcript
            print(f"Loading transcript: {args.transcript}")
            transcript = TranscriptParser.parse_csv(
                args.transcript,
                student_id=args.id,
                student_name=args.name,
                program=args.program_type
            )
            print(f"✓ Loaded {len(transcript)} course records")
            
            # Get waived courses
            waived_courses = self._get_waived_courses(args)
            
            # Run appropriate level
            if args.level == 1:
                report = self._run_level1(transcript)
            elif args.level == 2:
                report = self._run_level2(transcript, waived_courses, args)
            else:  # Level 3
                program = self._load_program(args)
                report = self._run_level3(transcript, program, waived_courses, args)
            
            # Output report
            self._output_report(report, args.output)
            
            print("\n✓ Audit complete!")
            
        except Exception as e:
            print(f"\n✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _validate_args(self, args):
        """Validate command-line arguments"""
        # Check transcript file exists
        if not Path(args.transcript).exists():
            raise FileNotFoundError(f"Transcript file not found: {args.transcript}")
        
        # Level 3 requires program file or type
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
    
    def _run_level1(self, transcript) -> str:
        """Run Level 1: Credit Tally"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 1: CREDIT TALLY ENGINE")
        print("=" * 60)
        
        report = CreditCalculator.calculate_credits(transcript)
        output = str(report)
        
        # Add detailed breakdown
        output += "\n" + CreditCalculator.get_detailed_breakdown(report)
        
        return output
    
    def _run_level2(self, transcript, waived_courses, args) -> str:
        """Run Level 2: GPA Calculation"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 2: GPA CALCULATOR & WAIVER HANDLER")
        print("=" * 60)
        
        # Interactive waiver prompt if needed
        if not args.no_interactive and not args.waive:
            # Assume common waivable courses
            waivable = ['ENG102', 'BUS112']
            additional = GPACalculator.prompt_for_waivers(waivable)
            waived_courses.update(additional)
        
        report = GPACalculator.calculate_cgpa(transcript, waived_courses)
        output = str(report)
        
        # Add semester breakdown
        output += "\n" + GPACalculator.get_semester_breakdown(report)
        
        return output
    
    def _run_level3(self, transcript, program, waived_courses, args) -> str:
        """Run Level 3: Full Audit"""
        print("\n" + "=" * 60)
        print("RUNNING LEVEL 3: GRADUATION AUDIT ENGINE")
        print("=" * 60)
        
        # Interactive waiver prompt if needed
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
        # Print to console
        print(report)
        
        # Save to file if specified
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

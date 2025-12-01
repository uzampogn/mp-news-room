#!/usr/bin/env python
"""
Main entry point for MP News Feed crew.

Three-phase execution:
1. Phase 1: Deterministic parallel search using SearchCrew
2. Phase 2: Analysis pipeline (filter → context → summary)
3. Phase 3: Email distribution

Phases can be run independently via CLI flags:
  --search-only   Run only Phase 1
  --analyze-only  Run only Phase 2 (requires search_results.json)
  --email-only    Run only Phase 3 (requires summary_report.md)
"""
import sys
import argparse
import warnings
import json
from pathlib import Path
from datetime import datetime, timedelta

from mp_news_feed.crew import MpNewsFeed
from mp_news_feed.search_service import run_search

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
SEARCH_RESULTS_FILE = OUTPUT_DIR / "search_results.json"
SUMMARY_REPORT_FILE = OUTPUT_DIR / "summary_report.md"


def get_inputs():
    """Get standardized inputs for the crew with date awareness."""
    today = datetime.now()
    timeframe_months = 8
    start_date = today - timedelta(days=timeframe_months * 30)

    mp_list_path = Path(__file__).parent.parent.parent / "knowledge" / "mp_list.json"
    with open(mp_list_path, 'r') as f:
        mp_data = json.load(f)

    return {
        'mp_list': mp_data,
        'today': today.strftime('%Y-%m-%d'),
        'timeframe': f'{timeframe_months} months',
        'team_email': 'zampogna.ulysse@gmail.com',
        'focus_areas': 'european politics',
        'date_range': f"{start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}",
    }


def parse_args():
    """Parse CLI arguments for phase control."""
    parser = argparse.ArgumentParser(
        description="MP News Feed - Multi-phase news monitoring system"
    )
    parser.add_argument(
        '--search-only', action='store_true',
        help='Run only Phase 1 (search)'
    )
    parser.add_argument(
        '--analyze-only', action='store_true',
        help='Run only Phase 2 (analysis) using existing search_results.json'
    )
    parser.add_argument(
        '--email-only', action='store_true',
        help='Run only Phase 3 (email) using existing summary_report.md'
    )
    return parser.parse_args()


def load_search_results():
    """Load existing search results from file."""
    if not SEARCH_RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Search results not found at {SEARCH_RESULTS_FILE}\n"
            "Run 'crewai run' or 'crewai run -- --search-only' first."
        )
    with open(SEARCH_RESULTS_FILE, 'r') as f:
        return json.load(f)


def load_summary_report():
    """Load existing summary report from file."""
    if not SUMMARY_REPORT_FILE.exists():
        raise FileNotFoundError(
            f"Summary report not found at {SUMMARY_REPORT_FILE}\n"
            "Run 'crewai run' or 'crewai run -- --analyze-only' first."
        )
    with open(SUMMARY_REPORT_FILE, 'r') as f:
        return f.read()


def run_phase1_search(inputs):
    """Phase 1: Run parallel search for all MPs."""
    print("=" * 60)
    print(f"PHASE 1: Searching {len(inputs['mp_list'])} MPs...")
    print("=" * 60)

    search_results = run_search(
        mp_list=inputs['mp_list'],
        timeframe=inputs['timeframe'],
        today=inputs['today'],
        max_concurrency=10
    )

    # Save search results
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(SEARCH_RESULTS_FILE, 'w') as f:
        json.dump(search_results, f, indent=2)

    print(f"\nPhase 1 complete!")
    print(f"  - MPs searched: {search_results['mp_count']}")
    print(f"  - Articles found: {len(search_results['research_list'])}")
    print(f"  - Results saved to: {SEARCH_RESULTS_FILE}")

    return search_results


def run_phase2_analysis(inputs, search_results):
    """Phase 2: Run analysis pipeline (filter → context → summary)."""
    print("\n" + "=" * 60)
    print("PHASE 2: Running analysis pipeline...")
    print("=" * 60)

    inputs['search_results'] = search_results
    inputs['mp_count'] = search_results['mp_count']

    result = MpNewsFeed().analysis_crew().kickoff(inputs=inputs)

    print(f"\nPhase 2 complete!")
    print(f"  - Report saved to: {SUMMARY_REPORT_FILE}")

    return result


def run_phase3_email(inputs):
    """Phase 3: Send email with existing report."""
    print("\n" + "=" * 60)
    print("PHASE 3: Sending email...")
    print("=" * 60)

    # Load the report to pass to email task
    report_content = load_summary_report()
    inputs['report_content'] = report_content

    result = MpNewsFeed().email_crew().kickoff(inputs=inputs)

    print(f"\nPhase 3 complete!")
    print("  - Email sent successfully")

    return result


def run():
    """Run the crew with optional phase control."""
    args = parse_args()
    inputs = get_inputs()
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Validate mutually exclusive flags
    flags = [args.search_only, args.analyze_only, args.email_only]
    if sum(flags) > 1:
        print("Error: Only one of --search-only, --analyze-only, --email-only can be specified")
        sys.exit(1)

    try:
        if args.search_only:
            # Phase 1 only
            run_phase1_search(inputs)

        elif args.analyze_only:
            # Phase 2 only (load existing search results)
            search_results = load_search_results()
            run_phase2_analysis(inputs, search_results)

        elif args.email_only:
            # Phase 3 only (load existing report)
            run_phase3_email(inputs)

        else:
            # Run all phases (default)
            search_results = run_phase1_search(inputs)
            run_phase2_analysis(inputs, search_results)
            run_phase3_email(inputs)

            print("\n" + "=" * 60)
            print("All phases complete!")
            print("=" * 60)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = get_inputs()
    try:
        MpNewsFeed().crew().train(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 1,
            filename=sys.argv[2] if len(sys.argv) > 2 else "trained_agents_data.pkl",
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        MpNewsFeed().crew().replay(task_id=sys.argv[1] if len(sys.argv) > 1 else "")
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and return the results."""
    inputs = get_inputs()
    try:
        MpNewsFeed().crew().test(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 1,
            openai_model_name=sys.argv[2] if len(sys.argv) > 2 else "gpt-4o-mini",
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()

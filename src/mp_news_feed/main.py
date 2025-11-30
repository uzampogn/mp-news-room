#!/usr/bin/env python
"""
Main entry point for MP News Feed crew.

Two-phase execution:
1. Phase 1: Deterministic parallel search using SearchCrew
2. Phase 2: Analysis pipeline using MpNewsFeed crew
"""
import sys
import warnings
import json
from pathlib import Path
from datetime import datetime, timedelta

from mp_news_feed.crew import MpNewsFeed
from mp_news_feed.search_service import run_search

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


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


def run():
    """Run the crew with deterministic search phase."""
    inputs = get_inputs()
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    try:
        # ========== PHASE 1: Deterministic Search ==========
        print("=" * 60)
        print(f"PHASE 1: Searching {len(inputs['mp_list'])} MPs...")
        print("=" * 60)

        search_results = run_search(
            mp_list=inputs['mp_list'],
            timeframe=inputs['timeframe'],
            today=inputs['today'],
            max_concurrency=10  # Higher concurrency with OpenAI (200K TPM limit)
        )

        # Save search results
        search_output_path = output_dir / "search_results.json"
        with open(search_output_path, 'w') as f:
            json.dump(search_results, f, indent=2)

        print(f"\nPhase 1 complete!")
        print(f"  - MPs searched: {search_results['mp_count']}")
        print(f"  - Articles found: {len(search_results['research_list'])}")
        print(f"  - Results saved to: {search_output_path}")

        # ========== PHASE 2: Agent Analysis ==========
        print("\n" + "=" * 60)
        print("PHASE 2: Running analysis pipeline...")
        print("=" * 60)

        # Pass pre-computed search results to crew
        inputs['search_results'] = search_results
        inputs['mp_count'] = search_results['mp_count']

        result = MpNewsFeed().crew().kickoff(inputs=inputs)

        print("\n" + "=" * 60)
        print("Crew execution complete!")
        print("=" * 60)
        return result

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

"""Main CLI execution script for Kuku Promo Finder.
Runs on the full 50-episode input pack and generates all required raw outputs.
"""

import os
import sys
import argparse

# Add src to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from pipeline import PromoFinderPipeline


def main():
    parser = argparse.ArgumentParser(description="Find high-converting promos from microdrama screenplays.")
    parser.add_argument(
        "--input_dir",
        type=str,
        default=os.path.join(BASE_DIR, "input_pack", "I Married a Broken Soldier. He was a Duke"),
        help="Path to folder containing screenplay txt files"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join(BASE_DIR, "raw_outputs"),
        help="Path to output directory for raw unedited results"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["expert", "gemini"],
        default="expert",
        help="Backend scoring model: 'expert' (fast, built-in) or 'gemini' (frontier LLM)"
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="Optional API key for frontier models"
    )
    parser.add_argument(
        "--max_per_ep",
        type=int,
        default=2,
        help="Max candidate promos retained per episode"
    )

    args = parser.parse_args()

    print("=" * 70)
    print(" KUKU MICRODRAMA AI PROMO FINDER - PRODUCTION PIPELINE")
    print("=" * 70)
    print(f" Input screenplays: {args.input_dir}")
    print(f" Output directory:  {args.output_dir}")
    print(f" Evaluation model:  {args.backend}")
    print("=" * 70)

    pipeline = PromoFinderPipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        backend_type=args.backend,
        api_key=args.api_key,
    )

    results = pipeline.run(max_promos_per_episode=args.max_per_ep)
    summary = results["summary"]
    promos = results["promos"]

    print("\n" + "=" * 70)
    print(" PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f" Episodes Processed:        {summary['episodes_processed']}")
    print(f" Total Promos Discovered:   {summary['total_promos_generated']}")
    print(f" Approved for Broadcast:    {summary['approved_for_broadcast']}")
    print(f" Flagged for Editor Check:  {summary['flagged_for_human_override']}")
    print(f" QA Pass Rate:              {summary['pass_rate_percentage']}%")
    print(f" Total Runtime:             {summary['pipeline_execution_time_seconds']} seconds")
    print("=" * 70)

    print("\nTop 5 Ranked Promos for Immediate Posting:")
    for p in promos[:5]:
        print(f"\n[RANK #{p['rank']}] Score: {p['composite_score']} | {p['tier']}")
        print(f"  Episode: {p['episode']} | Time: {p['start_time']} -> {p['end_time']} ({p['total_duration']}s)")
        print(f"  Hook ({p['hook']['type']}): {p['hook']['description']}")
        print(f"  Cliffhanger: {p['cliffhanger']['description']}")
        print(f"  Phase: {p['posting_phase']}")
        print(f"  Pitch: {p['why_it_works']}")
        print(f"  Viral Caption: \"{p['viral_hook_caption']}\"")

    print("\n[+] Full raw deliverables successfully generated in 'raw_outputs/'.")


if __name__ == "__main__":
    main()

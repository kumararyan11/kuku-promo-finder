"""Test parser across all 50 episodes."""
import glob
import os
import sys

BASE_DIR = r"C:\Users\Sudhir Kumar\.gemini\antigravity\scratch\kuku-promo-finder"
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from screenplay_parser import parse_screenplay

folder = os.path.join(BASE_DIR, "input_pack", "I Married a Broken Soldier. He was a Duke")
files = sorted(glob.glob(os.path.join(folder, "*.txt")))
print(f"Testing parser on {len(files)} files...")

total_scenes = 0
total_blocks = 0
total_dialogues = 0
total_actions = 0
errors = 0

for fpath in files:
    try:
        ep = parse_screenplay(fpath)
        total_scenes += len(ep.scenes)
        b_count = len(ep.all_blocks)
        total_blocks += b_count
        d_count = sum(1 for b in ep.all_blocks if b.block_type == "DIALOGUE")
        a_count = sum(1 for b in ep.all_blocks if b.block_type == "ACTION")
        total_dialogues += d_count
        total_actions += a_count
        if len(ep.scenes) == 0 or b_count == 0:
            print(f"Warning: {ep.raw_filename} has {len(ep.scenes)} scenes, {b_count} blocks")
    except Exception as e:
        print(f"Error on {fpath}: {e}")
        errors += 1

print("\n--- Parsing Summary ---")
print(f"Files processed: {len(files)}")
print(f"Total scenes: {total_scenes}")
print(f"Total script blocks: {total_blocks}")
print(f"Total dialogues: {total_dialogues}")
print(f"Total actions: {total_actions}")
print(f"Errors encountered: {errors}")

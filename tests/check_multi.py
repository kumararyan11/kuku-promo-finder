import json

with open(r"C:\Users\Sudhir Kumar\.gemini\antigravity\scratch\kuku-promo-finder\raw_outputs\all_promos.json", "r", encoding="utf-8") as f:
    promos = json.load(f)

multis = [p for p in promos if p["promo_type"] == "multi_segment"]
print(f"Found {len(multis)} multi-segment promos:")
for m in multis:
    print(f"Rank: #{m['rank']} | Score: {m['composite_score']} | Ep: {m['episode']} | Segments: {len(m['segments'])}")
    for s_idx, s in enumerate(m["segments"], 1):
        print(f"  Segment {s_idx}: Ep {s['episode']} [{s['start_time']} -> {s['end_time']}] ({s['duration']}s)")
    print(f"  Hook: {m['hook']['description']}")
    print(f"  Cliffhanger: {m['cliffhanger']['description']}")
    print(f"  Why it works: {m['why_it_works']}")
    print()

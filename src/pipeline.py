"""End-to-end promo discovery and evaluation pipeline.
Processes full 50-episode microdrama input pack, runs feature extraction, model scoring,
ranking, quality auditing, and exports complete unedited raw outputs.
"""

import os
import glob
import json
import csv
import time
from typing import List, Dict, Any, Optional
from screenplay_parser import parse_screenplay, Episode
from candidate_generator import generate_episode_candidates, PromoCandidate
from multi_segment_builder import build_curated_multi_segment_promos
from llm_evaluator import LLMEvaluator, HeuristicExpertBackend, GeminiBackend
from ranker import rank_and_schedule_promos
from quality_auditor import audit_all_promos


class PromoFinderPipeline:
    def __init__(self, input_dir: str, output_dir: str, backend_type: str = "expert", api_key: Optional[str] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.episodes: Dict[int, Episode] = {}
        self.all_candidates: Dict[int, List[PromoCandidate]] = {}
        
        # Select backend
        if backend_type == "gemini":
            backend = GeminiBackend(api_key=api_key)
        else:
            backend = HeuristicExpertBackend()
        self.evaluator = LLMEvaluator(backend=backend)

    def load_episodes(self) -> int:
        """Parses all screenplays from input directory."""
        files = sorted(glob.glob(os.path.join(self.input_dir, "*.txt")))
        print(f"[*] Found {len(files)} screenplay files in {self.input_dir}")
        for fpath in files:
            try:
                ep = parse_screenplay(fpath)
                self.episodes[ep.episode_number] = ep
            except Exception as e:
                print(f"[!] Error parsing {fpath}: {e}")
        print(f"[+] Successfully parsed {len(self.episodes)} episodes.")
        return len(self.episodes)

    def run(self, max_promos_per_episode: int = 2) -> Dict[str, Any]:
        """Runs candidate generation, scoring, multi-segment curation, ranking, and auditing."""
        start_time = time.time()
        if not self.episodes:
            self.load_episodes()

        raw_evaluated = []

        # 1. Generate and evaluate single continuous candidates per episode
        for ep_num, ep in self.episodes.items():
            cands = generate_episode_candidates(ep, min_duration=20.0, max_duration=60.0)
            self.all_candidates[ep_num] = cands

            # Evaluate each candidate and pick top N per episode
            ep_evals = []
            for c in cands:
                res = self.evaluator.evaluate_promo(c)
                ep_evals.append((res, c))

            # Sort ep_evals descending by score
            ep_evals.sort(key=lambda x: x[0]["composite_score"], reverse=True)
            
            # Apply Non-Maximum Suppression (IoU deduplication) so candidates are distinct moments
            selected_for_ep = []
            for res, c in ep_evals:
                c_start = c.segments[0]["start_sec"]
                c_end = c.segments[-1]["end_sec"]
                
                is_overlap = False
                for s_res, s_c in selected_for_ep:
                    s_start = s_c.segments[0]["start_sec"]
                    s_end = s_c.segments[-1]["end_sec"]
                    
                    # Compute Intersection over Union (IoU)
                    inter = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                    union = max(c_end, s_end) - min(c_start, s_start)
                    iou = inter / union if union > 0 else 0.0
                    
                    if iou > 0.35:
                        is_overlap = True
                        break
                        
                if not is_overlap:
                    selected_for_ep.append((res, c))
                    if len(selected_for_ep) >= max_promos_per_episode:
                        break

            for res, c in selected_for_ep:
                raw_evaluated.append(res)

        # 2. Add signature Multi-Segment Cross-Episode Promos
        multi_cands = build_curated_multi_segment_promos(self.episodes)
        self.all_candidates[999] = multi_cands
        for mc in multi_cands:
            res = self.evaluator.evaluate_promo(mc)
            raw_evaluated.append(res)

        # 3. Rank and assign growth distribution phases
        ranked_promos = rank_and_schedule_promos(raw_evaluated)

        # 4. Rigorous Quality Audit
        audit_res = audit_all_promos(ranked_promos, self.all_candidates)
        final_promos = audit_res["audited_promos"]
        summary = audit_res["summary"]

        duration_sec = round(time.time() - start_time, 2)
        summary["pipeline_execution_time_seconds"] = duration_sec
        summary["episodes_processed"] = len(self.episodes)
        summary["total_promos_generated"] = len(final_promos)

        # 5. Export outputs
        self.export_results(final_promos, summary)

        print(f"[+] Pipeline completed in {duration_sec}s! Generated {len(final_promos)} ranked promos.")
        return {
            "summary": summary,
            "promos": final_promos,
        }

    def export_results(self, promos: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Saves all deliverables in unedited format to raw_outputs directory."""
        os.makedirs(self.output_dir, exist_ok=True)
        episodes_dir = os.path.join(self.output_dir, "episodes")
        os.makedirs(episodes_dir, exist_ok=True)

        # 1. Full JSON catalog
        all_json_path = os.path.join(self.output_dir, "all_promos.json")
        with open(all_json_path, "w", encoding="utf-8") as f:
            json.dump(promos, f, indent=2)

        # 2. Full CSV catalog
        all_csv_path = os.path.join(self.output_dir, "all_promos.csv")
        with open(all_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Rank", "Episode", "Promo_Type", "Start_Time", "End_Time", "Duration_Sec",
                "Composite_Score", "Tier", "Posting_Phase", "Platform",
                "Hook_Type", "Hook_Description", "Cliffhanger_Description",
                "Why_It_Works", "Viral_Hook_Caption", "QA_Verdict"
            ])
            for p in promos:
                writer.writerow([
                    p["rank"],
                    p["episode"],
                    p["promo_type"],
                    p["start_time"],
                    p["end_time"],
                    p["total_duration"],
                    p["composite_score"],
                    p["tier"],
                    p["posting_phase"],
                    p["recommended_platform"],
                    p["hook"]["type"],
                    p["hook"]["description"],
                    p["cliffhanger"]["description"],
                    p["why_it_works"],
                    p["viral_hook_caption"],
                    p.get("qa_audit", {}).get("qa_verdict", "N/A"),
                ])

        # 3. Top 10 Ranked Promos (Hero Promos)
        top_10 = promos[:10]
        top_json_path = os.path.join(self.output_dir, "top_ranked_promos.json")
        with open(top_json_path, "w", encoding="utf-8") as f:
            json.dump(top_10, f, indent=2)

        # 4. Quality Audit & Failure Summary
        qa_path = os.path.join(self.output_dir, "quality_audit_and_failures.json")
        with open(qa_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # 5. Per-episode individual JSON outputs
        by_ep: Dict[int, List[Dict[str, Any]]] = {}
        for p in promos:
            ep = p["episode"]
            by_ep.setdefault(ep, []).append(p)

        for ep_num, ep_promos in by_ep.items():
            ep_file = os.path.join(episodes_dir, f"episode_{ep_num:03d}.json")
            with open(ep_file, "w", encoding="utf-8") as f:
                json.dump(ep_promos, f, indent=2)

        print(f"[+] Successfully exported all files to {self.output_dir}")

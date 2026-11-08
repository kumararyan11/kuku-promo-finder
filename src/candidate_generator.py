"""Candidate promo generator.
Identifies potential promo windows (20s to 60s) from screenplays.
Snaps boundaries to natural camera shots or dialogue ends to ensure clean cuts.
"""

from typing import List, Dict, Any, Tuple
from screenplay_parser import Episode, Scene, ScriptBlock, format_timestamp


class PromoCandidate:
    def __init__(
        self,
        episode_number: int,
        segments: List[Dict[str, Any]],  # list of {'start_sec': float, 'end_sec': float, 'start_str': str, 'end_str': str, 'blocks': list}
        promo_type: str = "single_continuous",  # 'single_continuous' or 'multi_segment'
    ):
        self.episode_number = episode_number
        self.segments = segments
        self.promo_type = promo_type

    @property
    def total_duration(self) -> float:
        return sum(s["end_sec"] - s["start_sec"] for s in self.segments)

    @property
    def start_str(self) -> str:
        return self.segments[0]["start_str"]

    @property
    def end_str(self) -> str:
        return self.segments[-1]["end_str"]

    @property
    def all_blocks(self) -> List[ScriptBlock]:
        result = []
        for s in self.segments:
            result.extend(s.get("blocks", []))
        return result

    def get_summary_text(self) -> str:
        """Condensed readable transcript of the candidate promo."""
        lines = []
        for s_idx, seg in enumerate(self.segments):
            if len(self.segments) > 1:
                lines.append(f"--- Segment {s_idx + 1} (Ep {seg.get('episode', self.episode_number)}: {seg['start_str']} - {seg['end_str']}) ---")
            for b in seg.get("blocks", []):
                if b.block_type == "DIALOGUE":
                    speaker = b.speaker or "CHARACTER"
                    tone_str = f" ({b.tone})" if b.tone else ""
                    lines.append(f"[{b.start_str}] {speaker}{tone_str}: \"{b.content}\"")
                elif b.block_type == "ACTION":
                    lines.append(f"[{b.start_str}] ACTION: {b.content}")
                elif b.block_type == "CAMERA":
                    lines.append(f"[{b.start_str}] CAMERA: {b.content}")
                elif b.block_type == "SOUND_FX":
                    lines.append(f"[{b.start_str}] SOUND FX: {b.content}")
        return "\n".join(lines)


def generate_single_scene_candidates(
    scene: Scene,
    episode_number: int,
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    step_blocks: int = 1,
) -> List[PromoCandidate]:
    """Generate sliding window candidates within a single scene, snapping to block boundaries."""
    candidates = []
    blocks = scene.blocks
    if not blocks:
        return candidates

    n = len(blocks)
    for i in range(0, n, step_blocks):
        start_block = blocks[i]
        start_time = start_block.start_time

        # Seek an end block that falls within [min_duration, max_duration]
        for j in range(i, n):
            end_block = blocks[j]
            duration = end_block.end_time - start_time

            if duration < min_duration:
                continue
            if duration > max_duration:
                break  # Further blocks will only exceed max_duration

            # Valid window found
            seg_blocks = blocks[i : j + 1]
            seg = {
                "episode": episode_number,
                "start_sec": start_time,
                "end_sec": end_block.end_time,
                "start_str": format_timestamp(start_time),
                "end_str": format_timestamp(end_block.end_time),
                "duration": duration,
                "blocks": seg_blocks,
            }

            candidate = PromoCandidate(
                episode_number=episode_number,
                segments=[seg],
                promo_type="single_continuous",
            )
            candidates.append(candidate)

    return candidates


def generate_episode_candidates(
    episode: Episode,
    min_duration: float = 20.0,
    max_duration: float = 60.0,
) -> List[PromoCandidate]:
    """Generate candidates across all scenes in an episode."""
    all_candidates = []
    for scene in episode.scenes:
        scene_cands = generate_single_scene_candidates(
            scene=scene,
            episode_number=episode.episode_number,
            min_duration=min_duration,
            max_duration=max_duration,
        )
        all_candidates.extend(scene_cands)
    return all_candidates

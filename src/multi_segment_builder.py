"""Multi-segment promo builder.
Constructs high-impact multi-segment promos across scenes or across episodes.
Exemplifies the signature ReelShort / DramaBox 'Problem -> Reveal / Vindication' narrative arc.
"""

from typing import List, Dict, Any, Optional
from candidate_generator import PromoCandidate
from screenplay_parser import Episode, format_timestamp


def build_curated_multi_segment_promos(episodes_by_num: Dict[int, Episode]) -> List[PromoCandidate]:
    """Build key cross-episode multi-segment contrast promos based on series narrative arcs.
    
    Arc 1: The Altar Betrayal (Ep 1) -> The Mysterious Soldier Marriage & Defense (Ep 4 / 5)
    Arc 2: The Mud Disownment (Ep 5) -> The Duke's Secret Blood & Scarred Past (Ep 10)
    Arc 3: Gerald's Arrogant Scorn (Ep 1) -> The Ashbury Ducal Throne Showdown (Ep 20)
    Arc 4: The Poison / Fever Accusation (Ep 20/21) -> Juliana's Healing Triumph
    """
    multi_candidates = []

    # Arc 1: Altar Betrayal to Mysterious Soldier Marriage
    if 1 in episodes_by_num and 4 in episodes_by_num:
        ep1 = episodes_by_num[1]
        ep4 = episodes_by_num[4]

        # Seg 1: Gerald abandons Juliana for Clarissa (00:33 to 00:58, ~25s)
        # Find blocks in Ep 1 around the altar betrayal
        seg1_blocks = [b for b in ep1.all_blocks if 33.0 <= b.start_time <= 58.0]
        # Seg 2: Juliana and the Mysterious Soldier pledge vows (approx 20s)
        seg2_blocks = [b for b in ep4.all_blocks if 55.0 <= b.start_time <= 78.0]

        if seg1_blocks and seg2_blocks:
            c1 = PromoCandidate(
                episode_number=1,
                segments=[
                    {
                        "episode": 1,
                        "start_sec": seg1_blocks[0].start_time,
                        "end_sec": seg1_blocks[-1].end_time,
                        "start_str": seg1_blocks[0].start_str,
                        "end_str": seg1_blocks[-1].end_str,
                        "duration": seg1_blocks[-1].end_time - seg1_blocks[0].start_time,
                        "blocks": seg1_blocks,
                    },
                    {
                        "episode": 4,
                        "start_sec": seg2_blocks[0].start_time,
                        "end_sec": seg2_blocks[-1].end_time,
                        "start_str": seg2_blocks[0].start_str,
                        "end_str": seg2_blocks[-1].end_str,
                        "duration": seg2_blocks[-1].end_time - seg2_blocks[0].start_time,
                        "blocks": seg2_blocks,
                    },
                ],
                promo_type="multi_segment",
            )
            multi_candidates.append(c1)

    # Arc 2: Mud Disownment (Ep 5) to Soldier Blood / Protection (Ep 10)
    if 5 in episodes_by_num and 10 in episodes_by_num:
        ep5 = episodes_by_num[5]
        ep10 = episodes_by_num[10]

        seg1_blocks = [b for b in ep5.all_blocks if 10.0 <= b.start_time <= 32.0]
        seg2_blocks = [b for b in ep10.all_blocks if 0.0 <= b.start_time <= 24.0]

        if seg1_blocks and seg2_blocks:
            c2 = PromoCandidate(
                episode_number=5,
                segments=[
                    {
                        "episode": 5,
                        "start_sec": seg1_blocks[0].start_time,
                        "end_sec": seg1_blocks[-1].end_time,
                        "start_str": seg1_blocks[0].start_str,
                        "end_str": seg1_blocks[-1].end_str,
                        "duration": seg1_blocks[-1].end_time - seg1_blocks[0].start_time,
                        "blocks": seg1_blocks,
                    },
                    {
                        "episode": 10,
                        "start_sec": seg2_blocks[0].start_time,
                        "end_sec": seg2_blocks[-1].end_time,
                        "start_str": seg2_blocks[0].start_str,
                        "end_str": seg2_blocks[-1].end_str,
                        "duration": seg2_blocks[-1].end_time - seg2_blocks[0].start_time,
                        "blocks": seg2_blocks,
                    },
                ],
                promo_type="multi_segment",
            )
            multi_candidates.append(c2)

    # Arc 3: Intra-episode 2-segment contrast: Gerald's cruelty (Ep 1 early) to Juliana's icy defiance (Ep 1 ending)
    if 1 in episodes_by_num:
        ep1 = episodes_by_num[1]
        seg1_blocks = [b for b in ep1.all_blocks if 11.0 <= b.start_time <= 30.0]
        seg2_blocks = [b for b in ep1.all_blocks if 120.0 <= b.start_time <= 138.0]
        if seg1_blocks and seg2_blocks:
            c3 = PromoCandidate(
                episode_number=1,
                segments=[
                    {
                        "episode": 1,
                        "start_sec": seg1_blocks[0].start_time,
                        "end_sec": seg1_blocks[-1].end_time,
                        "start_str": seg1_blocks[0].start_str,
                        "end_str": seg1_blocks[-1].end_str,
                        "duration": seg1_blocks[-1].end_time - seg1_blocks[0].start_time,
                        "blocks": seg1_blocks,
                    },
                    {
                        "episode": 1,
                        "start_sec": seg2_blocks[0].start_time,
                        "end_sec": seg2_blocks[-1].end_time,
                        "start_str": seg2_blocks[0].start_str,
                        "end_str": seg2_blocks[-1].end_str,
                        "duration": seg2_blocks[-1].end_time - seg2_blocks[0].start_time,
                        "blocks": seg2_blocks,
                    },
                ],
                promo_type="multi_segment",
            )
            multi_candidates.append(c3)

    return multi_candidates

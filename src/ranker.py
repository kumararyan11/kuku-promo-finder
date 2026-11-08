"""Promo ranking and growth distribution strategy engine.
Ranks candidate promos, assigns publishing tiers, and formulates the multi-phase ad rollout strategy.
"""

from typing import List, Dict, Any


def rank_and_schedule_promos(evaluated_promos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sorts evaluated promos by composite score, tags them with tiers and strategic posting phases."""
    
    # Sort descending by composite score
    sorted_promos = sorted(evaluated_promos, key=lambda x: x["composite_score"], reverse=True)

    ranked_results = []
    for rank_idx, promo in enumerate(sorted_promos, 1):
        score = promo["composite_score"]
        themes = promo.get("themes", [])
        hook_type = promo["hook"]["type"]
        ep = promo["episode"]
        is_multi = promo["promo_type"] == "multi_segment"

        # Tier Assignment
        if score >= 85.0:
            tier = "Tier 1 (S-Rank - Hero Ad)"
        elif score >= 75.0:
            tier = "Tier 2 (A-Rank - Core Test Ad)"
        else:
            tier = "Tier 3 (B-Rank - Retargeting Ad)"

        # Strategic Posting Phase & Platform
        if "Betrayed Wedding" in themes or ep <= 3 or "Action Disruption" in hook_type:
            phase = "Phase 1: Top-of-Funnel Outrage & Acquisition (Post Day 1-2)"
            platform = "TikTok & Meta Reels (Broad Interest Targeting)"
            rationale = (
                "Post FIRST. The altar betrayal and public humiliation evoke universal moral outrage. "
                "Delivers the highest 3-second thumbstop rate (>45%) and lowest Cost-Per-Click (CPC) to pull fresh cold viewers."
            )
        elif is_multi or "Secret Duke" in " ".join(themes) or ep in [4, 5, 10]:
            phase = "Phase 2: High-Conversion Identity Reveal & Vindication (Post Day 3-5)"
            platform = "Instagram Reels & YouTube Shorts (Conversion-Optimized)"
            rationale = (
                "Post SECOND. Contrast between broken soldier and royal Duke triggers irresistible catharsis. "
                "Highest click-to-install and episode unlock conversion rate among viewers intrigued by Phase 1 ads."
            )
        else:
            phase = "Phase 3: Deep Mid-Series Escalation & Paywall Retargeting (Post Day 6+)"
            platform = "Meta Ads & TikTok Retargeting"
            rationale = (
                "Post THIRD. High-stakes conspiracy, poisonings, and estate battles re-engage warm users and "
                "push viewers past the free episode paywall."
            )

        promo_copy = dict(promo)
        promo_copy["rank"] = rank_idx
        promo_copy["tier"] = tier
        promo_copy["posting_phase"] = phase
        promo_copy["recommended_platform"] = platform
        promo_copy["posting_rationale"] = rationale
        ranked_results.append(promo_copy)

    return ranked_results

"""Feature extraction and scoring engine for microdrama promo candidates.
Calculates Hook Intensity (0-10), Cliffhanger Tension (0-10), Standalone Comprehensibility (0-10),
Pacing & Duration Score (0-10), and Composite Score.
"""

import re
from typing import Dict, Any, List
from candidate_generator import PromoCandidate
from screenplay_parser import ScriptBlock

# High-arousal action keywords indicative of visual disruptions
ACTION_HOOK_KEYWORDS = {
    "slap": 4.0, "strike": 3.5, "hit": 3.5, "shove": 3.0, "push": 3.0,
    "mud": 3.5, "blood": 4.0, "bloody": 3.5, "wound": 3.0, "dagger": 3.5,
    "sword": 3.5, "blade": 3.0, "tear": 3.0, "rip": 3.5, "clench": 2.5,
    "shatter": 3.5, "collapse": 3.0, "gasp": 2.5, "scream": 3.0,
    "kneel": 3.0, "grab": 3.0, "seize": 3.0, "weep": 2.5, "tremble": 2.5,
    "shiver": 2.0, "stumble": 2.5, "strangle": 4.0, "poison": 4.0,
}

# High-arousal dialogue shock words
DIALOGUE_HOOK_KEYWORDS = {
    "marrying": 3.5, "betrayal": 4.0, "disowned": 4.0, "liar": 3.5,
    "cheat": 3.5, "bastard": 3.5, "scandal": 3.5, "worthless": 3.5,
    "low value": 4.0, "plainness": 3.0, "beggar": 3.0, "broken": 3.0,
    "duke": 3.5, "kill": 4.0, "die": 3.5, "arrest": 3.5, "ruined": 3.5,
    "abandon": 3.5, "shame": 3.0, "refuse": 2.5, "forbidden": 3.0,
    "divorce": 4.0, "pregnant": 4.0, "mistress": 4.0, "traitor": 4.0,
    "execute": 4.0, "impostor": 4.0, "murderer": 4.0, "soldier": 2.5,
    "honor": 2.5, "dare": 2.5, "fool": 2.5, "whore": 4.0, "unworthy": 3.0,
}

# Emotional tone tags indicating intense confrontation
INTENSE_TONES = {
    "cold": 2.0, "furious": 2.5, "cruel": 2.5, "smug": 2.5, "gloating": 2.5,
    "arrogant": 2.5, "mocking": 2.5, "screaming": 3.0, "scornful": 2.5,
    "spiteful": 2.5, "haughty": 2.0, "commanding": 2.0, "threatening": 3.0,
    "heartbroken": 2.5, "desperate": 2.5, "whispering": 2.0, "venomous": 3.0,
    "malicious": 3.0, "seething": 3.0, "shocked": 2.5, "defiant": 2.5,
}

# Key character names in the microdrama
KEY_CHARACTERS = {"juliana", "gerald", "clarissa", "alexander", "duke", "matriarch", "duchess", "rupert", "catherine", "edward"}

# Ambiguous opening pronouns that confuse cold viewers
AMBIGUOUS_OPENERS = {"he", "she", "they", "it", "him", "her", "them", "his", "their"}


def evaluate_hook(candidate: PromoCandidate) -> Dict[str, Any]:
    """Score the first 3.5 seconds of the promo for stop-rate potential."""
    if not candidate.segments:
        return {"score": 0.0, "hook_type": "none", "description": "No segments"}

    first_seg = candidate.segments[0]
    seg_start = first_seg["start_sec"]
    hook_window = seg_start + 3.5

    hook_blocks = [b for b in first_seg["blocks"] if b.start_time <= hook_window]
    if not hook_blocks and first_seg["blocks"]:
        hook_blocks = [first_seg["blocks"][0]]

    score = 2.0  # baseline
    detected_elements = []
    primary_hook_text = ""

    for b in hook_blocks:
        content_lower = b.content.lower()
        
        # Action cues
        if b.block_type == "ACTION":
            for kw, weight in ACTION_HOOK_KEYWORDS.items():
                if kw in content_lower:
                    score += weight
                    detected_elements.append(f"Action: {kw}")
            if not primary_hook_text:
                primary_hook_text = b.content[:90]

        # Dialogue cues
        elif b.block_type == "DIALOGUE":
            for kw, weight in DIALOGUE_HOOK_KEYWORDS.items():
                if kw in content_lower:
                    score += weight
                    detected_elements.append(f"Shock line: '{kw}'")
            # Exclamation marks / question marks
            if "!" in b.content:
                score += 1.5
            if "?" in b.content:
                score += 1.0

            # Tone intensity
            if b.tone:
                tone_lower = b.tone.lower()
                for t, w in INTENSE_TONES.items():
                    if t in tone_lower:
                        score += w
                        detected_elements.append(f"Vocal tone: {t}")

            if not primary_hook_text:
                speaker = b.speaker or "CHARACTER"
                primary_hook_text = f'{speaker}: "{b.content[:70]}"'

        # Camera cues (close up, push in, sudden reveal)
        elif b.block_type == "CAMERA":
            if any(k in content_lower for k in ["close-up", "extreme close-up", "tight", "push-in", "shock", "tears"]):
                score += 1.5
                detected_elements.append("Intense camera framing")

    # Penalize ambiguous starts
    if hook_blocks and hook_blocks[0].block_type == "DIALOGUE":
        first_word = hook_blocks[0].content.strip().split(" ")[0].lower().strip("\"'.,;:")
        if first_word in AMBIGUOUS_OPENERS:
            score -= 1.5

    clamped_score = min(10.0, max(1.0, score))
    
    # Classify hook type
    hook_type = "Shock Dialogue"
    if any("Action" in e for e in detected_elements):
        hook_type = "Physical/Action Disruption"
    elif any("Vocal" in e for e in detected_elements):
        hook_type = "High-Conflict Confrontation"
    elif "duke" in primary_hook_text.lower() or "marrying" in primary_hook_text.lower():
        hook_type = "Betrayal / Identity Reveal"

    return {
        "score": round(clamped_score, 2),
        "hook_type": hook_type,
        "description": primary_hook_text or "Opening scene hook",
        "elements": detected_elements[:4],
    }


def evaluate_cliffhanger(candidate: PromoCandidate) -> Dict[str, Any]:
    """Score the final 3-4 seconds of the promo for unresolved curiosity & tension."""
    if not candidate.segments:
        return {"score": 0.0, "description": "No segments"}

    last_seg = candidate.segments[-1]
    seg_end = last_seg["end_sec"]
    tail_window = max(last_seg["start_sec"], seg_end - 4.0)

    tail_blocks = [b for b in last_seg["blocks"] if b.end_time >= tail_window]
    if not tail_blocks and last_seg["blocks"]:
        tail_blocks = [last_seg["blocks"][-1]]

    score = 2.5  # baseline
    detected_elements = []
    cliffhanger_text = ""

    last_block = tail_blocks[-1] if tail_blocks else None

    # Check for cliffhanger sound FX / cut to black
    for b in tail_blocks:
        content_lower = b.content.lower()
        if b.block_type == "SOUND_FX":
            if any(k in content_lower for k in ["cliffhanger", "drone", "swell", "ominous", "sting", "crescendo", "peak"]):
                score += 3.5
                detected_elements.append("Cliffhanger audio swell")
                cliffhanger_text = b.content[:80]
        elif b.block_type == "CAMERA":
            if any(k in content_lower for k in ["cut to black", "hard cut", "defiance", "hardening", "shock", "freeze"]):
                score += 2.5
                detected_elements.append("Cut to black / dramatic reaction")
                if not cliffhanger_text:
                    cliffhanger_text = b.content[:80]
        elif b.block_type == "ACTION":
            if any(k in content_lower for k in ["clenches", "defiance", "refusing", "stares", "steps forward", "draws", "collapses"]):
                score += 2.0
                detected_elements.append("Unresolved physical reaction")
                if not cliffhanger_text:
                    cliffhanger_text = b.content[:80]
        elif b.block_type == "DIALOGUE":
            # Questions at the cut leave strong curiosity gaps
            if "?" in b.content:
                score += 3.0
                detected_elements.append("Unanswered question")
                cliffhanger_text = f'{b.speaker or "CHARACTER"}: "{b.content[:70]}"'
            elif any(k in content_lower for k in ["never", "will pay", "or else", "wait", "no", "who", "die", "duke"]):
                score += 2.0
                detected_elements.append("Defiant parting line")
                if not cliffhanger_text:
                    cliffhanger_text = f'{b.speaker or "CHARACTER"}: "{b.content[:70]}"'

    # Check resolution penalty (calm parting words)
    if last_block and last_block.block_type == "DIALOGUE":
        last_line_lower = last_block.content.lower()
        if any(k in last_line_lower for k in ["thank you", "goodbye", "good night", "as you wish", "all right"]):
            score -= 2.5

    clamped_score = min(10.0, max(1.0, score))
    return {
        "score": round(clamped_score, 2),
        "description": cliffhanger_text or "Dramatic cut at unresolved tension",
        "elements": detected_elements[:4],
    }


def evaluate_standalone(candidate: PromoCandidate) -> Dict[str, Any]:
    """Score how comprehensible the promo is to a complete stranger scrolling on TikTok."""
    all_blocks = candidate.all_blocks
    total_text = " ".join([b.content for b in all_blocks]).lower()
    
    score = 4.0  # baseline
    named_chars = [c for c in KEY_CHARACTERS if c in total_text]

    # Award points for presence of clear key protagonists/antagonists
    if "juliana" in named_chars:
        score += 2.0
    if "gerald" in named_chars or "clarissa" in named_chars:
        score += 1.5
    if "duke" in named_chars or "alexander" in named_chars:
        score += 2.0

    # Conflict clarity: archetypal microdrama themes
    themes = []
    if any(k in total_text for k in ["altar", "marry", "wedding", "groom", "bride", "gown"]):
        score += 1.5
        themes.append("Betrayed Wedding")
    if any(k in total_text for k in ["disown", "inheritance", "family", "sister", "mother"]):
        score += 1.0
        themes.append("Cruel Family / Disownment")
    if any(k in total_text for k in ["soldier", "war", "duke", "title", "estate"]):
        score += 1.5
        themes.append("Secret Duke / Hidden Power")
    if any(k in total_text for k in ["blood", "wound", "fever", "save", "cure"]):
        score += 1.0
        themes.append("Life or Death / Rescue")

    # Penalize if promo is too short (<22s) to establish context
    dur = candidate.total_duration
    if dur < 22.0:
        score -= 1.5

    clamped_score = min(10.0, max(1.0, score))
    return {
        "score": round(clamped_score, 2),
        "themes": themes,
        "named_characters": named_chars,
    }


def evaluate_pacing_and_duration(candidate: PromoCandidate) -> Dict[str, Any]:
    """Evaluate pacing, cuts, and vertical video duration fit (20s to 60s)."""
    dur = candidate.total_duration
    all_blocks = candidate.all_blocks
    
    # Duration sweet spot for TikTok/Reels ads is 25s - 45s
    if 25.0 <= dur <= 45.0:
        dur_score = 10.0
    elif 20.0 <= dur < 25.0:
        dur_score = 8.5
    elif 45.0 < dur <= 55.0:
        dur_score = 8.5
    elif 55.0 < dur <= 60.0:
        dur_score = 7.0
    else:
        dur_score = 4.0

    # Cut density: number of camera/dialogue blocks per 10 seconds
    block_density = len(all_blocks) / (dur / 10.0) if dur > 0 else 0
    # Good vertical microdrama rhythm has a shot or dialogue beat every 2-4 seconds (density 2.5 - 5.0)
    if 2.0 <= block_density <= 5.5:
        pacing_score = 9.5
    elif block_density > 5.5:
        pacing_score = 8.0  # slightly hectic
    else:
        pacing_score = 6.5  # slightly slow/static

    composite_pacing = round((dur_score * 0.6) + (pacing_score * 0.4), 2)
    return {
        "score": composite_pacing,
        "duration_sec": round(dur, 2),
        "block_count": len(all_blocks),
        "block_density": round(block_density, 2),
    }


def score_candidate(candidate: PromoCandidate) -> Dict[str, Any]:
    """Calculate the overall candidate promo score and all sub-dimensions."""
    hook = evaluate_hook(candidate)
    cliffhanger = evaluate_cliffhanger(candidate)
    standalone = evaluate_standalone(candidate)
    pacing = evaluate_pacing_and_duration(candidate)

    # Weights reflect microdrama ad performance:
    # Hook is king (35%), Cliffhanger drives tap-through (30%), Standalone drives conversion (20%), Pacing (15%)
    composite_100 = (
        (hook["score"] * 3.5) +
        (cliffhanger["score"] * 3.0) +
        (standalone["score"] * 2.0) +
        (pacing["score"] * 1.5)
    )

    # Bonus for multi-segment contrast promos (Problem -> Reveal structure)
    if candidate.promo_type == "multi_segment":
        composite_100 = min(100.0, composite_100 + 4.0)

    # One line on why it works (synthesized explanation)
    why_it_works = synthesize_why_it_works(hook, cliffhanger, standalone, candidate)

    return {
        "composite_score": round(composite_100, 2),
        "hook": hook,
        "cliffhanger": cliffhanger,
        "standalone": standalone,
        "pacing": pacing,
        "why_it_works": why_it_works,
    }


def synthesize_why_it_works(hook: Dict, cliffhanger: Dict, standalone: Dict, cand: PromoCandidate) -> str:
    """Generate a sharp, insightful one-line pitch on why this specific promo converts."""
    themes_str = ", ".join(standalone["themes"]) if standalone["themes"] else "dramatic tension"
    h_type = hook["hook_type"]
    return (
        f"Instantly stops scrolling with {h_type.lower()} ('{hook['description']}'), "
        f"clearly establishes the {themes_str} conflict for cold viewers, "
        f"and cuts at maximum tension on {cliffhanger['description']} to drive app downloads."
    )

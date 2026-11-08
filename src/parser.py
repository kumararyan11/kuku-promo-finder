"""Screenplay parser for microdrama scripts.
Extracts metadata, scenes, camera movements, actions, dialogues, and sound cues with timestamps.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


def parse_timestamp(ts_str: str) -> float:
    """Convert MM:SS.ms or SS.ms to total seconds."""
    ts_str = ts_str.strip().strip("()")
    parts = ts_str.split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60.0 + float(parts[1])
    elif len(parts) == 1:
        return float(parts[0])
    raise ValueError(f"Invalid timestamp format: {ts_str}")


def format_timestamp(seconds: float) -> str:
    """Convert total seconds to MM:SS.ms format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


class ScriptBlock(BaseModel):
    block_type: str  # 'CAMERA', 'ACTION', 'DIALOGUE', 'SOUND_FX', 'OTHER'
    speaker: Optional[str] = None
    tone: Optional[str] = None
    start_time: float
    end_time: float
    start_str: str
    end_str: str
    content: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class Scene(BaseModel):
    scene_number: int
    heading: str
    start_time: float
    end_time: float
    start_str: str
    end_str: str
    blocks: List[ScriptBlock] = Field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class Episode(BaseModel):
    episode_number: int
    episode_title: str
    logline: str
    continuity_notes: str
    scenes: List[Scene] = Field(default_factory=list)
    raw_filename: str

    @property
    def total_duration(self) -> float:
        if not self.scenes:
            return 0.0
        return max(s.end_time for s in self.scenes)

    @property
    def all_blocks(self) -> List[ScriptBlock]:
        result = []
        for s in self.scenes:
            result.extend(s.blocks)
        return result


def parse_screenplay(file_path: str) -> Episode:
    """Parse an episode text file into an Episode object."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # Extract Episode Number
    ep_num = 0
    ep_num_match = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
    if ep_num_match:
        ep_num = int(ep_num_match.group(1))

    # Extract Logline
    logline = ""
    logline_match = re.search(r"EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s]+:|\n---)", text, re.DOTALL)
    if logline_match:
        logline = logline_match.group(1).strip()

    # Extract Continuity
    continuity = ""
    continuity_match = re.search(r"CONTINUITY NOTES:\s*(.*?)(?=\n--- SCRIPT START ---|\nSCENE)", text, re.DOTALL)
    if continuity_match:
        continuity = continuity_match.group(1).strip()

    # Split into scenes
    # Pattern looks for "SCENE XX"
    scene_splits = list(re.finditer(r"SCENE\s+(\d+)\s*\nScene heading:\s*(.*?)\nScene start:\s*([0-9:.]+)\s*\nScene end:\s*([0-9:.]+)", text))
    
    scenes: List[Scene] = []
    
    for i, match in enumerate(scene_splits):
        s_num = int(match.group(1))
        heading = match.group(2).strip()
        s_start_str = match.group(3).strip()
        s_end_str = match.group(4).strip()
        s_start = parse_timestamp(s_start_str)
        s_end = parse_timestamp(s_end_str)

        # Body of this scene is between end of this match and start of next match (or SCRIPT END)
        body_start = match.end()
        if i + 1 < len(scene_splits):
            body_end = scene_splits[i + 1].start()
        else:
            end_match = re.search(r"--- SCRIPT END ---", text[body_start:])
            body_end = body_start + end_match.start() if end_match else len(text)
        
        scene_body = text[body_start:body_end]
        
        # Parse blocks in scene body
        # Blocks start with **HEADER:**
        block_pattern = re.compile(
            r"\*\*([^*]+)\*\*:\s*\nStart:\s*\(([0-9:.]+)\)\s*\|\s*End:\s*\(([0-9:.]+)\)\s*\n(.*?)(?=(?:\n\*\*[^*]+\*\*:|\Z))",
            re.DOTALL
        )
        
        blocks: List[ScriptBlock] = []
        for b_match in block_pattern.finditer(scene_body):
            raw_tag = b_match.group(1).strip()
            b_start_str = b_match.group(2).strip()
            b_end_str = b_match.group(3).strip()
            raw_content = b_match.group(4).strip()
            
            b_start = parse_timestamp(b_start_str)
            b_end = parse_timestamp(b_end_str)
            
            # Determine block type and details
            tag_upper = raw_tag.upper()
            if tag_upper == "CAMERA":
                b_type = "CAMERA"
                speaker = None
                tone = None
                content = raw_content
            elif tag_upper in ("ACTION", "ACTIONS"):
                b_type = "ACTION"
                speaker = None
                tone = None
                content = raw_content
            elif "SOUND" in tag_upper or "SFX" in tag_upper or "MUSIC" in tag_upper:
                b_type = "SOUND_FX"
                speaker = None
                tone = None
                content = raw_content
            else:
                # Likely dialogue: e.g. "LADY JULIANA (Confused, Breathless)" or "GERALD"
                b_type = "DIALOGUE"
                # Check for emotion / tone in parentheses
                speaker_match = re.match(r"^([^(]+)(?:\((.*)\))?$", raw_tag)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    tone = speaker_match.group(2).strip() if speaker_match.group(2) else None
                else:
                    speaker = raw_tag
                    tone = None
                # Clean content quotes if any
                clean_content = raw_content.strip()
                if clean_content.startswith('"') and clean_content.endswith('"') and len(clean_content) > 1:
                    clean_content = clean_content[1:-1].strip()
                content = clean_content

            blocks.append(ScriptBlock(
                block_type=b_type,
                speaker=speaker,
                tone=tone,
                start_time=b_start,
                end_time=b_end,
                start_str=format_timestamp(b_start),
                end_str=format_timestamp(b_end),
                content=content
            ))

        scenes.append(Scene(
            scene_number=s_num,
            heading=heading,
            start_time=s_start,
            end_time=s_end,
            start_str=format_timestamp(s_start),
            end_str=format_timestamp(s_end),
            blocks=blocks
        ))

    import os
    return Episode(
        episode_number=ep_num,
        episode_title=f"Episode {ep_num}",
        logline=logline,
        continuity_notes=continuity,
        scenes=scenes,
        raw_filename=os.path.basename(file_path)
    )

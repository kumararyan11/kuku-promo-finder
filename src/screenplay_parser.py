"""Screenplay parser for microdrama scripts.
Robustly extracts metadata, scenes, camera movements, actions, dialogues, and sound cues with timestamps.
Handles formatting variations across episodes (case insensitivity, colon placement, line endings).
"""

import re
import os
from typing import List, Optional
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

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Extract Episode Number
    ep_num = 0
    ep_num_match = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
    if ep_num_match:
        ep_num = int(ep_num_match.group(1))

    # Extract Logline
    logline = ""
    logline_match = re.search(r"EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s]+:|\n---)", text, re.DOTALL | re.IGNORECASE)
    if logline_match:
        logline = logline_match.group(1).strip()

    # Extract Continuity
    continuity = ""
    continuity_match = re.search(r"CONTINUITY NOTES:\s*(.*?)(?=\n--- SCRIPT START ---|\nSCENE)", text, re.DOTALL | re.IGNORECASE)
    if continuity_match:
        continuity = continuity_match.group(1).strip()

    # Scene regex - handles SCENE 01 / SCENE 1 and case insensitive headings/starts
    scene_pattern = re.compile(
        r"SCENE\s+(\d+)\s*\n\s*(?:Scene heading|SCENE HEADING):\s*(.*?)\n\s*(?:Scene start|SCENE START):\s*([0-9:.]+)\s*\n\s*(?:Scene end|SCENE END):\s*([0-9:.]+)",
        re.IGNORECASE
    )
    
    scene_splits = list(scene_pattern.finditer(text))
    scenes: List[Scene] = []
    
    # If no explicit scene header was found, create one fallback scene spanning entire script
    if not scene_splits:
        script_start = text.find("--- SCRIPT START ---")
        start_idx = script_start + len("--- SCRIPT START ---") if script_start != -1 else 0
        end_idx = text.find("--- SCRIPT END ---")
        if end_idx == -1:
            end_idx = len(text)
        scene_bodies = [(1, "FULL EPISODE", "00:00.00", "02:00.00", text[start_idx:end_idx])]
    else:
        scene_bodies = []
        for i, match in enumerate(scene_splits):
            s_num = int(match.group(1))
            heading = match.group(2).strip()
            s_start_str = match.group(3).strip()
            s_end_str = match.group(4).strip()
            
            body_start = match.end()
            if i + 1 < len(scene_splits):
                body_end = scene_splits[i + 1].start()
            else:
                end_match = re.search(r"--- SCRIPT END ---", text[body_start:])
                body_end = body_start + end_match.start() if end_match else len(text)
            
            scene_bodies.append((s_num, heading, s_start_str, s_end_str, text[body_start:body_end]))

    # Block regex: matches **TAG:** or **TAG**: or **SPEAKER (TONE):**
    block_pattern = re.compile(
        r"\*\*([^*]+?):?\*\*:?\s*\nStart:\s*\(([0-9:.]+)\)\s*\|\s*End:\s*\(([0-9:.]+)\)\s*\n(.*?)(?=(?:\n\*\*[^*]+?:?\*\*:?|\n--- SCRIPT END ---|\Z))",
        re.DOTALL
    )

    for s_num, heading, s_start_str, s_end_str, scene_body in scene_bodies:
        s_start = parse_timestamp(s_start_str)
        s_end = parse_timestamp(s_end_str)
        
        blocks: List[ScriptBlock] = []
        for b_match in block_pattern.finditer(scene_body):
            raw_tag = b_match.group(1).strip().rstrip(":")
            b_start_str = b_match.group(2).strip()
            b_end_str = b_match.group(3).strip()
            raw_content = b_match.group(4).strip()
            
            b_start = parse_timestamp(b_start_str)
            b_end = parse_timestamp(b_end_str)
            
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
            elif any(k in tag_upper for k in ("SOUND", "SFX", "MUSIC")):
                b_type = "SOUND_FX"
                speaker = None
                tone = None
                content = raw_content
            else:
                b_type = "DIALOGUE"
                # Speaker and optional tone: e.g. "LADY JULIANA (Confused, Breathless)"
                speaker_match = re.match(r"^([^(]+)(?:\((.*)\))?$", raw_tag)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    tone = speaker_match.group(2).strip() if speaker_match.group(2) else None
                else:
                    speaker = raw_tag
                    tone = None
                
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

    return Episode(
        episode_number=ep_num,
        episode_title=f"Episode {ep_num}",
        logline=logline,
        continuity_notes=continuity,
        scenes=scenes,
        raw_filename=os.path.basename(file_path)
    )

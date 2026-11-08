import sys, os, re
sys.path.insert(0, r"C:\Users\Sudhir Kumar\.gemini\antigravity\scratch\kuku-promo-finder\src")
from screenplay_parser import parse_screenplay

ep = parse_screenplay(os.path.join(r"C:\Users\Sudhir Kumar\.gemini\antigravity\scratch\kuku-promo-finder\input_pack\I Married a Broken Soldier. He was a Duke\episode-001-Episode 1671703.txt"))
with open(os.path.join(r"C:\Users\Sudhir Kumar\.gemini\antigravity\scratch\kuku-promo-finder\input_pack\I Married a Broken Soldier. He was a Duke\episode-001-Episode 1671703.txt"), "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

# find scene 01
s_match = re.search(r"SCENE\s+(\d+)", text)
print("s_match:", s_match)
idx = text.find("Actions and dialogue:")
# Test on 1000 characters to catch dialogue
snippet = text[idx:idx+1500]
pattern = re.compile(
    r"\*\*([^*]+?):?\*\*:?\s*\nStart:\s*\(([0-9:.]+)\)\s*\|\s*End:\s*\(([0-9:.]+)\)\s*\n(.*?)(?=(?:\n\*\*[^*]+?:?\*\*:?|\n--- SCRIPT END ---|\Z))",
    re.DOTALL
)
matches = list(pattern.finditer(snippet))
print(f"Total matches in snippet: {len(matches)}")
for m in matches:
    print("Tag:", repr(m.group(1).strip().rstrip(":")), "| Start:", m.group(2), "| Content:", repr(m.group(4).strip()[:50]))

# 3-Minute Walkthrough Video Recording Script

> **Assignment:** Kuku — AI Generalist Assignment  
> **Problem 1:** Find the Promos (Ads)  
> **Target Duration:** 2 minutes 45 seconds – 3 minutes  
> **Recommended Tools:** Loom, OBS, or QuickTime / Windows Game Bar (`Win + Alt + R`)

---

## ⏱️ Visual & Narration Guide

### 🎬 Part 1: Problem Choice & The Core Challenge (0:00 – 0:45)
**Screen to Show:** Terminal running `python run_all.py` OR the top KPI banner in the Streamlit App (`streamlit run app.py`).

**Spoken Script:**
> *"Hi everyone, I'm Sudhir Kumar. For this assignment, I tackled **Problem 1: Find the Promos**.*  
> *In the vertical microdrama space—apps like Kuku, ReelShort, and DramaBox—short-form video ads on TikTok and Reels are the lifeblood of customer acquisition. But today, editors spend 4 to 6 hours per series manually watching 50 to 100 episodes to find promo moments.*  
> *I built an autonomous, two-stage AI promo finder that ingests raw screenplays, detects visceral 3-second hooks, scores unresolved cliffhangers, and schedules a phased ad rollout.*  
> *As you can see right here, our engine processed all 50 episodes of 'I Married a Broken Soldier. He was a Duke' in just **4.85 seconds**, discovering **103 ranked promos** with a **92.2% broadcast approval rate**."*

---

### 🎬 Part 2: Prototype Walkthrough & Vertical Simulator (0:45 – 1:40)
**Screen to Show:** Streamlit Web UI (`app.py`), scrolling through Tab 1 ("🔥 Ranked Promos Feed") and clicking into Tab 2 ("📱 Vertical Video Simulator").

**Spoken Script:**
> *"Let's take a look at the interactive studio. Each discovered promo is strictly constrained to **20 to 60 seconds**, with cut points mathematically snapped to natural camera transitions or dialogue boundaries—so we never cut mid-word.*  
> *Notice our ranking system isn't just chronological. It categorizes promos by growth marketing phases:*
> - *Our **Rank #1 Hero Promo** is from Episode 29, capturing Catherine's explosive accusation: 'The magistrate will call it witchcraft!'—cutting at peak tension to drive top-of-funnel mobile thumbstops.*
> - *In Tab 2, we have a **9:16 Vertical Video Preview Simulator**. Cold TikTok viewers decide whether to scroll away within the first 3 seconds. Our engine automatically generates on-screen hook captions like 'Ditched at the altar for her own sister... then he stepped up', previews the dialogue beats, and confirms the sound FX cliffhanger swell."*

---

### 🎬 Part 3: Quality Audit & Honest Failure Analysis (1:40 – 2:25)
**Screen to Show:** Tab 3 ("⚠️ Quality Audit & Failure Lab"). Point to the 8 flagged clips and failure breakdown table.

**Spoken Script:**
> *"A key requirement of this assignment was honesty: where does the tool pick badly?*  
> *Rather than hiding edge cases, we built an automated Quality Auditor that caught **8 failure instances** across our 50 episodes:*
> 1. *First, **Dangling Pronoun Ambiguity**: In 3 clips, the AI picked a high-emotion line like 'He told me not to tell you!' but a cold TikTok viewer has no idea who 'He' refers to. Our system detects this and recommends padding the start by -2.5 seconds to establish character context.*
> 2. *Second, **Clipped Reaction Beats**: In 6 clips, dialogue ended, but the visual reaction shot of Juliana's eyes hardening landed 1.2 seconds later. Our tool flags these for a +1.5-second buffer.*
> 3. *Third, **False Action Peaks**: Screaming arguments between minor servants about firewood that have high acoustic volume but zero main-story stakes. Our Protagonist Relevance Filter filters these out.*  
> *With our built-in Human-in-the-Loop controls, an editor can fix or approve flagged clips in one click."*

---

### 🎬 Part 4: Architecture, Economics & Scaling (2:25 – 2:55)
**Screen to Show:** Tab 4 ("📊 Growth Strategy & Architecture") or `docs/solution_doc.pdf`.

**Spoken Script:**
> *"Finally, how does this scale to every show Kuku makes?*  
> *If you feed 50 episodes of raw text into GPT-4o, it costs **$25 to $35 per show** and takes 15 minutes. At 100 shows a month, that's $36,000 a year.*  
> *Our **Hybrid Two-Stage Cascade** uses deterministic local parsing and heuristic feature scoring in Stage 1 to eliminate 95% of candidate noise in 4.8 seconds for $0.00.*  
> *Stage 2 passes only top candidates to our pluggable model evaluator—which supports Gemini, OpenAI, or our built-in expert engine—reducing LLM costs to **under 4 cents per show**.*  
> *All deliverables—the 2-page solution PDF, the full raw JSON and CSV catalogs, and the Streamlit studio—are ready in the repository. Thank you for your time!"*

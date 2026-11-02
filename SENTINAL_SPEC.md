# SENTINAL: AI-Assisted CCTV Incident Intelligence System

## 1. Project Overview & Architecture
SENTINAL is an automated CCTV incident intelligence platform designed for hackathon demonstration and real-world security operations. It converts raw video footage into candidate incidents with visual evidence snapshots and objective summaries for human review.

### System Architecture
```mermaid
flowchart TD
    VideoInput[Video Ingest: MP4/Upload/Sample] --> FrameExtractor[OpenCV Frame Processing]
    FrameExtractor --> Detector[YOLOv8 Tracker: Person & Luggage]
    Detector --> TemporalEngine[Temporal Event Rules Engine]
    TemporalEngine -- "Threshold triggered" --> SnapshotEngine[Evidence Snapshot Extractor]
    TemporalEngine --> LLMSummarizer[LLM Objective Summarizer (Gemini / Offline Fallback)]
    SnapshotEngine --> Storage[Evidence Store: Local & DB]
    LLMSummarizer --> Storage
    Storage --> HybridDB[(Storage Layer: SQLite + Supabase Dual-Mode)]
    HybridDB --> StreamlitUI[Streamlit Reviewer Dashboard]
    StreamlitUI -- "Triage Action: Acknowledge/Dismiss/Escalate" --> HybridDB
```

---

## 2. Core Functional Requirements
1. **Video Ingestion & Local Processing:**
   - Local OpenCV video decoding.
   - YOLOv8 (nano) detection for COCO classes (`person`, `backpack`, `handbag`, `suitcase`).
2. **Temporal Logic:**
   - Unattended item rule: track items left without an owner within radius $R$ for duration $> T$ seconds.
   - Person loitering / zone alert rule.
3. **Evidence Extraction:**
   - Save high-res keyframe crops with bounding boxes to `data/evidence/`.
4. **Objective LLM Summaries:**
   - Strict guardrails: No inference of intent, suspiciousness, guilt, or emotion.
   - Facts only: object class, duration, timestamp, distance, coordinates.
5. **Human-in-the-Loop Review Dashboard:**
   - Streamlit interface with video playback, incident cards, visual evidence comparison, and triage buttons (*Acknowledge*, *Dismiss*, *Escalate*).
6. **Dual Storage (SQLite & Supabase):**
   - Seamless local SQLite default (`sentinal.db`).
   - Optional Supabase PostgreSQL backend enabled simply via `.env` (`SUPABASE_URL`, `SUPABASE_KEY`).
7. **Git & GitHub Ready:**
   - Clean `.gitignore` protecting API keys, virtualenvs, local caches, and heavy videos.
   - Comprehensive `README.md` with demo setup instructions.

# 📋 Repository Map - Meeting Bot Codebase

## 🗂️ File Structure

### Core Modules

**Meeting Lifecycle:**
- `src/session_manager.py` - Main session orchestration, participant tracking loop, meeting end detection trigger
- `src/meeting_end_detector.py` - Meeting end detection logic (empty meeting check, leave button click)
- `src/meeting_flow/base.py` - Abstract MeetingFlow interface
- `src/meeting_flow/gmeet.py` - Google Meet flow implementation
- `src/meeting_flow/gmeet_enhanced.py` - Enhanced Google Meet flow
- `src/meeting_flow/teams.py` - Microsoft Teams flow
- `src/meeting_flow/teams_enhanced.py` - Enhanced Teams flow

**Participant Tracking:**
- `src/participant_tracker.py` - ParticipantTracker class (DEPRECATED - use ParticipantExtractor)
- `src/participant_extractor.py` - **NEW** Production-grade participant extraction
- `src/participant_name_filter.py` - Filters UI elements from participant names

**Audio Capture:**
- `src/audio.py` - AudioCaptureLoop class, main audio capture loop
- `src/audio_capture.py` - Real audio capture using CDP/MediaRecorder

**Speaker Identification:**
- `src/diarization.py` - Basic diarisation (external API or fallback)
- `src/diarization_enhanced.py` - Enhanced diarisation (Pyannote, Whisper support)

**Summary & Events:**
- `src/meeting_summary_builder.py` - **NEW** Accurate summary builder
- `src/events.py` - Event publishing (local + Azure)
- `src/local_storage.py` - Local file storage

**Infrastructure:**
- `src/main.py` - FastAPI app, endpoints
- `src/config.py` - Configuration (settings, environment variables)
- `src/playwright_client.py` - Playwright browser management
- `src/playwright_manager.py` - Enhanced Playwright with per-session profiles
- `src/storage.py` - Blob storage (local + Azure)

---

## 🔍 Key Classes & Functions

### SessionManager (`src/session_manager.py`)
- `_run_session_loops()` - Runs audio and participant tracking loops
- `participants_loop()` - **CRITICAL** - Participant tracking, leave detection logic
- `_create_flow()` - Creates platform-specific flow

### MeetingEndDetector (`src/meeting_end_detector.py`)
- `wait_for_meeting_end()` - Main loop checking for meeting end
- `_check_meeting_empty()` - **CRITICAL** - Checks if only bot remains
- `_check_gmeet_empty()` - Google Meet specific empty check
- `leave_meeting_cleanly()` - Clicks Leave button

### ParticipantExtractor (`src/participant_extractor.py`)
- `extract_participants()` - **CRITICAL** - Main extraction method
- `_extract_gmeet_participants()` - Google Meet extraction
- `_extract_via_data_self_name()` - Strategy A: data-self-name attribute
- `_extract_via_list_items()` - Strategy B: List items
- `_extract_via_contributors()` - Strategy C: Contributors section

### AudioCaptureLoop (`src/audio.py`)
- `run()` - **CRITICAL** - Main audio capture loop
- Uses `AudioCapture` from `audio_capture.py` for real capture
- Falls back to silent WAV if real capture fails

### MeetingSummaryBuilder (`src/meeting_summary_builder.py`)
- `build_summary()` - **CRITICAL** - Builds accurate summary
- Filters participants to ONLY real ones

---

## 🔗 Call Flow

```
main.py
  └─> SessionManager.enqueue_session()
      └─> _worker()
          └─> _run_session()
              └─> flow.join_meeting()
              └─> _run_session_loops()
                  ├─> AudioCaptureLoop.run() [parallel]
                  ├─> participants_loop() [parallel]
                  │   ├─> flow.read_participants()
                  │   │   └─> ParticipantExtractor.extract_participants()
                  │   └─> Check if should leave
                  └─> flow.wait_for_meeting_end()
                      └─> MeetingEndDetector.wait_for_meeting_end()
                          └─> _check_meeting_empty()
                              └─> ParticipantExtractor.extract_participants()
```

---

## ⚠️ Current Issues (To Fix)

1. **Meeting End Logic** - `src/session_manager.py` line 250-340
   - Need: Bot display name configuration
   - Need: Stricter leave conditions

2. **Participant Extraction** - `src/participant_extractor.py`
   - Need: Hard blacklist of UI text
   - Need: Better DOM selectors

3. **Audio Capture** - `src/audio.py`, `src/audio_capture.py`
   - Need: Real audio validation
   - Need: Chunk size validation

4. **Summary** - `src/meeting_summary_builder.py`
   - Need: Validate audio_chunks count
   - Need: Ensure no UI text in participants



# 🎯 Implementation Plan for Three Stories

## Overview

This document outlines the implementation plan for:
1. **Story 1:** Real Audio Capture (30-second chunks) + Speaker Identification
2. **Story 2:** Enhanced Participant Tracking + Active Speaker Detection
3. **Story 3:** Meeting End Detection + Auto Exit + Summary Publishing

---

## Story 1: Audio Capture Enhancement

### Current State
- ✅ Basic structure exists in `src/audio.py`
- ✅ 30-second chunk intervals
- ✅ Audio file storage (local + Azure)
- ✅ Speaker diarisation integration
- ❌ Currently uses placeholder silent WAVs

### Implementation Approach

**Real Audio Capture Options:**

1. **System-Level Capture (Recommended for Production)**
   - Use `pyaudio` or `sounddevice` to capture system audio
   - Requires virtual audio cable on Windows (e.g., VB-Audio Virtual Cable)
   - Pros: Most reliable, captures all meeting audio
   - Cons: Requires system setup

2. **Browser Extension Approach**
   - Create Chrome extension to capture audio from meeting tabs
   - Use MediaRecorder API within extension context
   - Pros: Works within browser security model
   - Cons: Requires extension installation

3. **Playwright CDP + JavaScript Injection (Complex)**
   - Inject scripts to capture from video elements
   - Use MediaRecorder API from page context
   - Pros: No external dependencies
   - Cons: Limited by browser security, may not work reliably

**Recommended: Hybrid Approach**
- Keep placeholder for now with clear structure
- Add system-level capture module as optional enhancement
- Document integration points clearly

### Acceptance Criteria Status
- ✅ Continuous audio capture with exact 30-second boundaries
- ✅ Speaker identification processed for every chunk
- ✅ Active speaker events in logs
- ✅ Audio files properly named and stored
- ⚠️ Real audio capture (currently placeholder - enhancement needed)

---

## Story 2: Enhanced Participant Tracking

### Current State
- ✅ Basic participant reading exists
- ✅ Join/leave tracking
- ✅ Participant update events
- ❌ No active speaker detection from UI
- ❌ No role detection (host/guest)
- ❌ Participants panel not always opened properly

### Implementation Tasks

1. **Enhanced Participants Panel Opening**
   - More robust selectors
   - Wait for panel to fully load
   - Handle panel already open case
   - Close panel after reading (optional)

2. **Active Speaker Detection**
   - Google Meet: Look for "speaking" indicator in UI
   - Teams: Look for active frame highlight
   - Check participant list for speaking indicators
   - Update participant object with `is_speaking` flag

3. **Role Detection**
   - Detect host/guest indicators
   - Extract from participant card UI
   - Add to participant data

4. **Better Participant Extraction**
   - More robust selectors
   - Handle different UI layouts
   - Extract join times from UI if available
   - Better name extraction

### Acceptance Criteria Status
- ⚠️ Participant list accurate (needs enhancement)
- ⚠️ Active speaker detection from UI (not yet implemented)
- ✅ Join/leave events tracked (already working)
- ⚠️ Process doesn't interrupt meeting (needs testing)
- ✅ Events contain meeting_id and session_id

---

## Story 3: Meeting End Detection Enhancement

### Current State
- ✅ Basic meeting end detection exists
- ✅ Summary publishing
- ✅ Session cleanup
- ❌ No screenshot on abnormal termination
- ❌ Limited end state detection
- ❌ No explicit leave button click

### Implementation Tasks

1. **Enhanced End State Detection**
   - More comprehensive state checks
   - Platform-specific detection (Google Meet vs Teams)
   - Handle various end scenarios
   - Check for disconnection states

2. **Screenshot Capture**
   - Capture screenshot before exit
   - Save to `data/error_[session_id]_[timestamp].png`
   - Include in error events

3. **Clean Exit Process**
   - Click "Leave" button if available
   - Close participants panel
   - Wait for confirmation
   - Close browser context gracefully

4. **Enhanced Summary**
   - Include error information
   - Add screenshot path if error occurred
   - Include all participant activity
   - Add speaker activity summary

### Acceptance Criteria Status
- ⚠️ Bot exits within 3-5 seconds (needs optimization)
- ✅ Summary event published (already working)
- ⚠️ Playwright context closes cleanly (needs verification)
- ⚠️ Summary stored even if abrupt end (needs enhancement)
- ✅ Logs show meeting lifecycle (already working)

---

## Implementation Priority

1. **High Priority** (Core Functionality)
   - Story 2: Enhanced participant tracking with active speaker detection
   - Story 3: Enhanced meeting end detection with screenshots

2. **Medium Priority** (Enhanced Features)
   - Story 1: Real audio capture integration (system-level option)
   - Better error handling and retries

3. **Low Priority** (Polish)
   - Advanced UI detection improvements
   - Performance optimizations

---

## Next Steps

1. Implement enhanced participant tracking (Story 2)
2. Implement enhanced meeting end detection (Story 3)
3. Create audio capture enhancement module (Story 1)
4. Add comprehensive tests
5. Update documentation




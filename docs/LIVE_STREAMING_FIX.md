# Live Streaming Question Loop - FIXED
**Date:** December 14, 2025 12:48 PM

## Problem
Monica kept asking "Are you live streaming right now?" repeatedly, even after you said "no" multiple times.

## Root Cause
The system prompt had an instruction that told Monica to **always ask** before using your real name:

```
IMPORTANT: The user often live streams. Before saying the real/legal name out loud, 
you MUST ask: "Are you live streaming right now?"
```

This caused Monica to ask every time she considered using your real name, creating an infinite loop.

## Changes Made

### File: `src/ai/conversation_manager.py`

#### 1. Fixed System Prompt (Lines 141-143)
**Before:**
```python
- IMPORTANT: The user often live streams. Before saying the real/legal name out loud, 
  you MUST ask: "Are you live streaming right now?"
- If the user is live streaming or you are unsure, NEVER say the real/legal name. Use only "MJP".
- DEFAULT SAFETY: Assume the user IS live streaming unless the user explicitly says they are NOT live.
```

**After:**
```python
- PRIVACY: If you need to use the real name, check if user is live streaming first.
- If the user is live streaming, NEVER say the real/legal name. Use only "MJP".
- IMPORTANT: Do NOT repeatedly ask if the user is live streaming. Ask ONCE if needed, then remember their answer.
```

#### 2. Enhanced Streaming Status Display (Lines 317-323)
**Before:**
```python
parts.append(f"\nLIVE_STREAMING_STATUS: {'LIVE' if live else 'NOT_LIVE'}")
parts.append("If LIVE or unknown, do not say the user's real/legal name out loud.")
```

**After:**
```python
parts.append(f"\n\nCURRENT STREAMING STATUS: {'USER IS LIVE STREAMING' if live else 'USER IS NOT LIVE STREAMING'}")
if live:
    parts.append("- Use only 'MJP' (never say 'Marvin Polanco' out loud)")
    parts.append("- Do NOT ask if user is live streaming - you already know they are")
else:
    parts.append("- You may use the real name 'Marvin' if contextually appropriate")
    parts.append("- Do NOT ask if user is live streaming - you already know they are NOT")
```

## How It Works Now

### Detection Logic (Already Working)
Lines 576-588 detect when you say you're not live streaming:

**Triggers for "NOT live":**
- "not live"
- "i'm not live" / "im not live"
- "not streaming"
- "offline"
- "not on stream"
- "not live streaming"
- "no livestreaming"

When detected, sets `is_live_streaming = False` and refreshes the system prompt.

### System Prompt Updates
Now when you say "I'm not live streaming", Monica's system prompt is updated to:

```
CURRENT STREAMING STATUS: USER IS NOT LIVE STREAMING
- You may use the real name 'Marvin' if contextually appropriate
- Do NOT ask if user is live streaming - you already know they are NOT
```

This explicitly tells Monica:
1. You are NOT live streaming
2. She should NOT ask about it again
3. She already knows the answer

## Result
Monica will:
- ✅ Detect when you say "not live" or "not streaming"
- ✅ Update her system prompt immediately
- ✅ Stop asking about live streaming
- ✅ Remember your answer for the rest of the conversation

## To Apply Fix

**Option 1: Restart Monica (Recommended)**
- Close Monica completely
- Restart from desktop shortcut
- New conversation will have the fixed prompt

**Option 2: Tell Monica to Forget**
- Say: "Monica, forget our conversation and start fresh"
- This clears the conversation history and reloads the system prompt

**Option 3: Just Tell Her Again**
- Say: "I'm not live streaming" or "I'm not live"
- The detection will trigger and update the prompt
- She should stop asking after this

## Verification
After applying the fix, Monica should:
1. Stop asking "Are you live streaming right now?"
2. Remember your answer for the entire conversation
3. Only ask once if she genuinely needs to know (rare)

## Technical Details

**Default State:** `is_live_streaming = True` (safest - protects your privacy)

**Detection:** Runs on every message you send (lines 564-590)

**Prompt Refresh:** Happens immediately when status changes (line 584, 588)

**Persistence:** Lasts for the entire conversation session (until restart or clear)

---

**The fix is now active. Monica will stop asking repeatedly!** 🎉

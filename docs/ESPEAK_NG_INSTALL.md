# Installing espeak-ng for Coqui TTS (Best Voice Quality)

## What is espeak-ng?

**espeak-ng** is a text-to-speech engine that Coqui TTS uses to generate phonemes (speech sounds). 

Without it, Coqui TTS cannot produce the **natural, human-like voice** that makes Monica sound amazing!

## Installation

### Option 1: Download Installer (Easiest)

1. **Download** espeak-ng installer:
   - Go to: https://github.com/espeak-ng/espeak-ng/releases
   - Download: `espeak-ng-X64.msi` (latest version)

2. **Run installer**:
   - Double-click the downloaded `.msi` file
   - Follow installation wizard
   - Install to default location: `C:\Program Files\eSpeak NG`

3. **Add to PATH**:
   - Open Windows Settings → System → About
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\Program Files\eSpeak NG`
   - Click OK on all dialogs

4. **Restart terminal** or reboot PC

### Option 2: Using Chocolatey (If you have it)

```powershell
choco install espeak-ng
```

### Option 3: Using Scoop (If you have it)

```powershell
scoop install espeak-ng
```

## Verify Installation

Open a new PowerShell window and run:

```powershell
espeak-ng --version
```

You should see version information like:
```
eSpeak NG text-to-speech: 1.51-dev
```

## Test Monica's Voice

After installing espeak-ng, test Monica's voice:

```powershell
cd C:\Users\mxz\StreamAnimateFog
python test_monica_voice.py
```

You should hear **natural, human-like AI voice** with Coqui TTS!

## What Happens Without espeak-ng?

Without espeak-ng:
- ❌ Coqui TTS won't work
- ⚠️ Monica will fall back to Google TTS (still good)
- ⚠️ If offline, falls back to pyttsx3 (robotic Zira voice)

With espeak-ng:
- ✅ Coqui TTS works perfectly
- ✅ **Natural, soft, sensual AI voice**
- ✅ Best quality for livestreaming
- ✅ Works offline
- ✅ Free and open source

## Quick Install Commands (Copy & Paste)

**If you don't have Chocolatey, install it first:**

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

**Then install espeak-ng:**

```powershell
choco install espeak-ng -y
```

**Verify:**

```powershell
espeak-ng --version
```

**Test Monica:**

```powershell
cd C:\Users\mxz\StreamAnimateFog
python test_monica_voice.py
```

## Troubleshooting

### "espeak-ng not found"

1. Check PATH includes `C:\Program Files\eSpeak NG`
2. Restart PowerShell/terminal
3. Try rebooting PC

### "DLL load failed"

Install Visual C++ Redistributable:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Run installer
- Restart

### "Command not recognized"

Make sure you:
1. Installed espeak-ng successfully
2. Added to PATH correctly
3. **Opened a NEW PowerShell window** (old one won't see PATH changes)

## Why This Matters

### Voice Quality Comparison

| Engine | Quality | Notes |
|--------|---------|-------|
| **Coqui TTS** | ⭐⭐⭐⭐⭐ | Natural, human-like, with espeak-ng |
| **Google TTS** | ⭐⭐⭐⭐ | Good, but requires internet |
| **pyttsx3** | ⭐⭐ | Robotic, but always works |

espeak-ng unlocks the **5-star quality** voice!

## After Installation

Once espeak-ng is installed, Monica will automatically use Coqui TTS with the **natural AI voice**.

Launch Monica:

```powershell
python launch_monica_ultimate.py
```

Say "Monica, hello!" and hear the difference! 🎤✨

## Alternative: Use Google TTS (No Installation Needed)

If you can't install espeak-ng, Monica will use Google TTS which is still **very good quality**.

The voice engine will automatically select:
1. ✅ Coqui TTS (if espeak-ng available) - BEST
2. ✅ Google TTS (if online) - GOOD
3. ✅ pyttsx3 (always) - BASIC

**You're still getting an upgrade!** Even Google TTS is much better than the old robotic voice.

## Summary

**To get the BEST natural AI voice:**
1. Download espeak-ng from releases page
2. Run installer
3. Add to PATH
4. Restart terminal
5. Test with `python test_monica_voice.py`

**Don't want to install?**
- Monica will use Google TTS (still much better than before!)
- Or fallback to pyttsx3 (like the old version)

Either way, you now have **multiple voice options** that are all better than the original mechanical voice! 🔥

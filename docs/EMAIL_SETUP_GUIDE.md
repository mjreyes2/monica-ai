# Email Setup Guide for Monica AI Crash Reports

**Date**: 2025-12-12
**User**: Marvin (marvinjr18@hotmail.com)
**Status**: Email drafts working ✅ | SMTP optional ⏳

---

## Current Status

**Email drafts are working!** All crash reports automatically create email draft files that you can manually send.

**SMTP auto-send is optional** - follow the steps below if you want Monica to automatically email crash reports.

---

## How Email Works Now (Without SMTP)

When a crash or error occurs, Monica automatically:

1. ✅ Saves crash report to `crash_reports/crash_report_TIMESTAMP.txt`
2. ✅ Creates email draft to `crash_reports/crash_report_TIMESTAMP.email.txt`
3. ✅ Includes full error details, stack trace, and system info

**You can:**
- Open the `.email.txt` file
- Copy the content
- Email it manually to yourself or support

**No setup needed!** This works right now.

---

## Optional: Enable Automatic Email Sending

If you want Monica to **automatically send** crash reports via email (instead of just creating drafts), follow these steps:

### Step 1: Choose Your Email Provider

You need SMTP server details. Here are common providers:

#### Hotmail/Outlook (Your email: marvinjr18@hotmail.com)
```
SMTP Server: smtp-mail.outlook.com
Port: 587
Username: marvinjr18@hotmail.com
Password: [Your Hotmail password or App Password]
```

**Note**: You may need to create an **App Password** instead of using your regular password:
1. Go to https://account.microsoft.com/security
2. Enable "Two-step verification" if not already enabled
3. Create an "App Password" for "Mail"
4. Use that app password (not your regular password)

#### Gmail
```
SMTP Server: smtp.gmail.com
Port: 587
Username: your_email@gmail.com
Password: [App Password - NOT your regular password]
```

**Gmail requires App Passwords**:
1. Go to https://myaccount.google.com/apppasswords
2. Generate app password for "Mail"
3. Use the 16-character password generated

#### Other Providers
- **Yahoo**: smtp.mail.yahoo.com:587
- **iCloud**: smtp.mail.me.com:587
- **Custom SMTP**: Ask your email provider

---

### Step 2: Set Environment Variables

You need to set environment variables **before launching Monica**.

#### Option A: Set in Windows System (Permanent)

1. Press `Win + X` → "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Under "User variables", click "New" and add each variable:

```
Variable Name: MONICA_SMTP_ENABLED
Value: true

Variable Name: MONICA_SMTP_SERVER
Value: smtp-mail.outlook.com

Variable Name: MONICA_SMTP_PORT
Value: 587

Variable Name: MONICA_SMTP_USER
Value: marvinjr18@hotmail.com

Variable Name: MONICA_SMTP_PASSWORD
Value: [Your App Password]

Variable Name: MONICA_SMTP_FROM
Value: marvinjr18@hotmail.com
```

4. Click OK, then **restart your computer** for changes to take effect

#### Option B: Set in Batch File (Temporary - per session)

Edit `RUN_MONICA.bat` and add these lines **before** the Python command:

```batch
@echo off
title MONICA AI - PERFECT VOICE SYSTEM
color 0A

REM Isolate environment from system Python
set PYTHONPATH=
set PYTHONHOME=

REM Email configuration
set MONICA_SMTP_ENABLED=true
set MONICA_SMTP_SERVER=smtp-mail.outlook.com
set MONICA_SMTP_PORT=587
set MONICA_SMTP_USER=marvinjr18@hotmail.com
set MONICA_SMTP_PASSWORD=your_app_password_here
set MONICA_SMTP_FROM=marvinjr18@hotmail.com

REM Change to project root
cd /d "C:\Users\mxz\monica_project"

echo Using Python: .venv\Scripts\python.exe (3.10.11)
echo PyTorch: 2.5.1+cu121

REM Use venv Python explicitly
.venv\Scripts\python.exe monica_ai\main.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Monica failed to start
)
pause
```

**Important**: Replace `your_app_password_here` with your actual App Password

---

### Step 3: Test Email Sending

Run the crash reporter test:

```batch
.venv\Scripts\python.exe monica_ai\crash_reporter.py
```

**Expected output if SMTP is configured:**
```
[CRASH REPORTER] Email draft saved to: crash_reports/crash_report_TIMESTAMP.email.txt
[CRASH REPORTER] Connecting to SMTP server: smtp-mail.outlook.com:587
[CRASH REPORTER] ✅ Email sent successfully to: marvinjr18@hotmail.com
```

**If SMTP is not configured:**
```
[CRASH REPORTER] Email draft saved to: crash_reports/crash_report_TIMESTAMP.email.txt
[CRASH REPORTER] SMTP not configured - email draft saved only
[CRASH REPORTER] To enable auto-email, set environment variables:
  MONICA_SMTP_ENABLED=true
  MONICA_SMTP_SERVER=smtp.example.com
  ...
```

---

## Security Notes

### ⚠️ Password Security

**NEVER commit passwords to Git!**

If using Option B (batch file):
- ❌ Don't share your batch file
- ❌ Don't commit it to version control
- ✅ Keep it local only

**Recommended: Use Windows Environment Variables (Option A)** - more secure

### App Passwords vs Regular Passwords

Most modern email providers **require App Passwords** for security:
- ✅ App Passwords can be revoked without changing your main password
- ✅ Limited to mail access only
- ✅ Safer if compromised

**DO NOT use your regular email password** - it won't work and is less secure.

---

## Troubleshooting

### "SMTP send failed: Authentication failed"
- Make sure you're using an **App Password**, not your regular password
- For Hotmail/Outlook: Enable two-step verification first, then create app password
- For Gmail: Generate app password at https://myaccount.google.com/apppasswords

### "SMTP send failed: Connection refused"
- Check SMTP server address and port
- Make sure your firewall allows outbound connections on port 587
- Try port 465 (SSL) instead of 587 (TLS)

### "Email draft saved instead"
- SMTP is not configured or failed
- Check environment variables are set correctly
- Check console output for specific error

### Emails not arriving
- Check your spam/junk folder
- Verify `MONICA_SMTP_USER` and `MONICA_SMTP_FROM` are correct
- Some providers require verified sender addresses

---

## What Gets Emailed?

When Monica crashes or you click "Report Issue", the email includes:

1. **Error Information**
   - Error type and message
   - Full stack trace (if exception)
   - Exit code (if training failure)

2. **System Information**
   - Python version
   - PyTorch version
   - Platform details
   - SpeechBrain version
   - PyAudio version

3. **Context**
   - What was happening when error occurred
   - Component that failed (Training, Voice Recording, etc.)
   - User ID
   - Recording counts
   - Current epoch (if training)

4. **File Attachments**
   - Crash report text file
   - Diagnostics ZIP (if using "Report Issue" button)

---

## Summary

**Current Setup (No SMTP):**
- ✅ Crash reports saved to files
- ✅ Email drafts created
- ✅ You manually send emails

**With SMTP Configured:**
- ✅ Crash reports saved to files
- ✅ Email drafts created (backup)
- ✅ **Emails sent automatically** to marvinjr18@hotmail.com

**Recommendation:** Start without SMTP (current setup works fine). Add SMTP later if you want automatic emails.

---

## Quick Reference

### Environment Variables Needed
```batch
MONICA_SMTP_ENABLED=true
MONICA_SMTP_SERVER=smtp-mail.outlook.com
MONICA_SMTP_PORT=587
MONICA_SMTP_USER=marvinjr18@hotmail.com
MONICA_SMTP_PASSWORD=[App Password]
MONICA_SMTP_FROM=marvinjr18@hotmail.com
```

### Hotmail/Outlook App Password
1. https://account.microsoft.com/security
2. Two-step verification → ON
3. App passwords → Create
4. Use generated password

---

**Last Updated**: 2025-12-12
**Status**: Email drafts working, SMTP optional

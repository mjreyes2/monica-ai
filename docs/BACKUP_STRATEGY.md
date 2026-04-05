# Monica AI - Backup Strategy

**Date:** December 13, 2025  
**Status:** Git initialized, OneDrive sync pending

---

## 🔒 CURRENT BACKUP STATUS

### ✅ Git Version Control - ACTIVE
- **Location:** `c:\Users\mxz\monica_project\.git`
- **Status:** Initialized with first commit
- **What's Protected:**
  - All source code
  - Configuration files
  - AR teaching visualizations (Python code)
  - Documentation
  - Training scripts

### ⏳ OneDrive Sync - PENDING SETUP
- **Your OneDrive Locations:**
  - Personal: `C:\Users\mxz\OneDrive`
  - Work: `C:\Users\mxz\Desktop\OneDrive - Tampa Bay Therapist & Associates`

---

## 📊 WHAT'S BACKED UP (Git)

### Included in Git:
- ✅ All Python source code
- ✅ Configuration files (YAML, JSON)
- ✅ AR teaching visualization scripts
- ✅ Documentation (MD files)
- ✅ Training scripts
- ✅ Requirements.txt
- ✅ Custom Monica modules

### Excluded from Git (Too Large):
- ❌ Virtual environments (monica_310_env, etc.)
- ❌ Trained models (*.pth, *.pt, *.ckpt)
- ❌ Model checkpoints
- ❌ Rendered videos (*.mp4)
- ❌ Audio files (*.wav, *.mp3)
- ❌ Cache files

**Why excluded?** These files are too large for Git (100MB+ limit). They'll be backed up via OneDrive instead.

---

## 🎯 RECOMMENDED BACKUP STRATEGY

### Option A: Move Entire Project to OneDrive (Recommended)
**Pros:**
- Automatic sync of everything (code + models)
- No manual backups needed
- Accessible from any device
- Version history via OneDrive

**Cons:**
- Uses OneDrive storage (~5-10GB for Monica)
- Initial upload takes time

**How to do it:**
1. Move `c:\Users\mxz\monica_project` to `C:\Users\mxz\OneDrive\monica_project`
2. OneDrive automatically syncs everything
3. Git still works normally
4. Both backups active simultaneously

### Option B: Keep Project Local, Sync Only Models
**Pros:**
- Saves OneDrive space
- Faster sync
- Code backed up via Git

**Cons:**
- Models not backed up automatically
- Need to manually copy important files

**How to do it:**
1. Keep project at `c:\Users\mxz\monica_project`
2. Create symlink: `OneDrive\monica_models` → `monica_project\models`
3. Only models sync to cloud
4. Code stays local (Git backup only)

### Option C: Git + GitHub (No OneDrive)
**Pros:**
- Free unlimited storage for code
- Professional version control
- Can share with others
- Accessible anywhere

**Cons:**
- Models not backed up (too large for GitHub)
- Need to manually backup models separately

**How to do it:**
1. Create GitHub repository
2. Push code to GitHub
3. Models stay local (manual backup needed)

---

## 💾 CURRENT FILE SIZES

Estimated sizes in your Monica project:
- **Source code:** ~50MB
- **Virtual environments:** ~2-3GB (excluded from backups)
- **Trained models:** ~1-2GB (needs OneDrive or manual backup)
- **AR teaching videos:** ~500MB (can regenerate, excluded)
- **Model checkpoints:** ~500MB (excluded)

**Total to backup:** ~3-4GB (if including models)

---

## 🚀 RECOMMENDED SETUP (Option A)

Move entire project to OneDrive for maximum protection:

```powershell
# 1. Close Monica if running
# 2. Move project to OneDrive
Move-Item "c:\Users\mxz\monica_project" "C:\Users\mxz\OneDrive\monica_project"

# 3. Create shortcut for easy access (optional)
New-Item -ItemType SymbolicLink -Path "c:\Users\mxz\monica_project" -Target "C:\Users\mxz\OneDrive\monica_project"

# 4. Wait for OneDrive to sync (check OneDrive icon in taskbar)
```

**After this:**
- ✅ All code backed up via Git
- ✅ All models backed up via OneDrive
- ✅ Automatic sync every time you save
- ✅ Can restore from any point in time
- ✅ Protected against hardware failure

---

## 📝 DAILY WORKFLOW (After Setup)

### When You Make Changes:
1. **Work normally** - OneDrive syncs automatically
2. **Commit to Git** when you reach milestones:
   ```powershell
   git add .
   git commit -m "Description of changes"
   ```

### When You Want to Save a Snapshot:
```powershell
# Commit current work
git add .
git commit -m "Checkpoint: [what you did]"

# OneDrive syncs automatically in background
```

### To See What's Changed:
```powershell
git status              # See modified files
git diff                # See exact changes
git log --oneline       # See commit history
```

### To Restore Previous Version:
```powershell
# See all commits
git log --oneline

# Restore specific file from previous commit
git checkout <commit-hash> -- path/to/file

# Restore entire project to previous state
git checkout <commit-hash>
```

---

## 🔍 VERIFY BACKUPS

### Check Git Status:
```powershell
cd c:\Users\mxz\monica_project
git status
git log --oneline -5  # See last 5 commits
```

### Check OneDrive Sync:
1. Look at OneDrive icon in system tray
2. Should show green checkmark when synced
3. Right-click files → "Free up space" means they're backed up

---

## ⚠️ IMPORTANT NOTES

### What Git Protects:
- ✅ Code changes
- ✅ Can restore any previous version
- ✅ See who changed what and when
- ✅ Undo mistakes easily

### What OneDrive Protects:
- ✅ Everything (code + models + data)
- ✅ Hardware failure protection
- ✅ Accidental deletion recovery
- ✅ Access from other devices

### Best Practice:
- **Commit to Git** after completing a feature
- **Let OneDrive sync** automatically (no action needed)
- **Check both** before major changes

---

## 🎓 GIT QUICK REFERENCE

### Common Commands:
```powershell
# See what changed
git status

# Save changes
git add .
git commit -m "Your message here"

# See history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all changes (dangerous!)
git reset --hard HEAD

# Create a branch for experiments
git checkout -b experiment-name

# Switch back to main
git checkout main
```

---

## 📊 BACKUP CHECKLIST

Before making major changes:
- [ ] Git commit current state
- [ ] Verify OneDrive is synced (green checkmark)
- [ ] Note current commit hash: `git log -1`

After completing work:
- [ ] Git commit with descriptive message
- [ ] Wait for OneDrive sync to complete
- [ ] Test that changes work

Weekly:
- [ ] Check Git log: `git log --oneline -10`
- [ ] Verify OneDrive storage not full
- [ ] Clean up old rendered videos if needed

---

## 🆘 DISASTER RECOVERY

### If You Delete Files Accidentally:
```powershell
# Restore from Git (if committed)
git checkout HEAD -- path/to/file

# Restore from OneDrive
# Right-click file → "Restore previous versions"
```

### If Computer Crashes:
1. Install Monica on new computer
2. Download from OneDrive (automatic sync)
3. Git history preserved
4. All models intact

### If You Break Something:
```powershell
# See what you changed
git diff

# Undo all changes since last commit
git reset --hard HEAD

# Go back to specific commit
git checkout <commit-hash>
```

---

## 📈 STORAGE USAGE

### Git Repository Size:
- Current: ~50MB (code only)
- Expected growth: +5-10MB per month

### OneDrive Usage (if you move project):
- Initial: ~4GB
- Growth: +500MB per month (new visualizations, models)

### Recommendations:
- Clean up old rendered videos monthly (can regenerate)
- Archive old model checkpoints after training complete
- Keep only last 3 training checkpoints

---

**Status:** Git backup active. OneDrive sync pending your decision.  
**Next Step:** Choose Option A, B, or C above and I'll help you set it up.

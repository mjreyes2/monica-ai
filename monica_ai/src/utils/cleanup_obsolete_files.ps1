# Monica Project Cleanup Script
# Removes obsolete Nemo and Whisper files
# Run this script to recover ~3-4 GB of disk space

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Monica Project Cleanup - Removing Obsolete Files" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$totalSize = 0

# Function to get directory size
function Get-DirectorySize {
    param($path)
    if (Test-Path $path) {
        $size = (Get-ChildItem -Path $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        return $size
    }
    return 0
}

# Function to format size
function Format-Size {
    param($bytes)
    if ($bytes -ge 1GB) {
        return "{0:N2} GB" -f ($bytes / 1GB)
    } elseif ($bytes -ge 1MB) {
        return "{0:N2} MB" -f ($bytes / 1MB)
    } else {
        return "{0:N2} KB" -f ($bytes / 1KB)
    }
}

Write-Host "Analyzing files to remove..." -ForegroundColor Yellow
Write-Host ""

# 1. Nemo Training Environments
$nemoClean = "C:\Users\Marvi\OneDrive\monica_project\nemo_train_clean"
$nemoEnv = "C:\Users\Marvi\OneDrive\monica_project\nemo_train_env"
$nemoModels = "C:\Users\Marvi\OneDrive\monica_project\models\nemo_personal"

Write-Host "Checking Nemo directories..." -ForegroundColor White

if (Test-Path $nemoClean) {
    $size = Get-DirectorySize $nemoClean
    $totalSize += $size
    Write-Host "  [FOUND] nemo_train_clean: $(Format-Size $size)" -ForegroundColor Yellow
} else {
    Write-Host "  [SKIP] nemo_train_clean: Not found" -ForegroundColor Gray
}

if (Test-Path $nemoEnv) {
    $size = Get-DirectorySize $nemoEnv
    $totalSize += $size
    Write-Host "  [FOUND] nemo_train_env: $(Format-Size $size)" -ForegroundColor Yellow
} else {
    Write-Host "  [SKIP] nemo_train_env: Not found" -ForegroundColor Gray
}

if (Test-Path $nemoModels) {
    $size = Get-DirectorySize $nemoModels
    $totalSize += $size
    Write-Host "  [FOUND] models/nemo_personal: $(Format-Size $size)" -ForegroundColor Yellow
} else {
    Write-Host "  [SKIP] models/nemo_personal: Not found" -ForegroundColor Gray
}

# 2. Nemo Training Scripts
Write-Host ""
Write-Host "Checking Nemo training scripts..." -ForegroundColor White

$nemoScripts = @(
    "C:\Users\Marvi\OneDrive\monica_project\monica_ai\voice_training\train_nemo_simple.py",
    "C:\Users\Marvi\OneDrive\monica_project\monica_ai\voice_training\train_nemo_patched.py",
    "C:\Users\Marvi\OneDrive\monica_project\monica_ai\voice_training\train_nemo_exp.py",
    "C:\Users\Marvi\OneDrive\monica_project\monica_ai\voice_training\train_nemo_config.yaml"
)

foreach ($script in $nemoScripts) {
    if (Test-Path $script) {
        $size = (Get-Item $script).Length
        $totalSize += $size
        Write-Host "  [FOUND] $(Split-Path $script -Leaf): $(Format-Size $size)" -ForegroundColor Yellow
    }
}

# 3. External Whisper
Write-Host ""
Write-Host "Checking external Whisper..." -ForegroundColor White

$whisperExt = "C:\Users\Marvi\OneDrive\monica_project\external\whisper"
if (Test-Path $whisperExt) {
    $size = Get-DirectorySize $whisperExt
    $totalSize += $size
    Write-Host "  [FOUND] external/whisper: $(Format-Size $size)" -ForegroundColor Yellow
} else {
    Write-Host "  [SKIP] external/whisper: Not found" -ForegroundColor Gray
}

# 4. Nemo models in voice_training
Write-Host ""
Write-Host "Checking voice_training Nemo models..." -ForegroundColor White

$voiceNemo = "C:\Users\Marvi\OneDrive\monica_project\monica_ai\voice_training\models\nemo_personal"
if (Test-Path $voiceNemo) {
    $size = Get-DirectorySize $voiceNemo
    $totalSize += $size
    Write-Host "  [FOUND] voice_training/models/nemo_personal: $(Format-Size $size)" -ForegroundColor Yellow
} else {
    Write-Host "  [SKIP] voice_training/models/nemo_personal: Not found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Total space to recover: $(Format-Size $totalSize)" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Ask for confirmation
$confirmation = Read-Host "Do you want to DELETE these files? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host ""
    Write-Host "Cleanup cancelled. No files were deleted." -ForegroundColor Yellow
    Write-Host ""
    exit
}

Write-Host ""
Write-Host "Starting cleanup..." -ForegroundColor Green
Write-Host ""

$deletedSize = 0

# Delete Nemo directories
if (Test-Path $nemoClean) {
    Write-Host "Deleting nemo_train_clean..." -ForegroundColor White
    $size = Get-DirectorySize $nemoClean
    Remove-Item $nemoClean -Recurse -Force -ErrorAction SilentlyContinue
    $deletedSize += $size
    Write-Host "  [OK] Deleted $(Format-Size $size)" -ForegroundColor Green
}

if (Test-Path $nemoEnv) {
    Write-Host "Deleting nemo_train_env..." -ForegroundColor White
    $size = Get-DirectorySize $nemoEnv
    Remove-Item $nemoEnv -Recurse -Force -ErrorAction SilentlyContinue
    $deletedSize += $size
    Write-Host "  [OK] Deleted $(Format-Size $size)" -ForegroundColor Green
}

if (Test-Path $nemoModels) {
    Write-Host "Deleting models/nemo_personal..." -ForegroundColor White
    $size = Get-DirectorySize $nemoModels
    Remove-Item $nemoModels -Recurse -Force -ErrorAction SilentlyContinue
    $deletedSize += $size
    Write-Host "  [OK] Deleted $(Format-Size $size)" -ForegroundColor Green
}

# Delete Nemo scripts
Write-Host "Deleting Nemo training scripts..." -ForegroundColor White
foreach ($script in $nemoScripts) {
    if (Test-Path $script) {
        $size = (Get-Item $script).Length
        Remove-Item $script -Force -ErrorAction SilentlyContinue
        $deletedSize += $size
    }
}
Write-Host "  [OK] Scripts deleted" -ForegroundColor Green

# Delete external Whisper
if (Test-Path $whisperExt) {
    Write-Host "Deleting external/whisper..." -ForegroundColor White
    $size = Get-DirectorySize $whisperExt
    Remove-Item $whisperExt -Recurse -Force -ErrorAction SilentlyContinue
    $deletedSize += $size
    Write-Host "  [OK] Deleted $(Format-Size $size)" -ForegroundColor Green
}

# Delete voice_training Nemo models
if (Test-Path $voiceNemo) {
    Write-Host "Deleting voice_training/models/nemo_personal..." -ForegroundColor White
    $size = Get-DirectorySize $voiceNemo
    Remove-Item $voiceNemo -Recurse -Force -ErrorAction SilentlyContinue
    $deletedSize += $size
    Write-Host "  [OK] Deleted $(Format-Size $size)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Space recovered: $(Format-Size $deletedSize)" -ForegroundColor Green
Write-Host ""
Write-Host "Monica now uses SpeechBrain exclusively." -ForegroundColor Cyan
Write-Host "All obsolete Nemo and Whisper files have been removed." -ForegroundColor Cyan
Write-Host ""

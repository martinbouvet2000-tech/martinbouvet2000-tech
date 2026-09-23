# Publish last night's run to the profile README.
# Called at the end of the night agent's own run, so it needs no second
# scheduled task and no assumption about the laptop still being awake.
# Costs nothing but 4 KB: it reads counters and draws an SVG, no model involved.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

python scripts/collect_nightly.py
if ($LASTEXITCODE -ne 0) { Write-Error "collect failed"; exit 1 }
python scripts/build_nightly.py
if ($LASTEXITCODE -ne 0) { Write-Error "build failed"; exit 1 }

# Stage only our two files: the repo may hold unrelated work in progress.
git add assets/last-run.json assets/nightly.svg
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host "same night, nothing to publish"; exit 0 }

git commit -m "chore: replay the night of $(Get-Date -Format yyyy-MM-dd)" --quiet
if ($LASTEXITCODE -ne 0) { Write-Error "commit failed"; exit 1 }

# --autostash: the daily Action commits here too, and this repo often has
# unstaged edits of mine. Without it the rebase refuses to start.
git pull --rebase --autostash --quiet
if ($LASTEXITCODE -ne 0) { Write-Error "pull failed — nothing pushed, will retry tomorrow"; exit 1 }

git push --quiet
if ($LASTEXITCODE -ne 0) { Write-Error "push failed — commit kept locally"; exit 1 }

Write-Host "published the night of $((Get-Content assets/last-run.json | ConvertFrom-Json).night)"

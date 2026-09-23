# Publish last night's run to the profile README.
# Runs on my machine after the night agent, because its state never leaves it.
# Scheduled at 00:45 Paris; if the machine was off, the terminal keeps showing
# the last real run and says which night it was — it never invents one.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

python scripts/collect_nightly.py
python scripts/build_nightly.py

git add assets/last-run.json assets/nightly.svg
if (git diff --cached --quiet) {
    Write-Host "nothing changed"
    exit 0
}
git commit -m "chore: replay the night of $(Get-Date -Format yyyy-MM-dd)" | Out-Null
git pull --rebase --quiet
git push --quiet
Write-Host "published"

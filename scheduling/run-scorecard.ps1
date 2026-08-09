# Agentic BI Team — unattended scorecard run (Windows Task Scheduler).
#
#   powershell -NoProfile -File scheduling\run-scorecard.ps1 -Period weekly
#
# A scheduled task does not inherit your interactive session's environment, so
# warehouse credentials must be machine-level environment variables (or set in
# the .env this script reads). Test by hand before trusting the schedule.
#
# See scheduling/SCHEDULING.md.

[CmdletBinding()]
param(
    [ValidateSet("weekly", "monthly")]
    [string]$Period = "weekly"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Credentials: variable names live in .env.example, values in .env (gitignored).
$envFile = Join-Path $RepoRoot ".env"
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        $trimmed = $line.Trim()
        if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
        $name, $value = $trimmed -split "=", 2
        if ($value) {
            Set-Item -Path "Env:$($name.Trim())" -Value $value.Trim().Trim('"')
        }
    }
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Error @'
The 'claude' CLI is not on PATH.

A scheduled task runs with the machine PATH, not yours. Either use the full path
to claude.cmd in this script, or add its install directory to the system PATH.
'@
    exit 1
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
Write-Output "=== $stamp - /scorecard $Period in $RepoRoot"
claude -p "/scorecard $Period" --permission-mode acceptEdits

$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
Write-Output "=== $stamp - /health-check"
claude -p "/health-check" --permission-mode acceptEdits
if (-not $?) { Write-Warning "Health check exited non-zero; see output above." }

# The git history is the team's audit trail: each period's numbers, with a diff
# against the last. Commit locally; pushing is left to you deliberately.
$dirty = git status --porcelain scorecards/ knowledge/
if ($dirty) {
    git add scorecards/ knowledge/
    git commit -m "chore: $Period scorecard $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd'))"
    Write-Output "Committed. Push when you have reviewed it."
} else {
    Write-Output "Nothing was written. That usually means the run failed rather than"
    Write-Output "that there was no news - check the output above."
}

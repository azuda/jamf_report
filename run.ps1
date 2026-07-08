# run.ps1
# Windows equivalent of run.sh. Task Scheduler can't redirect output,
# so this wrapper appends all output to logs\report.log itself.

$Project = $PSScriptRoot
$Python = Join-Path $Project ".venv\Scripts\python.exe"
$LogDir = Join-Path $Project "logs"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

& $Python (Join-Path $Project "main.py") *>> (Join-Path $LogDir "report.log")
exit $LASTEXITCODE

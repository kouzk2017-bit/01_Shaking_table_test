param(
    [ValidateSet('model','gravity','modal','trial')][string]$Stage = 'trial',
    [int]$Case = 13,
    [double]$Duration = 20,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $tjuPython = Join-Path $PSScriptRoot '..\..\..\02_TJU_test\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $tjuPython) {
        $Python = (Resolve-Path -LiteralPath $tjuPython).Path
    } else {
        $Python = (Get-Command python -ErrorAction Stop).Source
    }
}
Push-Location -LiteralPath $PSScriptRoot
try {
    & $Python -B -m entrypoints.trial --stage $Stage --case $Case --duration $Duration
    if ($LASTEXITCODE -ne 0) { throw "OpenSees run failed (exit $LASTEXITCODE); inspect the reported solver.log." }
} finally {
    Pop-Location
}

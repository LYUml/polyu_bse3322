# Run a finite Group 18 FDS queue locally. Existing matching runs are reused.
param([int]$MaxFds = 16)
$ErrorActionPreference = 'Stop'
if ($MaxFds -lt 1) { throw 'MaxFds must be positive' }
$project = Split-Path $PSScriptRoot -Parent
$results = Join-Path $project '04_Results'
$bin = 'C:/Program Files/PyroSim 2026/fds'
$env:Path = "$bin;$bin/mpi;$env:Path"
$env:OMP_NUM_THREADS = '1'
$generator = Join-Path $PSScriptRoot 'generate_design.cjs'
$log = Join-Path $results 'design_queue.log'
function Record($message) {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) $message"
}
# First complete the six scenarios of the same physical design, then expand
# the design space at the common OP-6, 0.02 screening condition.
$jobs = @()
foreach ($op in @(1,6)) {
    foreach ($soot in @('0.02','0.05','0.1')) {
        $jobs += ,@($op,$soot,'0.16','0.16')
    }
}
foreach ($depth in @('0','0.08','0.16','0.24')) {
    foreach ($flow in @('0.08','0.16','0.24','0.32')) {
        $jobs += ,@(6,'0.02',$depth,$flow)
    }
}
$mutex = [Threading.Mutex]::new($false,'Local\BSE3322DesignQueue')
if (!$mutex.WaitOne(0)) { throw 'Another copy of the queue is active' }
try {
    foreach ($jobArgs in $jobs) {
        $deck = @(& node $generator @jobArgs 120)
        if ($LASTEXITCODE -ne 0 -or $deck[0] -notmatch "CHID='([a-zA-Z0-9_]+)'") { throw 'Invalid generated case' }
        $id = $Matches[1]
        $caseDir = Join-Path $results $id
        $inputFile = Join-Path $caseDir "$id.fds"
        while (!(Test-Path -LiteralPath $caseDir) -and @(Get-Process -Name fds -ErrorAction SilentlyContinue).Count -ge $MaxFds) { Start-Sleep -Seconds 15 }
        if (Test-Path -LiteralPath $caseDir) {
            if (!(Test-Path -LiteralPath $inputFile) -or (Compare-Object (Get-Content -LiteralPath $inputFile) $deck)) { throw "Existing input differs: $id" }
            $errFile = Join-Path $caseDir 'stderr.log'
            $finished = (Test-Path $errFile) -and (Select-String -LiteralPath $errFile -SimpleMatch 'FDS completed successfully' -Quiet)
            $live = Get-CimInstance Win32_Process -Filter "Name='fds.exe'" | Where-Object { $_.CommandLine -like "*$id.fds*" }
            if (!$finished -and !$live) { throw "Inspect interrupted case before retry: $id" }
            Record "reuse $id"
            continue
        }

        $null = New-Item -ItemType Directory -Path $caseDir
        $deck | Set-Content -Encoding ascii -LiteralPath $inputFile
        $p = Start-Process -FilePath "$bin/fds.exe" -ArgumentList "$id.fds" -WorkingDirectory $caseDir -WindowStyle Hidden -RedirectStandardError "$caseDir/stderr.log" -PassThru
        Record "start $id pid=$($p.Id)"
    }
} finally { $mutex.ReleaseMutex(); $mutex.Dispose() }

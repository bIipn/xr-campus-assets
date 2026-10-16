<#
.SYNOPSIS
  Run the headless editor setup (Scripts/setup_project.py) and check every WTA_RESULT line.
.DESCRIPTION
  1. configure_plugins.py enables the optional plugins this engine has.
  2. Builds the editor module first if Binaries\Win64\UnrealEditor-WalkTheArchive.dll is missing.
  3. UnrealEditor-Cmd <uproject> -ExecutePythonScript=<Scripts\setup_project.py> -unattended -nopause
     -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal, tee'd to Tools\.cache\setup.log.
  4. check_results.py judges the log; the script exits non-zero if the editor or any step failed.
  The first run compiles shaders and can take 10-40 minutes before the first step prints.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\setup_project.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\setup_project.ps1 -Steps probe,import_meshes
#>
param(
    [string[]]$Steps = @('all'),   # comma list for WTA_STEPS (probe,import_meshes,import_art,data_tables,build_level,lighting,actors,navmesh,project_settings,verify)
    [switch]$NullRHI,         # no rendering device (machines without a usable GPU session; screenshots will not work)
    [switch]$NoBuild,         # do not build the editor module automatically when it is missing
    [switch]$SkipPlugins,     # skip configure_plugins.py
    [switch]$Force            # run even if an editor has this project open (not recommended)
)
. (Join-Path $PSScriptRoot '_common.ps1')
# -Steps a,b arrives as one string under powershell -File and as an array inside PowerShell; normalise to 'a,b'.
$stepsCsv = (@($Steps | ForEach-Object { "$_" -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ',')
if (-not $stepsCsv) { $stepsCsv = 'all' }

Write-Step 'Setup project (headless editor Python)'
if (-not (Test-Path -LiteralPath $script:UProject)) { Write-Fail ('no project file at ' + $script:UProject); exit 1 }
if (-not (Test-Path -LiteralPath $script:SetupScript)) { Write-Fail ('no setup script at ' + $script:SetupScript); exit 1 }
$engine = Get-RequiredEngine
$editorCmd = Get-Prop $engine 'editor_cmd' ''
if (-not (Test-FileExists $editorCmd)) { Write-Fail ('UnrealEditor-Cmd.exe missing at ' + $editorCmd); exit 1 }
# Get-EnginePython returns an array (exe plus fixed args) via the comma operator; do not wrap it in @() or it nests.
$python = Get-EnginePython $engine
if ($null -eq $python) { Write-Fail 'no Python found (the engine ships one under Engine\Binaries\ThirdParty\Python3\Win64).'; exit 1 }

if ($script:SetupScript -match '\s') {
    Write-Warn ('the setup script path contains spaces (' + $script:SetupScript + '). -ExecutePythonScript treats the first space-separated token as the file, so the run may never start a step; move the repo to a path without spaces (COWORK.md step 0) if no WTA_RESULT line appears.')
}

if ((Test-EditorOpenOnProject) -and -not $Force) {
    Write-Fail 'An Unreal Editor has this project open. It holds a write lock on loaded assets; close it and rerun (or pass -Force).'
    exit 1
}

$cache = Initialize-CacheDir
$log = Join-Path $cache 'setup.log'
$engineLog = Join-Path $cache 'setup_editor_full.log'
if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }
Write-Note ('log: ' + $log)

if (-not $SkipPlugins) {
    Write-Step 'Optional plugins'
    $cfgScript = Join-Path $script:CommonDir 'configure_plugins.py'
    $pyArgs = '"' + $cfgScript + '" --uproject "' + $script:UProject + '" --engine "' + (Get-Prop $engine 'root' '') + '"'
    if ($python.Length -gt 1) { $pyArgs = ($python[1..($python.Length - 1)] -join ' ') + ' ' + $pyArgs }
    $code = Invoke-Logged -FilePath $python[0] -ArgumentString $pyArgs -LogPath $log
    if ($code -ne 0) { Write-Fail ('configure_plugins.py failed (exit ' + $code + ')'); exit $code }
}

$dll = Join-Path $script:ProjectDir ('Binaries\Win64\UnrealEditor-' + $script:ProjectName + '.dll')
if (-not (Test-FileExists $dll)) {
    if ($NoBuild) { Write-Fail ('editor module missing (' + $dll + '); run build_editor.ps1 first.'); exit 1 }
    Write-Step 'Editor module missing; building it first'
    & (Join-Path $PSScriptRoot 'build_editor.ps1')
    if ($LASTEXITCODE -ne 0) { Write-Fail 'build_editor.ps1 failed; see its log.'; exit $LASTEXITCODE }
}

Write-Step 'Run UnrealEditor-Cmd'
$envVars = @{}
if ($stepsCsv -ne 'all') { $envVars['WTA_STEPS'] = $stepsCsv; Write-Note ('WTA_STEPS=' + $stepsCsv) }
$argStr = '"' + $script:UProject + '" -ExecutePythonScript="' + $script:SetupScript + '" -unattended -nopause -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal -abslog="' + $engineLog + '"'
if ($NullRHI) { $argStr += ' -NullRHI' }
Write-Note 'First run on this machine: shader compilation can take 10-40 minutes before the first WTA_RESULT line.'
$ueExit = Invoke-Logged -FilePath $editorCmd -ArgumentString $argStr -LogPath $log -Environment $envVars -WorkingDirectory $script:ProjectDir
Write-Note ('UnrealEditor-Cmd exit code: ' + $ueExit)

Write-Step 'Check results'
$checkScript = Join-Path $script:CommonDir 'check_results.py'
$checkArgs = '"' + $checkScript + '" "' + $log + '"'
if ($stepsCsv -ne 'all') { $checkArgs += ' --steps "' + $stepsCsv + '"' }
if ($python.Length -gt 1) { $checkArgs = ($python[1..($python.Length - 1)] -join ' ') + ' ' + $checkArgs }
$checkExit = Invoke-Logged -FilePath $python[0] -ArgumentString $checkArgs
$ok = ($ueExit -eq 0) -and ($checkExit -eq 0)
Write-Note ('setup log: ' + $log)
Write-Note ('full engine log: ' + $engineLog)
Write-ResultLine 'setup_project' $ok @{ editor_exit = $ueExit; check_exit = $checkExit; log = $log; steps = $stepsCsv }
if (-not $ok) { exit 1 }
exit 0

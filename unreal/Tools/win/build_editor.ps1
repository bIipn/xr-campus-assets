<#
.SYNOPSIS
  Generate project files and build the WalkTheArchiveEditor target with UE 5.8's Build.bat.
.DESCRIPTION
  Uses the engine's UnrealBuildTool for -projectfiles (falls back to RunUBT.bat or the version
  selector) and Engine\Build\BatchFiles\Build.bat for the compile. Output is tee'd to
  Tools\.cache\build_editor.log. Exit code is UBT's.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\build_editor.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\build_editor.ps1 -Config DebugGame
#>
param(
    [ValidateSet('Development', 'DebugGame', 'Debug')][string]$Config = 'Development',
    [string]$Target = 'WalkTheArchiveEditor',
    [switch]$SkipProjectFiles
)
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Step ('Build ' + $Target + ' ' + $Config)
if (-not (Test-Path -LiteralPath $script:UProject)) { Write-Fail ('no project file at ' + $script:UProject); exit 1 }
$sourceDir = Join-Path $script:ProjectDir 'Source'
if (-not (Test-Path -LiteralPath (Join-Path $sourceDir ($Target + '.Target.cs')))) {
    Write-Fail ('no ' + $Target + '.Target.cs under ' + $sourceDir + '; the C++ sources must be present before building.')
    exit 1
}
$engine = Get-RequiredEngine
$buildBat = Get-Prop $engine 'build' ''
if (-not (Test-FileExists $buildBat)) { Write-Fail ('Build.bat missing at ' + $buildBat); exit 1 }

$vs = Get-VsInstall
if ($null -eq $vs) { Write-Warn 'Visual Studio was not found by vswhere; the build will fail without the C++ toolchain (run install_prereqs.ps1).' }
elseif (-not $vs.HasGameWorkload) { Write-Warn ('Visual Studio ' + $vs.Version + ' lacks the "Game development with C++" workload (run install_prereqs.ps1).') }

$log = Join-Path (Initialize-CacheDir) 'build_editor.log'
if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }
Write-Note ('log: ' + $log)
$projectArg = '-project="' + $script:UProject + '"'

if (-not $SkipProjectFiles) {
    Write-Step 'Generate project files'
    $ubt = Get-Prop $engine 'ubt' ''
    $runUbt = Get-Prop $engine 'run_ubt' ''
    $uvs = Get-Prop $engine 'version_selector' ''
    $code = 1
    if (Test-FileExists $ubt) {
        $code = Invoke-Logged -FilePath $ubt -ArgumentString ('-projectfiles ' + $projectArg + ' -game -rocket -progress') -LogPath $log
    } elseif (Test-FileExists $runUbt) {
        $code = Invoke-Logged -FilePath $runUbt -ArgumentString ('-projectfiles ' + $projectArg + ' -game -rocket -progress') -LogPath $log
    } elseif (Test-FileExists $uvs) {
        $code = Invoke-Logged -FilePath $uvs -ArgumentString ('/projectfiles "' + $script:UProject + '"') -LogPath $log
    } else {
        Write-Fail 'neither UnrealBuildTool.exe, RunUBT.bat nor UnrealVersionSelector.exe was found in the engine.'
    }
    if ($code -ne 0) {
        Write-Fail ('project file generation failed (exit ' + $code + '); see ' + $log)
        Write-ResultLine 'build_editor' $false @{ phase = 'projectfiles'; exit_code = $code; log = $log }
        exit $code
    }
}

Write-Step 'Compile'
$argStr = $Target + ' Win64 ' + $Config + ' -Project="' + $script:UProject + '" -WaitMutex -FromMsBuild'
$code = Invoke-Logged -FilePath $buildBat -ArgumentString $argStr -LogPath $log
$dll = Join-Path $script:ProjectDir ('Binaries\Win64\UnrealEditor-' + $script:ProjectName + '.dll')
if ($Config -ne 'Development') { $dll = Join-Path $script:ProjectDir ('Binaries\Win64\UnrealEditor-' + $script:ProjectName + '-Win64-' + $Config + '.dll') }
$built = (Test-FileExists $dll)
Write-Note ('exit code: ' + $code + '; module binary present: ' + $built)
Write-Note ('log: ' + $log)
Write-ResultLine 'build_editor' (($code -eq 0) -and $built) @{ target = $Target; config = $Config; exit_code = $code; binary = $dll; log = $log }
if ($code -ne 0) { exit $code }
if (-not $built) { exit 1 }
exit 0

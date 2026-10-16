<#
.SYNOPSIS
  Launch Walk the Archive as a game from the editor binary (-game) in a 1920x1080 window.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\play.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\play.ps1 -ResX 2560 -ResY 1440 -Wait
#>
param(
    [int]$ResX = 1920,
    [int]$ResY = 1080,
    [string]$Map = '',    # optional map path, e.g. /Game/WTA/Maps/L_Campus (default: GameDefaultMap)
    [switch]$Fullscreen,
    [switch]$ShowLog,     # -log window with the game's output
    [switch]$Wait         # wait for the game to exit and return its exit code
)
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Step 'Play'
if (-not (Test-Path -LiteralPath $script:UProject)) { Write-Fail ('no project file at ' + $script:UProject); exit 1 }
$engine = Get-RequiredEngine
$editor = Get-Prop $engine 'editor' ''
if (-not (Test-FileExists $editor)) { Write-Fail ('UnrealEditor.exe missing at ' + $editor); exit 1 }
$dll = Join-Path $script:ProjectDir ('Binaries\Win64\UnrealEditor-' + $script:ProjectName + '.dll')
if (-not (Test-FileExists $dll)) { Write-Fail ('editor module not built (' + $dll + '); run build_editor.ps1 and setup_project.ps1 first.'); exit 1 }

$argStr = '"' + $script:UProject + '"'
if ($Map) { $argStr += ' ' + $Map }
$argStr += ' -game -ResX=' + $ResX + ' -ResY=' + $ResY
if ($Fullscreen) { $argStr += ' -fullscreen' } else { $argStr += ' -windowed' }
if ($ShowLog) { $argStr += ' -log' }
$proc = Start-Process -FilePath $editor -ArgumentList $argStr -WorkingDirectory $script:ProjectDir -PassThru
Write-Note ('started PID ' + $proc.Id + ': "' + $editor + '" ' + $argStr)
Write-Note 'Controls: WASD move, mouse look, Shift sprint, Space jump, E/LMB interact, Tab cursor, T tour, M map, Esc menu.'
if ($Wait) {
    $proc.WaitForExit()
    Write-ResultLine 'play' ($proc.ExitCode -eq 0) @{ pid = $proc.Id; exit_code = $proc.ExitCode }
    exit $proc.ExitCode
}
Write-ResultLine 'play' $true @{ pid = $proc.Id }
exit 0

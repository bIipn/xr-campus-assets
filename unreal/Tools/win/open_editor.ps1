<#
.SYNOPSIS
  Open WalkTheArchive.uproject in the UE 5.8 editor (detached).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\open_editor.ps1
#>
param(
    [switch]$Wait,     # wait for the editor to close and return its exit code
    [switch]$ShowLog   # pass -log so the editor opens a log window
)
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Step 'Open editor'
if (-not (Test-Path -LiteralPath $script:UProject)) { Write-Fail ('no project file at ' + $script:UProject); exit 1 }
$engine = Get-RequiredEngine
$editor = Get-Prop $engine 'editor' ''
if (-not (Test-FileExists $editor)) { Write-Fail ('UnrealEditor.exe missing at ' + $editor); exit 1 }
$dll = Join-Path $script:ProjectDir ('Binaries\Win64\UnrealEditor-' + $script:ProjectName + '.dll')
if (-not (Test-FileExists $dll)) { Write-Warn ('editor module not built (' + $dll + '); the editor will offer to compile it. Prefer build_editor.ps1.') }

# Start-Process passes a single -ArgumentList string verbatim, so the quotes survive.
$argStr = '"' + $script:UProject + '"'
if ($ShowLog) { $argStr += ' -log' }
$proc = Start-Process -FilePath $editor -ArgumentList $argStr -WorkingDirectory $script:ProjectDir -PassThru
Write-Note ('started PID ' + $proc.Id + ': "' + $editor + '" ' + $argStr)
if ($Wait) {
    $proc.WaitForExit()
    Write-Note ('editor exited with ' + $proc.ExitCode)
    Write-ResultLine 'open_editor' ($proc.ExitCode -eq 0) @{ pid = $proc.Id; exit_code = $proc.ExitCode }
    exit $proc.ExitCode
}
Write-ResultLine 'open_editor' $true @{ pid = $proc.Id }
exit 0

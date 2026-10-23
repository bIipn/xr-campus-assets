<#
.SYNOPSIS
  Two games on this computer play a guided visit together and the play test says PASS or FAIL for each check.
.DESCRIPTION
  The first game runs WTAPlayTest group_lead: it names its player "Ms. Keller" and reloads the campus as a listen
  server (the guide). Once its log says it is listening, the second game runs WTAPlayTest group_join and joins it at
  127.0.0.1 as "Ana" (the visitor). Each then plays its part (see Core/WTAPlayTest.h): the visitor arrives beside the
  guide, follows two tour stops, comes when gathered, sees the tour end and leaves; the guide checks the same from its
  side. Screenshots land in Saved/Screenshots/WindowsEditor/QA (play_NN_group_guide_* and play_NN_group_guest_*) and are
  copied to -Out. The run ends when both logs say "WTA_PLAY done".
  -multihome=127.0.0.1 keeps the game port on this computer (no firewall prompt), -WTANoBeacon keeps the network
  beacon off. The save game and graphics settings are put back afterwards.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\visit_qa.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\visit_qa.ps1 -Out C:\temp\visit -Res 1600x900
#>
param(
    [int]$TimeoutSec = 1500,
    [string]$Res = '1280x720',
    [string]$Out = '',
    [string]$Editor = ''     # an UnrealEditor.exe to use instead of the engine's (e.g. the DebugGame one)
)
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Step 'Guided visit QA (two games)'
if (-not $Editor) {
    $engine = Get-RequiredEngine
    $Editor = Get-Prop $engine 'editor' ''
}
if (-not (Test-FileExists $Editor)) { Write-Fail ('no editor at ' + $Editor); exit 1 }
$saved = Join-Path $script:ProjectDir 'Saved'
$qa = Join-Path $saved 'Screenshots\WindowsEditor\QA'
if (-not $Out) { $Out = Join-Path $saved 'QA\visit' }
$hostLog = Join-Path $saved 'QA\visit_guide.log'
$guestLog = Join-Path $saved 'QA\visit_visitor.log'
New-Item -ItemType Directory -Force -Path $qa, $Out, (Split-Path $hostLog) | Out-Null
Get-ChildItem $qa -Filter 'play_*_group_*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
foreach ($l in @($hostLog, $guestLog)) { if (Test-Path $l) { Remove-Item $l -Force } }

# Keep the player's own progress and settings: both games write the same save.
$keep = @((Join-Path $saved 'SaveGames\WalkTheArchive.sav'), (Join-Path $saved 'Config\WindowsEditor\GameUserSettings.ini'))
$backup = Join-Path $saved 'QA\visit_backup'
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach ($f in $keep) { if (Test-Path $f) { Copy-Item $f $backup -Force } }

$w, $h = $Res.Split('x')
$common = '"' + $script:UProject + '" -game -windowed -ResX=' + $w + ' -ResY=' + $h + ' -nosound -multihome=127.0.0.1 -WTANoBeacon'
$guide = Start-Process -FilePath $Editor -ArgumentList ($common + ' -WinX=0 -WinY=40 -abslog="' + $hostLog + '" -ExecCmds="WTAPlayTest group_lead"') -PassThru
Write-Note ('guide PID ' + $guide.Id)
$t0 = Get-Date
$listening = $false
while (((Get-Date) - $t0).TotalSeconds -lt 300) {
    Start-Sleep -Seconds 3
    if (Select-String -Path $hostLog -Pattern 'WTA_VISIT role guide' -SimpleMatch -Quiet -ErrorAction SilentlyContinue) { $listening = $true; break }
    if ($guide.HasExited) { break }
}
if (-not $listening) { Write-Fail 'the guide never started listening'; Stop-Process -Id $guide.Id -Force -ErrorAction SilentlyContinue; exit 1 }
Start-Sleep -Seconds 8
$visitor = Start-Process -FilePath $Editor -ArgumentList ($common + ' -WinX=' + ([int]$w + 20) + ' -WinY=40 -abslog="' + $guestLog + '" -ExecCmds="WTAPlayTest group_join"') -PassThru
Write-Note ('visitor PID ' + $visitor.Id)

$done = @{ guide = $false; visitor = $false }
while (((Get-Date) - $t0).TotalSeconds -lt $TimeoutSec) {
    Start-Sleep -Seconds 5
    if (-not $done.visitor) { $done.visitor = [bool](Select-String -Path $guestLog -Pattern 'WTA_PLAY done' -SimpleMatch -Quiet -ErrorAction SilentlyContinue) }
    if (-not $done.guide) { $done.guide = [bool](Select-String -Path $hostLog -Pattern 'WTA_PLAY done' -SimpleMatch -Quiet -ErrorAction SilentlyContinue) }
    if ($done.guide -and $done.visitor) { break }
    if ($guide.HasExited -and $visitor.HasExited) { break }
}
Start-Sleep -Seconds 2
foreach ($p in @($visitor, $guide)) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
foreach ($f in $keep) { $b = Join-Path $backup (Split-Path $f -Leaf); if (Test-Path $b) { Copy-Item $b $f -Force } }

Get-ChildItem $Out -Filter '*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
Copy-Item (Join-Path $qa 'play_*_group_*.png') $Out -Force -ErrorAction SilentlyContinue
$pass = 0; $fail = 0
foreach ($pair in @(@('guide', $hostLog), @('visitor', $guestLog))) {
    $lines = Select-String -Path $pair[1] -Pattern 'WTA_PLAY (\w+) (PASS|FAIL|SKIP|INFO)' -ErrorAction SilentlyContinue | ForEach-Object { $_.Line.Substring($_.Line.IndexOf('WTA_PLAY')) }
    foreach ($l in $lines) { Write-Note ($pair[0] + ': ' + $l); if ($l -match ' PASS ') { $pass++ } elseif ($l -match ' FAIL ') { $fail++ } }
    Select-String -Path $pair[1] -Pattern 'LogWTA: (Warning|Error)|Fatal error|Unhandled Exception' -ErrorAction SilentlyContinue | Select-Object -First 10 | ForEach-Object { Write-Note ($pair[0] + ' log: ' + $_.Line) }
}
$ok = $done.guide -and $done.visitor -and $fail -eq 0
Write-ResultLine 'visit_qa' $ok @{ pass = $pass; fail = $fail; guide_done = $done.guide; visitor_done = $done.visitor; shots = (Get-ChildItem $Out -Filter '*.png').Count; out = $Out }
if ($ok) { exit 0 } else { exit 1 }

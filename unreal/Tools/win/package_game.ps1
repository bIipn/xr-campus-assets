<#
.SYNOPSIS
  Cook and package Walk the Archive for Win64 with RunUAT BuildCookRun.
.DESCRIPTION
  RunUAT.bat BuildCookRun -project=<uproject> -noP4 -platform=Win64 -clientconfig=<Config>
  -build -cook -allmaps -stage -pak -iostore -archive -archivedirectory=unreal\Packaged\Win64
  Output is tee'd to Tools\.cache\package_Win64.log. The playable build lands in
  unreal\Packaged\Win64\Windows\WalkTheArchive.exe; the project's Fonts and ThirdParty\whisper folders are copied
  into Windows\WalkTheArchive beside it.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\package_game.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\package_game.ps1 -Config Shipping
#>
param(
    [ValidateSet('Development', 'Shipping', 'DebugGame', 'Test')][string]$Config = 'Development',
    [string]$Archive = '',   # archive folder (default unreal\Packaged\Win64)
    [switch]$SkipBuild,      # reuse the compiled game binaries
    [switch]$NoIoStore       # classic .pak containers instead of IoStore (.utoc/.ucas)
)
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Step ('Package Win64 ' + $Config)
if (-not (Test-Path -LiteralPath $script:UProject)) { Write-Fail ('no project file at ' + $script:UProject); exit 1 }
$engine = Get-RequiredEngine
$runUat = Get-Prop $engine 'run_uat' ''
if (-not (Test-FileExists $runUat)) { Write-Fail ('RunUAT.bat missing at ' + $runUat); exit 1 }
if (-not $Archive) { $Archive = Join-Path (Join-Path $script:UnrealDir 'Packaged') 'Win64' }
New-Item -ItemType Directory -Path $Archive -Force | Out-Null
if ((Test-EditorOpenOnProject)) { Write-Warn 'An editor has this project open; close it if the cook fails to save or lock files.' }

$log = Join-Path (Initialize-CacheDir) ('package_Win64_' + $Config + '.log')
if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }
Write-Note ('log: ' + $log)
Write-Note ('archive: ' + $Archive)

$argStr = 'BuildCookRun -project="' + $script:UProject + '" -noP4 -utf8output -unattended -platform=Win64 -clientconfig=' + $Config
if (-not $SkipBuild) { $argStr += ' -build' }
$argStr += ' -cook -allmaps -stage -pak'
if (-not $NoIoStore) { $argStr += ' -iostore' }
$argStr += ' -archive -archivedirectory="' + $Archive + '"'
$code = Invoke-Logged -FilePath $runUat -ArgumentString $argStr -LogPath $log -WorkingDirectory $script:ProjectDir

$exe = Join-Path (Join-Path $Archive 'Windows') ($script:ProjectName + '.exe')
$present = Test-Path -LiteralPath $exe
Write-Note ('UAT exit code: ' + $code + '; executable present: ' + $present)
# What the game reads from its own folder at run time (FPaths::ProjectDir() is <archive>\Windows\WalkTheArchive):
# the UI's fonts, and whisper for the Lost Stories booth when Tools\win\get_whisper.ps1 has set it up.
if ($present) {
    $gameDir = Join-Path (Join-Path $Archive 'Windows') $script:ProjectName
    foreach ($sub in @('Fonts', 'ThirdParty\whisper')) {
        $src = Join-Path $script:ProjectDir $sub
        if (Test-Path -LiteralPath $src) {
            $dst = Join-Path $gameDir $sub
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force
            Write-Note ('copied ' + $sub + ' next to the game')
        } elseif ($sub -like 'ThirdParty*') {
            Write-Note 'no ThirdParty\whisper: stories told in this build are kept but not written down (Tools\win\get_whisper.ps1)'
        }
    }
}
if ($present) { Write-Note ('run: "' + $exe + '"') }
Write-ResultLine 'package_game' (($code -eq 0) -and $present) @{ platform = 'Win64'; config = $Config; exit_code = $code; archive = $Archive; exe = $exe; log = $log }
if ($code -ne 0) { exit $code }
if (-not $present) { exit 1 }
exit 0

<#
.SYNOPSIS
  Install the Windows prerequisites for Walk the Archive with winget, then list the manual steps.
.DESCRIPTION
  Installs (only what is missing): Git, the Epic Games Launcher, Visual Studio Community with the
  Unreal components from Tools/ue.vsconfig (VS 2026 by default, -VS2022 for the 2022 release),
  and Blender. Unreal Engine 5.8 itself can only be installed from the Launcher after signing in,
  so that step is printed at the end. Installers that need admin rights raise a UAC prompt; no
  other step needs admin.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\install_prereqs.ps1
  powershell -ExecutionPolicy Bypass -File Tools\win\install_prereqs.ps1 -Only git,blender -DryRun
#>
param(
    [string[]]$Only,      # subset of: git, launcher, vs, blender
    [string[]]$Skip,      # items to leave alone
    [switch]$VS2022,      # install Visual Studio 2022 Community instead of 2026
    [switch]$DryRun       # print the commands without running them
)
. (Join-Path $PSScriptRoot '_common.ps1')

$items = @('git', 'launcher', 'vs', 'blender')
# -Only git,vs arrives as one string under powershell -File; accept both forms.
if ($Only) { $Only = @($Only | ForEach-Object { "$_" -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
if ($Skip) { $Skip = @($Skip | ForEach-Object { "$_" -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
if ($Only) { $items = @($items | Where-Object { $Only -contains $_ }) }
if ($Skip) { $items = @($items | Where-Object { $Skip -notcontains $_ }) }

$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($null -eq $winget -and -not $DryRun) {
    Write-Fail 'winget is not available. Install "App Installer" from the Microsoft Store (https://aka.ms/getwinget), then rerun.'
    exit 1
}
if (-not (Test-IsAdmin)) { Write-Note 'Not elevated: Visual Studio and the Launcher will show UAC prompts; approve them.' }

$log = Join-Path (Initialize-CacheDir) 'install_prereqs.log'
$results = [ordered]@{}
$rebootNeeded = $false

function Invoke-Winget([string]$Name, [string]$ArgumentString) {
    if ($DryRun) { Write-Note ("[dry run] winget " + $ArgumentString); return 0 }
    $code = Invoke-Logged -FilePath $winget.Source -ArgumentString $ArgumentString -LogPath $log
    if ($code -eq 3010 -or $code -eq 1641) { $script:rebootNeeded = $true; Write-Warn ($Name + ': installed, reboot required (exit ' + $code + ')'); return 0 }
    if ($code -eq -1978335189 -or $code -eq 0x8A150061) { Write-Note ($Name + ': already installed per winget'); return 0 }
    if ($code -ne 0) { Write-Fail ($Name + ': winget exit code ' + $code + ' (see ' + $log + ')') }
    return $code
}

foreach ($item in $items) {
    switch ($item) {
        'git' {
            Write-Step 'Git'
            $v = Get-GitVersion
            if ($v) { Write-Note ('present: ' + $v); $results.git = 'present'; break }
            $results.git = (Invoke-Winget 'Git' 'install --id Git.Git -e --accept-package-agreements --accept-source-agreements')
        }
        'launcher' {
            Write-Step 'Epic Games Launcher'
            $p = Get-EpicLauncherPath
            if ($p) { Write-Note ('present: ' + $p); $results.launcher = 'present'; break }
            $results.launcher = (Invoke-Winget 'Epic Games Launcher' 'install --id EpicGames.EpicGamesLauncher -e --accept-package-agreements --accept-source-agreements')
        }
        'vs' {
            Write-Step 'Visual Studio Community (C++ game development, Unreal components)'
            $cfg = $script:VsConfig
            if ($VS2022) { $cfg = $script:VsConfig2022 }
            if (-not (Test-FileExists $cfg)) { Write-Fail ('missing ' + $cfg); $results.vs = 2; break }
            # The VS bootstrapper gets the --config path on its own command line; a copy at a
            # path without spaces avoids every quoting question.
            if ($cfg -match '\s') {
                $alt = Join-Path $env:ProgramData 'WalkTheArchive\ue.vsconfig'
                try {
                    New-Item -ItemType Directory -Path (Split-Path -Parent $alt) -Force | Out-Null
                    Copy-Item -LiteralPath $cfg -Destination $alt -Force
                    $cfg = $alt
                } catch { Write-Warn ('could not copy the vsconfig to ' + $alt + '; using the quoted repo path') }
            }
            $vs = Get-VsInstall
            if ($vs -and $vs.HasGameWorkload) { Write-Note ('present with the Game workload: ' + $vs.Version + ' at ' + $vs.Path); $results.vs = 'present'; break }
            if ($vs -and -not $vs.HasGameWorkload) {
                Write-Note ('Visual Studio ' + $vs.Version + ' is installed without the C++ game workload; adding the components.')
                $setup = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\setup.exe'
                $argStr = 'modify --installPath "' + $vs.Path + '" --config "' + $cfg + '" --passive --norestart'
                if ($DryRun) { Write-Note ('[dry run] "' + $setup + '" ' + $argStr); $results.vs = 0; break }
                $code = Invoke-Logged -FilePath $setup -ArgumentString $argStr -LogPath $log
                if ($code -eq 3010 -or $code -eq 1641) { $rebootNeeded = $true; $code = 0 }
                if ($code -eq 740) { Write-Fail 'the VS installer needs elevation (exit 740); rerun from an elevated prompt.' }
                $results.vs = $code
                break
            }
            $id = 'Microsoft.VisualStudio.Community'
            if ($VS2022) { $id = 'Microsoft.VisualStudio.2022.Community' }
            $override = '--passive --norestart --config \"' + $cfg + '\"'
            $results.vs = (Invoke-Winget 'Visual Studio' ('install --id ' + $id + ' -e --accept-package-agreements --accept-source-agreements --override "' + $override + '"'))
        }
        'blender' {
            Write-Step 'Blender'
            $b = Get-BlenderPath
            if ($b) { Write-Note ('present: ' + $b); $results.blender = 'present'; break }
            $results.blender = (Invoke-Winget 'Blender' 'install --id BlenderFoundation.Blender -e --accept-package-agreements --accept-source-agreements')
        }
    }
}

Write-Step 'Manual steps that remain'
Write-Note '1. Open the Epic Games Launcher and sign in (Epic account + two-factor code).'
Write-Note '2. Unreal Engine > Library > "+" > choose 5.8.x > Install (default folder C:\Program Files\Epic Games\UE_5.8).'
Write-Note '   In Options you can untick target platforms you do not need; keep "Editor symbols for debugging" off unless debugging.'
Write-Note '3. Start the engine once from the Launcher so it registers; then run Tools\win\build_editor.ps1.'
if ($rebootNeeded) { Write-Warn 'An installer asked for a reboot. Reboot before building.' }

$failed = @($results.Keys | Where-Object { $results[$_] -is [int] -and $results[$_] -ne 0 })
Write-ResultLine 'install_prereqs' ($failed.Count -eq 0) @{ results = $results; reboot_needed = $rebootNeeded; log = $log }
if ($failed.Count -gt 0) { exit 1 }
exit 0

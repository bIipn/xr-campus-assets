<#
.SYNOPSIS
  Puts whisper.cpp's whisper-cli and a speech model where the Lost Stories booth looks for them, so the stories
  visitors tell are written down: unreal\WalkTheArchive\ThirdParty\whisper (UWTAStoriesSubsystem::FindWhisper).
.DESCRIPTION
  -From <folder>  copies from a folder that already has them: whisper-cli.exe with the DLLs beside it (found anywhere
                  under the folder) and a ggml-*.bin model (ggml-base.bin preferred). Nothing is downloaded.
  -Download       downloads them first (ask the owner of the machine before running this; about 200 MB):
                    whisper-bin-x64.zip (the Windows x64 build of whisper.cpp, MIT) from the whisper.cpp releases
                      https://github.com/ggml-org/whisper.cpp/releases (-Version picks the release, default v1.9.2)
                    ggml-base.bin (the multilingual base model, 148 MB, MIT) from
                      https://huggingface.co/ggerganov/whisper.cpp
                  into Tools\.cache\whisper, then copies as -From does.
  The target folder is not in git (.gitignore: unreal/WalkTheArchive/ThirdParty/). package_game.ps1 copies it next
  to the packaged game. Another folder can be used instead: the project setting Walk the Archive > Lost Stories >
  Whisper Folder, or the WTA_WHISPER environment variable.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\get_whisper.ps1 -From C:\dev\wta_tools\whisper
  powershell -ExecutionPolicy Bypass -File Tools\win\get_whisper.ps1 -Download
#>
param(
    [string]$From = '',
    [switch]$Download,
    [string]$Version = 'v1.9.2',
    [string]$Model = 'base'
)
. (Join-Path $PSScriptRoot '_common.ps1')

$target = Join-Path (Join-Path $script:ProjectDir 'ThirdParty') 'whisper'
Write-Step ('whisper for the Lost Stories booth -> ' + $target)

if ($Download) {
    $cache = Join-Path (Initialize-CacheDir) 'whisper'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    $zip = Join-Path $cache 'whisper-bin-x64.zip'
    $bin = Join-Path $cache ('ggml-' + $Model + '.bin')
    $ProgressPreference = 'SilentlyContinue'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    if (-not (Test-Path -LiteralPath $zip)) {
        $url = 'https://github.com/ggml-org/whisper.cpp/releases/download/' + $Version + '/whisper-bin-x64.zip'
        Write-Note ('downloading ' + $url)
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    }
    if (-not (Test-Path -LiteralPath $bin)) {
        $url = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-' + $Model + '.bin'
        Write-Note ('downloading ' + $url)
        Invoke-WebRequest -Uri $url -OutFile $bin -UseBasicParsing
    }
    $unz = Join-Path $cache 'bin'
    if (-not (Test-Path -LiteralPath $unz)) { Expand-Archive -LiteralPath $zip -DestinationPath $unz -Force }
    $From = $cache
}
if (-not $From) { Write-Fail 'say where they are (-From <folder>) or -Download'; exit 1 }
if (-not (Test-Path -LiteralPath $From)) { Write-Fail ('no folder ' + $From); exit 1 }

$exe = Get-ChildItem -LiteralPath $From -Recurse -Filter 'whisper-cli.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) { Write-Fail ('no whisper-cli.exe under ' + $From); exit 1 }
$models = @(Get-ChildItem -LiteralPath $From -Recurse -Filter 'ggml-*.bin' -ErrorAction SilentlyContinue)
$pick = $models | Where-Object { $_.Name -eq ('ggml-' + $Model + '.bin') } | Select-Object -First 1
if (-not $pick) { $pick = $models | Sort-Object Length | Select-Object -First 1 }
if (-not $pick) { Write-Fail ('no ggml-*.bin model under ' + $From); exit 1 }

New-Item -ItemType Directory -Path $target -Force | Out-Null
# whisper-cli and the DLLs it loads from its own folder (ggml, whisper, the CPU back ends, the C runtime it ships)
$files = @(Get-ChildItem -LiteralPath $exe.DirectoryName -File | Where-Object { $_.Name -eq 'whisper-cli.exe' -or $_.Extension -eq '.dll' })
foreach ($f in $files) { Copy-Item -LiteralPath $f.FullName -Destination $target -Force }
Copy-Item -LiteralPath $pick.FullName -Destination $target -Force
Write-Note ('copied whisper-cli.exe, ' + ($files.Count - 1) + ' DLLs and ' + $pick.Name)

# Prove it runs: its help text, no audio needed. whisper-cli prints it on stderr, which Windows PowerShell turns into
# error records (and, with 'Stop', a terminating error), so they are read as plain text here.
$cli = Join-Path $target 'whisper-cli.exe'
$prev = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$out = (& $cli --help 2>&1 | ForEach-Object { [string]$_ }) -join "`n"
$ErrorActionPreference = $prev
$ok = $out -match 'usage'
if ($ok) { Write-Note 'whisper-cli runs' } else { Write-Warn ('whisper-cli did not answer --help: ' + $out.Substring(0, [Math]::Min(300, $out.Length))) }
Write-ResultLine 'get_whisper' $ok @{ folder = $target; model = $pick.Name; dlls = ($files.Count - 1) }
if (-not $ok) { exit 1 }
exit 0

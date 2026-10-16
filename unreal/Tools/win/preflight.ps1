<#
.SYNOPSIS
  Check this Windows PC for Walk the Archive (Unreal Engine 5.8) and print a verdict.
.DESCRIPTION
  Collects OS, CPU, RAM, GPU name + VRAM, free disk on the repo drive, and whether UE 5.8,
  Visual Studio (via vswhere), git, Blender and the Epic Games Launcher are installed.
  Verdict: FULL (RTX / RX 6000+ class with 8 GB+ VRAM: HWRT Lumen + MegaLights),
  STANDARD (software Lumen) or NOT_SUPPORTED. Writes Tools/.cache/preflight.json.
  Exit code 0 for FULL/STANDARD, 2 for NOT_SUPPORTED, 1 on a script error.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Tools\win\preflight.ps1
#>
param(
    [switch]$Json,       # print the JSON report to the console as well
    [switch]$NoDxDiag    # never fall back to dxdiag (it takes 10-30 s)
)
. (Join-Path $PSScriptRoot '_common.ps1')

function Get-GpuList {
    # Name, VRAM in GB and driver per adapter. Win32_VideoController.AdapterRAM is a 32-bit
    # value (caps at 4 GB), so the registry QWORD HardwareInformation.qwMemorySize is read
    # first, then nvidia-smi, then dxdiag as a last resort.
    $regVram = @{}
    $classKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
    try {
        foreach ($sub in (Get-ChildItem -LiteralPath $classKey -ErrorAction SilentlyContinue)) {
            if ($sub.PSChildName -notmatch '^\d{4}$') { continue }
            $p = Get-ItemProperty -LiteralPath $sub.PSPath -ErrorAction SilentlyContinue
            $desc = Get-Prop $p 'DriverDesc' ''
            $qw = Get-Prop $p 'HardwareInformation.qwMemorySize' $null
            if ($desc -and $null -ne $qw -and [int64]$qw -gt 0) { $regVram[$desc] = [int64]$qw }
        }
    } catch { }

    $smi = @{}
    $smiCmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($smiCmd) {
        try {
            foreach ($line in (& nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null)) {
                $parts = "$line".Split(',')
                if ($parts.Count -ge 2) { $smi["$($parts[0])".Trim()] = [double]("$($parts[1])".Trim()) / 1024.0 }
            }
        } catch { }
    }

    $gpus = @()
    foreach ($c in (Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue)) {
        $name = "$(Get-Prop $c 'Name' 'Unknown GPU')"
        $vramGB = $null; $source = 'none'
        if ($regVram.ContainsKey($name)) { $vramGB = [math]::Round($regVram[$name] / 1GB, 1); $source = 'registry' }
        elseif ($smi.ContainsKey($name)) { $vramGB = [math]::Round($smi[$name], 1); $source = 'nvidia-smi' }
        else {
            $ar = Get-Prop $c 'AdapterRAM' 0
            if ($ar -and [int64]$ar -gt 0) { $vramGB = [math]::Round([int64]$ar / 1GB, 1); $source = 'AdapterRAM (32-bit, may cap at 4 GB)' }
        }
        $gpus += [ordered]@{ name = $name; vram_gb = $vramGB; vram_source = $source; driver = "$(Get-Prop $c 'DriverVersion' '')" }
    }

    $needDx = (@($gpus | Where-Object { $null -eq $_.vram_gb }).Count -gt 0) -or ($gpus.Count -eq 0)
    if ($needDx -and -not $NoDxDiag -and (Get-Command dxdiag -ErrorAction SilentlyContinue)) {
        Write-Note 'VRAM unknown; running dxdiag (10-30 s) ...'
        $xml = Join-Path (Initialize-CacheDir) 'dxdiag.xml'
        if (Test-Path -LiteralPath $xml) { Remove-Item -LiteralPath $xml -Force }
        try {
            Start-Process -FilePath 'dxdiag' -ArgumentList @('/x', ('"' + $xml + '"')) -Wait -WindowStyle Hidden
            if (Test-Path -LiteralPath $xml) {
                $doc = [xml](Get-Content -LiteralPath $xml -Raw)
                foreach ($d in $doc.DxDiag.DisplayDevices.DisplayDevice) {
                    $card = "$($d.CardName)".Trim()
                    $mem = "$($d.DedicatedMemory)" -replace '[^\d]', ''
                    $gb = $null
                    if ($mem) { $gb = [math]::Round([double]$mem / 1024.0, 1) }
                    $match = @($gpus | Where-Object { $_.name -eq $card -and $null -eq $_.vram_gb })
                    if ($match.Count -gt 0) { foreach ($m in $match) { $m.vram_gb = $gb; $m.vram_source = 'dxdiag' } }
                    elseif (@($gpus | Where-Object { $_.name -eq $card }).Count -eq 0) {
                        $gpus += [ordered]@{ name = $card; vram_gb = $gb; vram_source = 'dxdiag'; driver = "$($d.DriverVersion)" }
                    }
                }
            }
        } catch { Write-Warn ("dxdiag failed: " + $_.Exception.Message) }
    }
    return ,$gpus
}

function Get-GpuTier([string]$Name, $VramGB) {
    # 'rt' = hardware ray tracing class (NVIDIA RTX, AMD RX 6000/7000/9000, Radeon PRO W6000+),
    # 'dx12' = anything else discrete or integrated. Intel Arc is left at 'dx12' (unverified).
    $n = $Name
    $isRt = ($n -match '\bRTX\b') -or ($n -match '\bRX\s?[6-9]\d{3}\b') -or ($n -match 'Radeon PRO W[6-9]\d{3}')
    if ($isRt -and $null -ne $VramGB -and [double]$VramGB -ge 7.5) { return 'rt' }
    return 'dx12'
}

try {
    Write-Step 'Preflight: Windows'
    $os = Get-CimInstance Win32_OperatingSystem
    $cs = Get-CimInstance Win32_ComputerSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $osVersion = [version]"$(Get-Prop $os 'Version' '0.0.0')"
    $osBuild = [int]"$(Get-Prop $os 'BuildNumber' '0')"
    $ramGB = [math]::Round([double](Get-Prop $cs 'TotalPhysicalMemory' 0) / 1GB, 1)
    $gpus = Get-GpuList

    $driveLetter = $script:RepoRoot.Substring(0, 1)
    $freeGB = $null
    try { $freeGB = [math]::Round([double]((Get-PSDrive -Name $driveLetter).Free) / 1GB, 1) } catch { }

    $engine = Find-Engine
    $vs = Get-VsInstall
    $git = Get-GitVersion
    $blender = Get-BlenderPath
    $launcher = Get-EpicLauncherPath

    $reasons = @()
    $verdict = 'STANDARD'
    $bestTier = 'dx12'
    $bestGpu = $null
    foreach ($g in $gpus) {
        $tier = Get-GpuTier $g.name $g.vram_gb
        $g['tier'] = $tier
        if ($tier -eq 'rt') { $bestTier = 'rt'; $bestGpu = $g }
        elseif ($null -eq $bestGpu) { $bestGpu = $g }
    }
    if ($osVersion.Major -lt 10 -or $osBuild -lt 17763) {
        $verdict = 'NOT_SUPPORTED'; $reasons += 'Windows 10 1809 (build 17763) or newer is required (DX12 + DXR).'
    }
    if ($ramGB -lt 15.5) {
        $verdict = 'NOT_SUPPORTED'; $reasons += ("RAM is " + $ramGB + " GB; the editor with Lumen and Nanite needs 16 GB (32 GB recommended).")
    }
    if ($gpus.Count -eq 0) {
        $verdict = 'NOT_SUPPORTED'; $reasons += 'No display adapter was detected.'
    } elseif ($null -ne $bestGpu -and $null -ne $bestGpu.vram_gb -and [double]$bestGpu.vram_gb -lt 3.5) {
        $verdict = 'NOT_SUPPORTED'; $reasons += ("GPU " + $bestGpu.name + " has " + $bestGpu.vram_gb + " GB VRAM; 8 GB is Epic's floor, 4 GB the bare minimum to open the editor.")
    }
    if ($verdict -ne 'NOT_SUPPORTED') {
        if ($bestTier -eq 'rt') { $verdict = 'FULL'; $reasons += ("GPU " + $bestGpu.name + " (" + $bestGpu.vram_gb + " GB): hardware ray tracing class, Lumen HWRT + MegaLights.") }
        else {
            $desc = 'no GPU name'
            if ($null -ne $bestGpu) { $desc = $bestGpu.name + " (" + $bestGpu.vram_gb + " GB)" }
            $reasons += ("GPU " + $desc + ": software Lumen, no MegaLights; expect reduced fidelity. Need RTX or RX 6000+ with 8 GB+ for FULL.")
        }
        if ($ramGB -lt 31.5) { $reasons += ("RAM is " + $ramGB + " GB; 32 GB is recommended for shader compiles.") }
        if ($null -ne $freeGB -and $freeGB -lt 120) { $reasons += ("Only " + $freeGB + " GB free on " + $driveLetter + ": ; UE 5.8 (~50 GB), Visual Studio (~20 GB) and the shader cache need around 120 GB.") }
    }
    if ($script:RepoRoot -match '\s') { $reasons += 'The repo path contains spaces; every script quotes paths, but a path without spaces is safer for UAT cooks.' }

    $report = [ordered]@{
        step = 'preflight'
        platform = 'win'
        time = (Get-Date).ToString('s')
        os = [ordered]@{ caption = "$(Get-Prop $os 'Caption' '')"; version = "$osVersion"; build = $osBuild }
        cpu = [ordered]@{ name = "$(Get-Prop $cpu 'Name' '')".Trim(); cores = Get-Prop $cpu 'NumberOfCores' 0; threads = Get-Prop $cpu 'NumberOfLogicalProcessors' 0 }
        ram_gb = $ramGB
        gpus = $gpus
        disk = [ordered]@{ drive = ($driveLetter + ':'); free_gb = $freeGB }
        repo_root = $script:RepoRoot
        installed = [ordered]@{
            unreal = $(if ($engine) { [ordered]@{ root = (Get-Prop $engine 'root' ''); version = (Get-Prop $engine 'version' '') } } else { $null })
            epic_launcher = $launcher
            visual_studio = $(if ($vs) { [ordered]@{ path = $vs.Path; version = $vs.Version; game_workload = $vs.HasGameWorkload } } else { $null })
            git = $git
            blender = $blender
            system_python = $(if (Get-SystemPython) { ((Get-SystemPython) -join ' ') } else { $null })
        }
        verdict = $verdict
        reasons = $reasons
    }

    $cache = Initialize-CacheDir
    $jsonPath = Join-Path $cache 'preflight.json'
    ($report | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    Write-Note ("OS       : " + $report.os.caption + " (" + $osVersion + ", build " + $osBuild + ")")
    Write-Note ("CPU      : " + $report.cpu.name + " (" + $report.cpu.cores + " cores / " + $report.cpu.threads + " threads)")
    Write-Note ("RAM      : " + $ramGB + " GB")
    foreach ($g in $gpus) { Write-Note ("GPU      : " + $g.name + " - " + $g.vram_gb + " GB VRAM (" + $g.vram_source + "), driver " + $g.driver + ", tier " + $g.tier) }
    Write-Note ("Disk     : " + $freeGB + " GB free on " + $driveLetter + ":")
    Write-Note ("UE 5.8   : " + $(if ($engine) { (Get-Prop $engine 'version' '?') + " at " + (Get-Prop $engine 'root' '?') } else { 'not installed' }))
    Write-Note ("Launcher : " + $(if ($launcher) { $launcher } else { 'not installed' }))
    Write-Note ("VS       : " + $(if ($vs) { $vs.Version + " at " + $vs.Path + " (Game workload: " + $vs.HasGameWorkload + ")" } else { 'not installed' }))
    Write-Note ("git      : " + $(if ($git) { $git } else { 'not installed' }))
    Write-Note ("Blender  : " + $(if ($blender) { $blender } else { 'not installed' }))
    foreach ($r in $reasons) { Write-Note ("- " + $r) }
    Write-Note ("Report   : " + $jsonPath)
    if ($Json) { Write-Host ($report | ConvertTo-Json -Depth 8) }

    $color = 'Green'; if ($verdict -eq 'NOT_SUPPORTED') { $color = 'Red' } elseif ($verdict -eq 'STANDARD') { $color = 'Yellow' }
    Write-Host ("PREFLIGHT_VERDICT " + $verdict) -ForegroundColor $color
    Write-ResultLine 'preflight' ($verdict -ne 'NOT_SUPPORTED') @{ verdict = $verdict; report = $jsonPath }
    if ($verdict -eq 'NOT_SUPPORTED') { exit 2 }
    exit 0
} catch {
    Write-Fail ("preflight failed: " + $_.Exception.Message)
    Write-Host $_.ScriptStackTrace
    Write-ResultLine 'preflight' $false @{ error = $_.Exception.Message }
    exit 1
}

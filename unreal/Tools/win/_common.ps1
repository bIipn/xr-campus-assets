# _common.ps1 - shared helpers for the Walk the Archive Windows tools. Dot-source it:
#   . (Join-Path $PSScriptRoot '_common.ps1')
# Works in Windows PowerShell 5.1 and PowerShell 7. Every path is quoted when it reaches a
# native program, so folders like "C:\Program Files\Epic Games" are safe.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# ---- repo layout (Tools/win -> Tools -> unreal -> repo root) ----
$script:ToolsDir   = Split-Path -Parent $PSScriptRoot
$script:UnrealDir  = Split-Path -Parent $script:ToolsDir
$script:RepoRoot   = Split-Path -Parent $script:UnrealDir
$script:CommonDir  = Join-Path $script:ToolsDir 'common'
$script:CacheDir   = Join-Path $script:ToolsDir '.cache'
$script:ProjectDir = Join-Path $script:UnrealDir 'WalkTheArchive'
$script:UProject   = Join-Path $script:ProjectDir 'WalkTheArchive.uproject'
$script:ProjectName = 'WalkTheArchive'
$script:SetupScript = Join-Path (Join-Path $script:ProjectDir 'Scripts') 'setup_project.py'
$script:VsConfig   = Join-Path $script:ToolsDir 'ue.vsconfig'
$script:VsConfig2022 = Join-Path $script:ToolsDir 'ue-vs2022.vsconfig'
$script:EngineVersion = '5.8'

function Test-IsWindowsHost {
    # PowerShell 5.1 has no $IsWindows; it only runs on Windows.
    if (Test-Path variable:IsWindows) { return [bool](Get-Variable -Name IsWindows -ValueOnly) }
    return $true
}

function Write-Step([string]$Text) { Write-Host ("==> " + $Text) -ForegroundColor Cyan }
function Write-Note([string]$Text) { Write-Host ("    " + $Text) }
function Write-Warn([string]$Text) { Write-Host ("WARNING: " + $Text) -ForegroundColor Yellow }
function Write-Fail([string]$Text) { Write-Host ("ERROR: " + $Text) -ForegroundColor Red }

function Join-EnvPath([string]$Base, [string]$Relative) {
    # Join-Path throws on a null base; some environment variables are empty on odd hosts.
    if ([string]::IsNullOrWhiteSpace($Base)) { return $null }
    return (Join-Path $Base $Relative)
}

function Test-FileExists($Path) {
    # Test-Path throws on an empty string; this returns $false instead.
    if ($null -eq $Path -or [string]::IsNullOrWhiteSpace("$Path")) { return $false }
    return (Test-Path -LiteralPath "$Path")
}

function Get-Prop($Object, [string]$Name, $Default = $null) {
    # Safe property read for ConvertFrom-Json objects under strict mode.
    if ($null -eq $Object) { return $Default }
    $p = $Object.PSObject.Properties[$Name]
    if ($null -eq $p) { return $Default }
    return $p.Value
}

function Initialize-CacheDir {
    if (-not (Test-Path -LiteralPath $script:CacheDir)) { New-Item -ItemType Directory -Path $script:CacheDir | Out-Null }
    return $script:CacheDir
}

function Write-ResultLine([string]$Step, [bool]$Ok, [hashtable]$Extra) {
    # One machine-checkable line in the same shape as the editor setup steps (check_results.py reads it).
    $obj = [ordered]@{ step = $Step; ok = $Ok }
    if ($Extra) { foreach ($k in $Extra.Keys) { $obj[$k] = $Extra[$k] } }
    Write-Host ("WTA_RESULT " + ($obj | ConvertTo-Json -Compress -Depth 6))
}

function Test-IsAdmin {
    try {
        $id = [Security.Principal.WindowsIdentity]::GetCurrent()
        return (New-Object Security.Principal.WindowsPrincipal $id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch { return $false }
}

# ---- Python (any Python 3 for find_engine.py, then the engine's bundled one) ----
function Get-SystemPython {
    # Returns an array (exe plus fixed args) for a working Python 3, or $null.
    # The Microsoft Store alias "python.exe" prints an install hint and exits non-zero, so every
    # candidate is executed once to prove it is a real interpreter.
    $candidates = @(@('py', '-3'), @('python3'), @('python'))
    foreach ($cand in $candidates) {
        $cmd = Get-Command $cand[0] -ErrorAction SilentlyContinue
        if ($null -eq $cmd) { continue }
        try {
            $out = Invoke-Python $cand @('-c', 'import sys; print(sys.version_info[0])') 2>$null
            if ($LASTEXITCODE -eq 0 -and ("$out".Trim() -eq '3')) { return ,@($cand) }
        } catch { }
    }
    return $null
}

function Invoke-Python([string[]]$Python, [string[]]$Arguments) {
    # Runs a Python command built from Get-SystemPython / engine python and returns stdout lines.
    $exe = $Python[0]
    $fixed = @()
    if ($Python.Length -gt 1) { $fixed = $Python[1..($Python.Length - 1)] }
    $all = @($fixed + $Arguments)
    return (& $exe @all)
}

# ---- engine discovery ----
function Get-EnginePathsFromRoot([string]$Root) {
    $eng = Join-Path $Root 'Engine'
    $obj = [ordered]@{
        root = $Root
        version = 'unknown'
        found_via = 'powershell'
        python = Join-Path $eng 'Binaries\ThirdParty\Python3\Win64\python.exe'
        editor = Join-Path $eng 'Binaries\Win64\UnrealEditor.exe'
        editor_cmd = Join-Path $eng 'Binaries\Win64\UnrealEditor-Cmd.exe'
        build = Join-Path $eng 'Build\BatchFiles\Build.bat'
        run_uat = Join-Path $eng 'Build\BatchFiles\RunUAT.bat'
        run_ubt = Join-Path $eng 'Build\BatchFiles\RunUBT.bat'
        ubt = Join-Path $eng 'Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe'
        version_selector = Join-Path $eng 'Binaries\Win64\UnrealVersionSelector.exe'
    }
    $bv = Join-Path $eng 'Build\Build.version'
    if (Test-FileExists $bv) {
        try {
            $v = Get-Content -LiteralPath $bv -Raw | ConvertFrom-Json
            $obj.version = ('{0}.{1}.{2}' -f (Get-Prop $v 'MajorVersion' 0), (Get-Prop $v 'MinorVersion' 0), (Get-Prop $v 'PatchVersion' 0))
        } catch { }
    }
    return [pscustomobject]$obj
}

function Test-EngineRoot([string]$Root) {
    if ([string]::IsNullOrWhiteSpace($Root)) { return $false }
    return (Test-Path -LiteralPath (Join-Path $Root 'Engine\Binaries')) -and (Test-Path -LiteralPath (Join-Path $Root 'Engine\Build'))
}

function Find-EngineFallback {
    # Pure PowerShell copy of find_engine.py's search, for machines without any Python yet.
    $wanted = $script:EngineVersion
    if ($env:UE_ROOT -and (Test-EngineRoot $env:UE_ROOT)) {
        $e = Get-EnginePathsFromRoot $env:UE_ROOT; $e.found_via = 'UE_ROOT'; return $e
    }
    $dat = Join-EnvPath $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'
    if (Test-FileExists $dat) {
        try {
            $list = Get-Prop (Get-Content -LiteralPath $dat -Raw | ConvertFrom-Json) 'InstallationList' @()
            foreach ($entry in $list) {
                if ((Get-Prop $entry 'AppName' '') -eq ('UE_' + $wanted)) {
                    $loc = Get-Prop $entry 'InstallLocation' ''
                    if (Test-EngineRoot $loc) { $e = Get-EnginePathsFromRoot $loc; $e.found_via = 'LauncherInstalled.dat'; return $e }
                }
            }
        } catch { }
    }
    $default = Join-EnvPath $env:ProgramFiles ('Epic Games\UE_' + $wanted)
    if (Test-EngineRoot $default) { $e = Get-EnginePathsFromRoot $default; $e.found_via = 'default path'; return $e }
    try {
        $reg = Get-ItemProperty -LiteralPath ('HKLM:\SOFTWARE\EpicGames\Unreal Engine\' + $wanted) -ErrorAction Stop
        $loc = Get-Prop $reg 'InstalledDirectory' ''
        if (Test-EngineRoot $loc) { $e = Get-EnginePathsFromRoot $loc; $e.found_via = 'registry'; return $e }
    } catch { }
    return $null
}

function Find-Engine {
    # Prefers common/find_engine.py (the single source of truth); falls back to PowerShell.
    $py = Get-SystemPython
    $script = Join-Path $script:CommonDir 'find_engine.py'
    if ($null -ne $py -and (Test-FileExists $script)) {
        try {
            $out = Invoke-Python $py @($script, '--json') 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { return ((($out) -join "`n") | ConvertFrom-Json) }
        } catch { }
    }
    return (Find-EngineFallback)
}

function Get-EnginePython($Engine) {
    # The engine's bundled Python when it exists, else the system one (as an exe+args array).
    if ($null -ne $Engine) {
        $p = Get-Prop $Engine 'python' ''
        if (Test-FileExists $p) { return ,@("$p") }
    }
    $sys = Get-SystemPython
    if ($null -eq $sys) { return $null }
    return ,@($sys)
}

function Get-RequiredEngine {
    $engine = Find-Engine
    if ($null -eq $engine) {
        Write-Fail ("Unreal Engine " + $script:EngineVersion + " was not found. Install it from the Epic Games Launcher " +
                    "(Unreal Engine > Library > + > " + $script:EngineVersion + ".x > Install) or set UE_ROOT to the engine folder.")
        exit 1
    }
    Write-Note ("Engine " + (Get-Prop $engine 'version' '?') + " at " + (Get-Prop $engine 'root' '?') + " (via " + (Get-Prop $engine 'found_via' '?') + ")")
    return $engine
}

# ---- running native programs with a tee'd log ----
function Invoke-Logged {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,      # .exe or .bat
        [string]$ArgumentString = '',                          # raw, already quoted
        [string]$LogPath,                                      # appended to; omit for console only
        [hashtable]$Environment,
        [string]$WorkingDirectory
    )
    # The raw command line is built here and handed to cmd.exe verbatim, so PowerShell's own
    # argument re-quoting (which differs between 5.1 and 7) never touches the quotes.
    # cmd /s /c strips the outer quotes and runs the rest literally; 2>&1 merges stderr.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    if (Test-IsWindowsHost) {
        $psi.FileName = $env:ComSpec
        $psi.Arguments = '/d /s /c ""' + $FilePath + '" ' + $ArgumentString + ' 2>&1"'
    } else {
        # Only reached when these helpers are smoke-tested with PowerShell 7 on Linux or macOS.
        $psi.FileName = '/bin/sh'
        $psi.Arguments = '-c "' + (('"' + $FilePath + '" ' + $ArgumentString + ' 2>&1') -replace '"', '\"') + '"'
    }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $false
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
    if ($Environment) { foreach ($k in $Environment.Keys) { $psi.EnvironmentVariables[$k] = [string]$Environment[$k] } }
    Write-Host ("    > " + $FilePath + " " + $ArgumentString) -ForegroundColor DarkGray
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $writer = $null
    if ($LogPath) {
        $writer = New-Object System.IO.StreamWriter($LogPath, $true, (New-Object System.Text.UTF8Encoding $false))
        $writer.WriteLine("> " + $FilePath + " " + $ArgumentString)
    }
    try {
        $null = $proc.Start()
        while (-not $proc.StandardOutput.EndOfStream) {
            $line = $proc.StandardOutput.ReadLine()
            Write-Host $line
            if ($writer) { $writer.WriteLine($line) }
        }
        $proc.WaitForExit()
    } finally {
        if ($writer) { $writer.Dispose() }
    }
    return [int]$proc.ExitCode
}

# ---- state checks ----
function Test-EditorOpenOnProject {
    # The open editor holds a write lock on loaded assets; headless jobs must not run beside it.
    if (-not (Test-IsWindowsHost)) { return $false }
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'" -ErrorAction SilentlyContinue
        foreach ($p in $procs) {
            $cl = Get-Prop $p 'CommandLine' ''
            if ($cl -and $cl -like ('*' + $script:ProjectName + '.uproject*')) { return $true }
        }
    } catch { }
    return $false
}

function Get-VsWhere {
    $p = Join-EnvPath ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-FileExists $p) { return $p }
    return $null
}

function Get-VsInstall {
    # Returns @{ Path; Version; HasGameWorkload } for the newest VS, or $null when none is installed.
    $vswhere = Get-VsWhere
    if ($null -eq $vswhere) { return $null }
    $anyPath = (& $vswhere -latest -products * -property installationPath 2>$null | Select-Object -First 1)
    if (-not $anyPath) { return $null }
    $anyVer = (& $vswhere -latest -products * -property catalog_productDisplayVersion 2>$null | Select-Object -First 1)
    $gamePath = (& $vswhere -latest -products * -requires Microsoft.VisualStudio.Workload.NativeGame -property installationPath 2>$null | Select-Object -First 1)
    return @{ Path = "$anyPath"; Version = "$anyVer"; HasGameWorkload = [bool]$gamePath }
}

function Get-EpicLauncherPath {
    $p = Join-EnvPath ${env:ProgramFiles(x86)} 'Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe'
    if (Test-FileExists $p) { return $p }
    return $null
}

function Get-BlenderPath {
    $cmd = Get-Command blender -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $dir = Join-EnvPath $env:ProgramFiles 'Blender Foundation'
    if (-not (Test-FileExists $dir)) { return $null }
    $hits = @(Get-ChildItem -Path $dir -Filter 'blender.exe' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
    if ($hits.Count -gt 0) { return $hits[0].FullName }
    return $null
}

function Get-GitVersion {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { return $null }
    try { return ("$(& git --version 2>$null)").Trim() } catch { return 'git (version unknown)' }
}

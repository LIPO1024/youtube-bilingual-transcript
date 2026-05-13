# pipeline.ps1
#
# YouTube 双语字幕整理一键流水线
#
# 用法:
#   pwsh pipeline.ps1 -Stage prep   -Config video_config.json
#   pwsh pipeline.ps1 -Stage final  -Config video_config.json
#   pwsh pipeline.ps1 -Stage all    -Config video_config.json   # 自动判断
#
# 阶段:
#   prep  : Stage 0 (fetch_and_split) -> Stage 2 buffer -> Stage 2.1 split_long
#           输出 sentences_final.json
#   final : Stage 7 generate_final -> 复制到 Clippings/
#           需要 translations.json 已就位
#   all   : prep -> 检查 translations.json -> 若就位则 final，否则提示
#
# 翻译步骤(在 prep 与 final 之间)由主 agent 在 Claude Code 内并行 subagent 完成,
# 不在本脚本内执行。详见 skill.md Stage 5。

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("prep", "final", "all")]
    [string]$Stage = "all",

    [Parameter(Mandatory = $false)]
    [string]$Config = "video_config.json",

    [switch]$NoCopy
)

$ErrorActionPreference = "Stop"

# Resolve script directory and switch in
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Write-Host ">> 工作目录: $ScriptDir" -ForegroundColor Cyan

if (-not (Test-Path $Config)) {
    throw "Config not found: $Config"
}

$cfg = Get-Content $Config -Raw -Encoding UTF8 | ConvertFrom-Json
$VideoId = $cfg.video_id
$OutputName = $cfg.output_name
if (-not $VideoId) { throw "Config missing video_id" }
if (-not $OutputName) { throw "Config missing output_name" }

Write-Host ">> 视频 ID: $VideoId" -ForegroundColor Cyan
Write-Host ">> 输出文件: Clippings/$OutputName" -ForegroundColor Cyan

function Invoke-Step {
    param([string]$Label, [scriptblock]$Block)
    Write-Host ""
    Write-Host "==[ $Label ]==" -ForegroundColor Yellow
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $Block
    $sw.Stop()
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "$Label 失败 (exit $LASTEXITCODE)"
    }
    Write-Host "[$Label] 完成 ($([int]$sw.Elapsed.TotalSeconds)s)" -ForegroundColor Green
}

function Test-Translations {
    if (-not (Test-Path "translations.json")) { return $false }
    if (-not (Test-Path "sentences_final.json")) { return $false }
    $t = Get-Content "translations.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $s = Get-Content "sentences_final.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($t.Count -ne $s.Count) {
        Write-Host "translations.json count = $($t.Count); sentences_final.json count = $($s.Count). 不匹配!" -ForegroundColor Red
        return $false
    }
    # ASCII-quote sanity check (Stage 5 §5.1 要求)
    $rawT = Get-Content "translations.json" -Raw -Encoding UTF8
    $bad = ($rawT.ToCharArray() | Where-Object { $_ -eq '"' }).Count
    $expected = $t.Count * 2 + 2  # 每条字符串 2 个外引号 + 数组开头与结尾
    if ($bad -gt $expected) {
        Write-Host "WARN: translations.json 内层疑似含 ASCII 双引号 (bare-count=$bad expected≈$expected). 请确认翻译输出符合 Stage 5 §5.1。" -ForegroundColor Yellow
    }
    return $true
}

function Invoke-Prep {
    Invoke-Step "Stage 0: 抓取并切句" {
        python fetch_and_split.py $VideoId sentences.json
    }
    Invoke-Step "Stage 2: 句末 buffer" {
        python apply_buffer.py sentences.json sentences_buffered.json
    }
    Invoke-Step "Stage 2.1: 长句拆分" {
        python split_long.py sentences_buffered.json sentences_final.json
    }
    $s = Get-Content "sentences_final.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host ""
    Write-Host ">> 准备完成. 句子总数: $($s.Count)" -ForegroundColor Cyan
    Write-Host ">> 下一步: 主 agent 并行 subagent 翻译 -> translations.json" -ForegroundColor Cyan
    Write-Host ">> 翻译完成后, 运行: pwsh pipeline.ps1 -Stage final" -ForegroundColor Cyan
}

function Invoke-Final {
    if (-not (Test-Translations)) {
        throw "translations.json 不存在或与 sentences_final.json 数量不匹配, 无法进入 final 阶段"
    }
    Invoke-Step "Stage 7: 生成 markdown" {
        python generate_final.py sentences_final.json translations.json $Config out.md
    }
    if (-not $NoCopy) {
        $target = Join-Path -Path "..\..\..\Clippings" -ChildPath $OutputName
        Invoke-Step "复制到 Clippings" {
            Copy-Item -Path "out.md" -Destination $target -Force
            Write-Host "  -> $target"
        }
    }
    Write-Host ""
    Write-Host ">> 全流程完成." -ForegroundColor Green
}

switch ($Stage) {
    "prep"  { Invoke-Prep }
    "final" { Invoke-Final }
    "all" {
        Invoke-Prep
        if (Test-Translations) {
            Write-Host ""
            Write-Host ">> 检测到 translations.json 已就位且数量匹配, 直接进入 final 阶段." -ForegroundColor Cyan
            Invoke-Final
        }
        else {
            Write-Host ""
            Write-Host ">> translations.json 未就位或数量不匹配, 已停在 prep 阶段." -ForegroundColor Yellow
            Write-Host ">> 主 agent 须并行 subagent 完成翻译, 再运行 pipeline.ps1 -Stage final" -ForegroundColor Yellow
        }
    }
}

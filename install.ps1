# Install youtube-bilingual-transcript skill for Claude Code
# Usage: irm https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/LIPO1024/youtube-bilingual-transcript.git"
$SkillName = "youtube-bilingual-transcript"
$SkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$TargetDir = Join-Path $SkillsDir $SkillName

Write-Host "Installing youtube-bilingual-transcript skill for Claude Code..." -ForegroundColor Cyan

# Ensure skills directory exists
if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
    Write-Host "Created $SkillsDir" -ForegroundColor Green
}

# Remove existing skill if present
if (Test-Path $TargetDir) {
    Write-Host "Removing existing installation at $TargetDir ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $TargetDir
}

# Clone
git clone $RepoUrl $TargetDir
if ($LASTEXITCODE -ne 0) {
    throw "git clone failed"
}

Write-Host "" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Skill installed to: $TargetDir" -ForegroundColor Green
Write-Host "" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Open Claude Code in your Obsidian vault directory" -ForegroundColor White
Write-Host "  2. Type: /youtube-bilingual-transcript" -ForegroundColor White
Write-Host "  3. Or say: 处理这个YouTube转录稿，生成双语笔记" -ForegroundColor White

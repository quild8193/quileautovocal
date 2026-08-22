$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

python -m pip install --upgrade -r requirements.txt
$env:PYTHONPATH = $Root
python -m unittest discover -s tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Test thất bại; không tạo bộ cài." }

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
pyinstaller --noconfirm --clean --onedir --windowed --name QuiLe-Autovocal app.py

$iscc = @(
  "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { Write-Warning "Chưa tìm thấy Inno Setup. Đã tạo EXE folder tại dist\QuiLe-Autovocal; cài Inno Setup rồi chạy lại script để tạo Setup.exe."; exit 0 }
& $iscc "$Root\QuiLe-Autovocal.iss"
Write-Host "Đã tạo bộ cài one-click tại output\QuiLe-Autovocal-Setup.exe"

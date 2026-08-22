# Tự động build QuiLe-Autovocal.exe bằng GitHub Actions

## 1. Chuẩn bị repository

Đưa toàn bộ dự án QuiLe-Autovocal lên một repository GitHub, ví dụ `username/QuiLe-Autovocal`. Ở thư mục gốc repository cần có tối thiểu các tệp sau:

```text
app.py
 audio_engine.py
 key_detector.py
 requirements.txt
 QuiLe-Autovocal.iss
 build_windows.ps1
 build_windows_github.yml
 tests/test_audio.py
 USER_MANUAL_VI.md
 README.md
```

Tên thư mục workflow phải là `.github/workflows`. Thực hiện trên máy phát triển:

```powershell
New-Item -ItemType Directory -Force .github\workflows
Copy-Item build_windows_github.yml .github\workflows\build-windows.yml
```

Sau đó commit và push:

```powershell
git add .github/workflows/build-windows.yml
 git commit -m "ci: build QuiLe-Autovocal Windows installer"
git push origin main
```

Nếu repository dùng nhánh `master`, sửa danh sách branch trong file YAML từ `main` sang `master`. Workflow hiện được cấu hình chạy khi push vào `main` hoặc `master`, khi có pull request vào hai nhánh đó, và khi bấm chạy thủ công.

## 2. Workflow mẫu

Tệp `.github/workflows/build-windows.yml` dùng runner Windows, cài Python 3.11, cài dependencies, chạy regression test, tạo bundle bằng PyInstaller, cài Inno Setup và compile thành `output/QuiLe-Autovocal-Setup.exe`.

```yaml
name: Build QuiLe-Autovocal Windows Installer

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        shell: pwsh
        run: python -m pip install -r requirements.txt
      - name: Run tests
        shell: pwsh
        run: |
          $env:PYTHONPATH = "$PWD"
          python -m unittest discover -s tests -p "test_*.py" -v
      - name: Build application
        shell: pwsh
        run: pyinstaller --noconfirm --clean --onedir --windowed --name QuiLe-Autovocal app.py
      - name: Install Inno Setup
        shell: pwsh
        run: choco install innosetup -y --no-progress
      - name: Build installer
        shell: pwsh
        run: '& "$env:ProgramFiles(x86)\\Inno Setup 6\\ISCC.exe" QuiLe-Autovocal.iss'
      - uses: actions/upload-artifact@v4
        with:
          name: QuiLe-Autovocal-Windows-Installer
          path: output/QuiLe-Autovocal-Setup.exe
```

`actions/checkout`, `actions/setup-python` và `actions/upload-artifact` là các action chuẩn để checkout mã nguồn, cài Python và lưu file build; có thể xem tài liệu workflow/action chính thức của GitHub tại [1] [2].

## 3. Xem file EXE sau mỗi lần push

Mở repository trên GitHub, chọn tab **Actions**, chọn workflow **Build QuiLe-Autovocal Windows Installer**, rồi chọn lần chạy tương ứng với commit vừa push. Khi job có trạng thái xanh, kéo xuống phần **Artifacts** và tải `QuiLe-Autovocal-Windows-Installer.zip`. Giải nén ZIP sẽ có file:

```text
QuiLe-Autovocal-Setup.exe
```

Artifact là file build của từng lần chạy, thích hợp để kiểm thử nội bộ. Người dùng cuối không nên tải artifact pull request chưa được kiểm tra.

## 4. Cấu hình driver ASIO

Không đặt driver ASIO độc quyền của một hãng vào repository nếu chưa có quyền phân phối. Nếu nhà phát hành có bộ cài chính thức và được phép phân phối, đặt file vào:

```text
drivers/ASIO-Driver-Setup.exe
```

Workflow và Inno Setup sẽ đưa file này vào bước cài đặt tùy chọn. Nếu không có file, ứng dụng vẫn build bình thường và người dùng cài driver từ nhà sản xuất audio interface.

## 5. Tự động tạo GitHub Release khi tạo tag

Nếu muốn có file tải công khai thay vì chỉ có artifact, thêm trigger tag và bước release. Chỉ nên dùng sau khi đã kiểm tra installer trên máy Windows sạch:

```yaml
on:
  push:
    branches: [ "main", "master" ]
    tags: [ "v*.*.*" ]
```

Sau bước upload artifact, có thể thêm action tạo release tương thích với chính sách bảo mật của repository. Khi đó tạo phiên bản bằng:

```powershell
git tag v1.3.0
git push origin v1.3.0
```

Nên giới hạn quyền ghi release ở mức cần thiết và chỉ phát hành tag đã review.

## 6. Kiểm tra khi workflow thất bại

| Lỗi | Cách xử lý |
|---|---|
| `No module named ...` | Thêm package vào `requirements.txt`, không cài thủ công ngoài workflow |
| Không tìm thấy `QuiLe-Autovocal.iss` | Đảm bảo file nằm ở thư mục gốc repository và workflow chạy từ thư mục đó |
| Không tìm thấy `dist\\QuiLe-Autovocal` | Kiểm tra bước PyInstaller và xem log đầy đủ trước bước Inno Setup |
| Inno Setup không tạo output | Kiểm tra đường dẫn `output/` và cú pháp `.iss`; giữ bước cài Inno Setup trước bước compile |
| Test thất bại | Sửa code/test trước; workflow cố ý không tạo installer khi regression test không đạt |
| Artifact không xuất hiện | Kiểm tra job đã chạy đến bước `upload-artifact` và path có đúng `output/QuiLe-Autovocal-Setup.exe` |
| File EXE bị Windows cảnh báo | Dùng mã ký số Code Signing khi phát hành thật; artifact chưa ký có thể bị SmartScreen cảnh báo |

## 7. Khuyến nghị vận hành

Nên giữ workflow chạy ở pull request để phát hiện lỗi trước khi merge, và chạy lại ở push vào nhánh phát hành. Có thể thêm cache pip để giảm thời gian build, nhưng không nên bỏ bước test. Trước khi gửi cho người dùng, kiểm tra installer trên Windows 10/11 sạch, kiểm tra shortcut, uninstall, audio device, Auto Key, preset và việc khởi động khi không có ASIO native.

### Tài liệu tham khảo

[1]: https://docs.github.com/en/actions/writing-workflows/quickstart "GitHub Actions — Quickstart"
[2]: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts "GitHub Actions — Store and share data with workflow artifacts"
[3]: https://pyinstaller.org/en/stable/operating-mode.html "PyInstaller — Operating modes"
[4]: https://jrsoftware.org/ishelp/ "Inno Setup Help"

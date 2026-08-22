# QuiLe-Autovocal

QuiLe-Autovocal là ứng dụng desktop Windows độc lập dành cho thu âm, hát livestream và karaoke. Chuỗi xử lý hiện tại là **dò cao độ → autotune → chồng bè → Delay → Reverb → output**. Một sound card hoặc audio interface có thể dùng đồng thời cho microphone input và headphone output.

## Hiệu ứng mới

**Reverb** gồm hai điều khiển: `Reverb mix` quyết định tỷ lệ tiếng vang trộn vào giọng khô, còn `Room size` thay đổi cảm giác không gian. Khi hát live nên bắt đầu ở 10–20% mix; karaoke có thể tăng lên 20–35%, nhưng tránh quá cao vì âm tiết sẽ bị nhòe.

**Delay** gồm `Delay mix`, `Thời gian (ms)` và `Feedback`. Delay 90–160 ms tạo cảm giác double nhẹ; 220–350 ms phù hợp echo karaoke; 450–700 ms tạo tiếng lặp rõ. Feedback nên bắt đầu ở 15–30%. Nếu nghe tiếng lặp dồn hoặc hú, giảm Feedback trước rồi giảm Mix. Các tham số được xử lý liên tục qua các block audio để tiếng lặp không bị cắt khi callback chuyển block.

## Chạy test trước khi đóng gói

Từ PowerShell trong thư mục dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD"
python -m unittest discover -s tests -p "test_*.py" -v
```

Bộ test tạo tín hiệu sin tổng hợp và kiểm tra các tiêu chí sau:

| Nhóm kiểm tra | Tiêu chí |
|---|---|
| Dò cao độ | 440 Hz và 220 Hz phải nằm trong sai số cho phép |
| Lượng tử hóa nốt | Tín hiệu gần C phải được đưa về tần số C |
| Chồng bè | Bè 3 phải tạo thêm năng lượng và không trùng hoàn toàn tiếng gốc |
| Delay | Xung âm thanh phải tạo được tín hiệu lặp ở block tiếp theo |
| Reverb | Không tạo NaN/Inf và không vượt biên âm thanh ±1.0 |

Script `build_windows.ps1` đã được thiết kế để **cài phụ thuộc → chạy toàn bộ test → chỉ đóng gói khi test đạt**. Nếu test thất bại, quá trình build sẽ dừng.

## Cấu hình low-latency trên Windows

### 1. Kết nối phần cứng

Cắm microphone vào audio interface, ưu tiên cổng input có preamp phù hợp. Cắm tai nghe trực tiếp vào headphone output của chính interface, không dùng loa ngoài trong lúc thử realtime. Nếu dùng micro condenser, bật phantom 48 V trên interface chỉ khi micro và hệ thống dây được hỗ trợ. Đặt gain sao cho khi hát lớn nhất, đèn báo không chuyển đỏ; tín hiệu bị clipping không thể sửa tốt bằng phần mềm.

### 2. Cài driver đúng của nhà sản xuất

Tải và cài driver ASIO chính thức từ nhà sản xuất sound card/audio interface. Không nên dùng driver Windows mặc định nếu driver ASIO chính thức có sẵn, vì driver chính thức thường cho phép chọn buffer, sample rate và chế độ exclusive ổn định hơn. Sau khi cài, khởi động lại Windows và đóng các ứng dụng đang chiếm độc quyền thiết bị.

### 3. Chọn sample rate thống nhất

Trong Windows Sound và phần mềm điều khiển của interface, đặt cùng một sample rate. Với hát live, bắt đầu ở **48 kHz**; nếu driver hoặc máy tính không ổn định, thử **44.1 kHz**. Không trộn 44.1 kHz ở một nơi với 48 kHz ở nơi khác khi chưa biết driver tự chuyển mẫu, vì việc chuyển đổi không cần thiết có thể tăng tải và gây lỗi đồng bộ.

### 4. Chọn buffer thấp nhưng ổn định

Trong bảng điều khiển ASIO của interface, bắt đầu với **128 samples**. Nếu tiếng bị rè, crackle, drop-out hoặc báo overload, tăng lên 256 samples. Nếu máy mạnh và hệ thống vẫn ổn định, thử 64 samples. Không nên chọn 32 samples ngay từ đầu vì độ ổn định phụ thuộc driver, CPU, USB controller và số hiệu ứng đang chạy.

| Buffer | Độ trễ lý thuyết một chiều tại 48 kHz | Khuyến nghị |
|---:|---:|---|
| 64 samples | khoảng 1.33 ms | Máy mạnh, driver tốt |
| 128 samples | khoảng 2.67 ms | Điểm bắt đầu tốt cho live |
| 256 samples | khoảng 5.33 ms | Ưu tiên ổn định |
| 512 samples | khoảng 10.67 ms | Chỉ dùng khi máy/driver bị quá tải |

Độ trễ thực tế còn gồm input buffer, output buffer, thời gian xử lý, driver và phần cứng; vì vậy con số trên chỉ là phần buffer lý thuyết. Trong QuiLe-Autovocal, block mặc định là 256 mẫu để cân bằng tải và độ ổn định.

### 5. Cấu hình trong QuiLe-Autovocal

Mở ứng dụng, chọn đúng thiết bị có cả số kênh `in / out`, chọn sample rate giống với driver, rồi bấm **Bắt đầu monitor**. Đặt Reverb và Delay về 0% để đo thử đường tiếng sạch trước. Sau khi nghe tiếng ổn định, bật autotune, sau đó bật chồng bè và hiệu ứng từng phần một. Cách này giúp xác định chính xác thành phần nào gây quá tải hoặc feedback.

Để hát live, nên dùng các mức khởi đầu: Retune 25–45 ms, Correction mix 70–100%, chồng bè 15–30%, Reverb mix 10–20%, Delay mix 8–18%, Feedback 15–25%. Đây là điểm khởi đầu để tinh chỉnh theo giọng và phòng, không phải preset cố định cho mọi hệ thống.

### 6. Tối ưu Windows

Đặt Power mode ở chế độ hiệu năng cao khi livestream. Tắt các chương trình đang phát âm thanh nền không cần thiết, thông báo hệ thống, trình duyệt có nhiều tab và ứng dụng họp trực tuyến. Không sử dụng hub USB rẻ hoặc chia sẻ quá nhiều thiết bị trên cùng hub; nếu có thể, cắm interface trực tiếp vào cổng USB ổn định trên máy. Không để Windows tự đổi thiết bị mặc định trong lúc đang hát.

Nếu xuất hiện crackle, hãy lần lượt tăng buffer từ 128 lên 256, tắt Reverb/Delay, giảm sample rate từ 96 kHz xuống 48 kHz, đóng ứng dụng nền và kiểm tra driver. Nếu nghe trễ nhưng không crackle, giảm buffer từng bước; nếu bắt đầu drop-out, quay lại mức trước đó. Luôn đeo tai nghe khi kiểm tra để tránh vòng lặp âm thanh từ loa về microphone.

## Đóng gói Windows

Chạy:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

Lệnh này chạy test trước rồi tạo `dist\QuiLe-Autovocal\QuiLe-Autovocal.exe`. Sau đó mở `QuiLe-Autovocal.iss` bằng Inno Setup và bấm **Compile** để tạo `QuiLe-Autovocal-Setup.exe`. Người dùng cuối chỉ cần chạy bộ cài này, bấm Install, rồi mở shortcut QuiLe-Autovocal; không cần cài Python.

## Giới hạn hiện tại

Reverb và Delay trong bản MVP là các hiệu ứng realtime nhẹ, chưa phải engine studio hoàn chỉnh. Để phát hành thương mại, nên bổ sung giữ formant chất lượng cao, limiter, noise gate, preset, tempo-sync delay, đo round-trip latency, lựa chọn ASIO native trực tiếp và kiểm thử trên nhiều model audio interface.


## Khử ồn AI thích ứng

QuiLe-Autovocal có bộ **AI Adaptive Noise Suppression** dạng nhẹ cho realtime. Bộ lọc ước lượng phổ tiếng ồn nền, tạo mặt nạ giảm mềm theo tỷ lệ tín hiệu trên nhiễu, sau đó đưa tín hiệu sạch vào autotune. Vì xử lý theo block để giữ độ trễ thấp, đây là bộ khử ồn thích ứng phù hợp cho tiếng quạt, điều hòa, hum nhẹ và nền phòng; không nên kỳ vọng thay thế hoàn toàn mô hình neural chuyên dụng trong môi trường rất ồn.

Để thiết lập, bật **Học tiếng ồn nền**, giữ microphone ở vị trí hát nhưng im lặng khoảng 2–5 giây, rồi tắt chế độ học. Sau đó bật **Bật khử ồn** và bắt đầu với Cường độ 50–65%. Nếu giọng bị mỏng, mất phụ âm hoặc có tiếng lạo xạo, giảm cường độ; nếu nền vẫn còn rõ, tăng từng bước. Nên học lại hồ sơ noise khi đổi phòng, đổi gain hoặc đổi vị trí microphone bằng nút **Đặt lại hồ sơ noise** rồi thực hiện lại quy trình học.

Khử ồn được đặt trước autotune và chồng bè trong chuỗi tín hiệu. Hãy giữ Reverb/Delay ở mức 0 trong lúc học noise; nếu không, tiếng vang có thể bị học nhầm thành tiếng ồn nền.


## ASIO native và buffer siêu thấp

Giao diện hiện ưu tiên các thiết bị thuộc host API ASIO và hiển thị rõ tên host API trong danh sách. Có thể chọn `32 samples`, `48 samples` hoặc `64 samples`; driver ASIO thực tế vẫn có quyền từ chối kích thước không nằm trong giới hạn min/max/granularity của chính nó. Khi đó hãy chọn 64 hoặc 128 samples và kiểm tra crackle/drop-out thay vì ép một giá trị không được phần cứng hỗ trợ. Mức 32 samples tương đương khoảng 0,67 ms cho một buffer ở 48 kHz, nhưng round-trip latency thực tế còn phụ thuộc input/output buffer, driver, xử lý và phần cứng.

## Quản lý và gán lại phím tắt

Bấm **Quản lý / gán phím tắt** để mở bảng cấu hình. Chọn **Gán** bên cạnh chức năng, nhấn tổ hợp phím mới, rồi sử dụng ngay trong cửa sổ chính. Ứng dụng từ chối tổ hợp đã được dùng cho chức năng khác. Bấm **Khôi phục mặc định** để đưa toàn bộ phím tắt về cấu hình ban đầu.

| Chức năng | Mặc định |
|---|---|
| Monitor | F1 |
| Autotune bật/tắt | F2 |
| Khử ồn bật/tắt | F3 |
| Chồng bè bật/tắt | F4 |
| Reverb bật/tắt | F5 |
| Delay bật/tắt | F6 |
| Học noise | F7 |
| Ghi âm | Ctrl+R |


## Auto Key cho nhạc nền

Auto Key có thể phân tích một input vật lý từ audio interface hoặc một input loopback/virtual audio đại diện cho âm thanh đang phát trên máy tính. Chọn nguồn trong mục **Auto Key — tự nhận diện tông nhạc nền**, bật **Bật Auto Key**, rồi để nhạc chạy liên tục vài giây. Bộ phân tích tích lũy chroma qua nhiều cửa sổ, phân biệt thang Trưởng/Thứ, hiển thị độ tin cậy và chỉ tự cập nhật Tông giọng/Thang âm khi kết quả đủ ổn định.

Đối với nhạc đang phát trên máy tính, trên Windows nên dùng nguồn `Speakers (loopback)` nếu driver/host API cung cấp nguồn này. Nếu thư viện hoặc driver không hiển thị loopback, có thể dùng VB-Audio Virtual Cable hoặc thiết bị loopback của audio interface, đặt output của ứng dụng phát nhạc vào đó rồi chọn virtual input tương ứng trong QuiLe-Autovocal. Khi phân tích nhạc từ thiết bị ngoài, đưa line out/mixer out của nguồn nhạc vào line input riêng của audio interface; không nên đưa tín hiệu microphone vào nguồn Auto Key vì giọng hát có thể làm kết quả dao động.

Với nhạc stereo, bộ phân tích hiện lấy kênh trái để giảm tải. Nếu nguồn loopback chỉ cho phép stereo, hãy chọn thiết bị stereo thay vì ép mono. Auto Key không cần nằm trong đường monitor của giọng; nó chỉ đọc nguồn phân tích và cập nhật Key/Scale cho autotune. Nếu bài hát chuyển tông giữa chừng, nên tắt rồi bật lại Auto Key hoặc chờ bộ lịch sử mới ổn định.

Nguồn tham khảo: [Audacity — Windows WASAPI loopback](https://manual.audacityteam.org/man/tutorial_recording_computer_playback_on_windows.html), [Automatic key detection methodology](https://arxiv.org/html/2505.17259v1).


## Bộ cài QuiLe-Autovocal one-click

Bản build Windows dùng PyInstaller ở chế độ `onedir` để gom Python interpreter, mã ứng dụng và dependencies thành thư mục chạy độc lập. Inno Setup sau đó đóng thư mục này thành một file `QuiLe-Autovocal-Setup.exe`; người dùng cuối chỉ cần chạy file, bấm Install và không cần cài Python hay các thư viện pip. PyInstaller hỗ trợ cả one-folder và one-file; chế độ one-folder thường dễ chẩn đoán lỗi hơn trước khi đưa vào installer [1]. Inno Setup hỗ trợ tạo một file EXE duy nhất để phân phối ứng dụng Windows [2].

Trên máy Windows phát triển, chạy `Set-ExecutionPolicy -Scope Process Bypass`, sau đó `./build_windows.ps1`. Script sẽ cài dependencies, chạy test, tạo `dist\\QuiLe-Autovocal` và nếu phát hiện Inno Setup sẽ sinh `output\\QuiLe-Autovocal-Setup.exe`.

Driver ASIO không thể được tự động chọn chung cho mọi thiết bị. Trình cài chỉ chạy thêm `drivers\\ASIO-Driver-Setup.exe` nếu nhà phát hành đặt vào đó bộ cài chính thức phù hợp với model và có quyền phân phối. Nếu không có file này, ứng dụng vẫn cài đặt đầy đủ; người dùng cài driver ASIO từ hãng audio interface rồi mở lại ứng dụng. Bộ cài không tự tải hoặc chạy file driver không rõ nguồn gốc.

### Tài liệu tham khảo

[1]: https://pyinstaller.org/en/stable/operating-mode.html "PyInstaller — What It Does and How It Works"
[2]: https://jrsoftware.org/ishelp/ "Inno Setup Help"

# QuiLe-Autovocal — Hướng dẫn sử dụng

## 1. Giới thiệu

QuiLe-Autovocal là phần mềm Windows độc lập dành cho thu âm, hát livestream và karaoke. Phần mềm nhận microphone từ sound card/audio interface, xử lý khử ồn, autotune, chồng bè, Delay và Reverb, rồi phát tín hiệu đã xử lý ra tai nghe hoặc thiết bị livestream.

> Luôn dùng tai nghe khi monitor realtime. Nếu microphone thu tiếng từ loa, tín hiệu sẽ tạo vòng lặp và có thể gây hú.

## 2. Cài đặt

Chạy file `QuiLe-Autovocal-Setup.exe`, giữ thư mục mặc định và bấm **Install**. Bộ cài đã chứa runtime và dependencies cần thiết nên người dùng cuối không cần cài Python. Nếu sound card không có native ASIO driver, cài ASIO4ALL hoặc FlexASIO trước khi mở QuiLe-Autovocal.

Driver ASIO của từng hãng có thể là phần mềm độc quyền. Nếu bộ cài có kèm driver chính thức đúng model, trình cài sẽ chạy bước đó; nếu không, tải driver từ website chính thức của nhà sản xuất thiết bị.

## 3. Kết nối phần cứng

Cắm microphone vào input của audio interface và tai nghe vào headphone output của cùng interface. Mở phần mềm điều khiển của interface, chọn sample rate 48 kHz và bắt đầu với buffer 128 samples. Khi hệ thống ổn định, thử 64, 48 hoặc 32 samples. Buffer càng nhỏ thì độ trễ lý thuyết càng thấp nhưng nguy cơ crackle/drop-out càng cao.

Trong QuiLe-Autovocal, bấm **Tự nhận thiết bị**. Ưu tiên thiết bị có tên host `[ASIO]`. Chọn buffer phù hợp rồi bấm **Bắt đầu monitor**. Nếu 32 samples không mở được, quay về 64 hoặc 128 samples.

## 4. Cấu hình ASIO4ALL

ASIO4ALL là lớp ASIO dùng để gom hoặc chuyển tiếp thiết bị Windows khi không có driver ASIO native. Cài từ nguồn chính thức, khởi động lại ứng dụng âm thanh, rồi mở **ASIO4ALL Offline Settings** từ biểu tượng ASIO4ALL trong khay hệ thống hoặc từ ứng dụng đang sử dụng driver.

Trong bảng ASIO4ALL, bật biểu tượng nguồn bên cạnh đúng microphone và đúng output/headphone. Tắt những thiết bị không dùng để tránh xung đột clock. Nếu cần dùng một audio interface duy nhất, chỉ bật input và output của interface đó. Không bật đồng thời microphone laptop, webcam và interface nếu chưa cần.

Trong QuiLe-Autovocal, chọn thiết bị có host `[ASIO]` và kiểm tra input/output. Nếu thiết bị không xuất hiện, đóng các ứng dụng đang giữ microphone hoặc loa độc quyền, mở lại ASIO4ALL, rồi bấm **Tự nhận thiết bị**.

ASIO4ALL không biến phần cứng thành native ASIO thật; độ ổn định và độ trễ phụ thuộc WDM driver, thiết bị, USB controller và cách các thiết bị được ghép. Nếu nghe crackle, tăng buffer, chỉ bật một thiết bị input và một thiết bị output, hoặc dùng WASAPI/driver chính thức.

## 5. Cấu hình FlexASIO

FlexASIO là một ASIO driver dạng cấu hình, sử dụng backend như WASAPI, DirectSound hoặc WDM-KS. Sau khi cài FlexASIO, tạo hoặc chỉnh file `FlexASIO.toml` trong thư mục hồ sơ người dùng Windows. Cấu hình tối thiểu có thể bắt đầu như sau:

```toml
backend = "Windows WASAPI"
[input]
device = "Microphone (Tên audio interface)"
[output]
device = "Headphones (Tên audio interface)"
[input.mix]
volume = 1.0
[output.mix]
volume = 1.0
```

Tên thiết bị phải khớp với tên Windows hiển thị trong Sound Settings. Nếu backend WASAPI không ổn định, thử backend được FlexASIO hỗ trợ phù hợp với hệ thống, nhưng chỉ nên thay đổi từng thông số một. Đóng và mở lại QuiLe-Autovocal sau mỗi lần đổi file cấu hình.

Khi FlexASIO không mở được thiết bị, kiểm tra lại tên thiết bị, sample rate của Windows và quyền độc quyền. Không chạy đồng thời ASIO4ALL và FlexASIO cho cùng một đường tiếng; hãy chọn một driver ASIO duy nhất trong hệ thống.

## 6. Auto Key cho nhạc nền

Mục **Auto Key — tự nhận diện tông nhạc nền** có hai nhóm nguồn. Với nhạc đang phát trên máy tính, chọn `Speakers (loopback)` nếu Windows/driver cung cấp. Nếu không có loopback, dùng VB-Audio Virtual Cable hoặc loopback của audio interface; đặt output của phần mềm phát nhạc vào virtual cable rồi chọn virtual input trong QuiLe-Autovocal.

Với nhạc từ thiết bị ngoài, đưa line out hoặc mixer out vào line input của audio interface, sau đó chọn input đó trong **Nguồn phân tích**. Không chọn microphone làm nguồn Auto Key vì giọng hát có thể làm tông dao động.

Bật **Bật Auto Key**, cho nhạc chạy liên tục vài giây và quan sát tông cùng phần trăm tin cậy. Khi đủ ổn định, QuiLe-Autovocal tự cập nhật Tông giọng và Thang âm cho autotune. Nếu bài chuyển tông, tắt rồi bật lại Auto Key để làm mới lịch sử phân tích. WASAPI loopback trên Windows thường được sử dụng như một input loopback của thiết bị phát [1].

## 7. Preset giọng hát

Trong mục **Preset giọng hát**, chọn một cấu hình rồi bấm **Áp dụng preset**. Preset chỉ thay đổi thông số xử lý giọng và hiệu ứng, không thay đổi audio interface.

| Preset | Mục đích | Gợi ý sử dụng |
|---|---|---|
| Nam trầm | Retune chậm hơn, khử ồn vừa, bè 3 nhẹ, không gian vừa | Nam giọng thấp, ballad, karaoke |
| Nữ cao | Retune nhanh hơn, Reverb sáng hơn, bè 3 nhẹ | Giọng nữ cao, pop, livestream |
| Radio voice | Khử ồn mạnh, autotune rõ, không chồng bè, vang ngắn | Nói chuyện, podcast, phát thanh |

Sau khi áp dụng, người dùng vẫn có thể chỉnh từng thanh trượt và công tắc. Nên bắt đầu với preset gần nhất rồi tinh chỉnh theo microphone, phòng và nhạc nền.

## 8. Chuỗi xử lý và công tắc

Chuỗi mặc định là khử ồn → autotune → chồng bè → Delay → Reverb. Mỗi khối có công tắc riêng. Tắt Reverb/Delay khi kiểm tra đường tiếng sạch; tắt chồng bè nếu chỉ muốn giọng chính. Dùng Bypass để so sánh nhanh tín hiệu trước và sau autotune.

## 9. Phím tắt

| Chức năng | Phím mặc định |
|---|---|
| Monitor | F1 |
| Autotune bật/tắt | F2 |
| Khử ồn bật/tắt | F3 |
| Chồng bè bật/tắt | F4 |
| Reverb bật/tắt | F5 |
| Delay bật/tắt | F6 |
| Học noise | F7 |
| Ghi âm | Ctrl+R |

Bấm **Quản lý / gán phím tắt** để gán lại. Chọn **Gán**, nhấn tổ hợp phím mới và đóng cửa sổ. Ứng dụng không cho phép hai chức năng dùng chung một tổ hợp. `Ctrl+F2` đến `Ctrl+F6` giảm tham số tương ứng; `Shift+F2` đến `Shift+F6` tăng tham số.

## 10. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Không có thiết bị | Bấm Tự nhận thiết bị, kiểm tra cáp USB, đóng ứng dụng khác đang dùng thiết bị |
| Không mở được 32 samples | Chọn 64 hoặc 128 samples; driver có thể không hỗ trợ buffer thấp |
| Crackle/drop-out | Tăng buffer, giảm sample rate, tắt bớt Reverb/Delay và đóng ứng dụng nền |
| Có tiếng hú | Dùng tai nghe, giảm gain microphone, không phát loa ngoài vào microphone |
| Auto Key dao động | Chọn line/loopback của nhạc nền, tăng thời gian nhạc chạy, tránh để giọng lọt vào nguồn phân tích |
| Giọng bị mỏng | Giảm cường độ khử ồn, giảm Correction mix, kiểm tra clipping ở preamp |
| Delay bị dồn tiếng | Giảm Feedback và Delay mix |

## 11. Thu âm và livestream

Đeo tai nghe, chọn input/output cùng audio interface và bấm **Bắt đầu monitor**. Kiểm tra giọng bằng mức tín hiệu, sau đó bật từng hiệu ứng. Bấm **Ghi âm 10 giây** để kiểm tra trước khi livestream. Trong OBS, chọn thiết bị output tương ứng làm nguồn Mic/Aux hoặc dùng virtual audio cable nếu cần tách đường nhạc nền và giọng đã xử lý.

## 12. Ghi chú kỹ thuật

QuiLe-Autovocal hiện là bản MVP realtime. Bộ Auto Key sử dụng chroma và profile Trưởng/Thứ, còn các hiệu ứng được tối ưu nhẹ để hạn chế độ trễ. Kết quả phụ thuộc chất lượng nguồn nhạc, driver, audio interface, gain, phòng và buffer. PyInstaller có thể gom interpreter cùng dependencies vào bundle one-folder/one-file [2].

### Tài liệu tham khảo

[1]: https://manual.audacityteam.org/man/tutorial_recording_computer_playback_on_windows.html "Audacity Manual — Windows WASAPI loopback recording"
[2]: https://pyinstaller.org/en/stable/operating-mode.html "PyInstaller — What It Does and How It Works"

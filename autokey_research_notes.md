# Ghi chú Auto Key

Trên Windows, WASAPI loopback cho phép thu tín hiệu playback số từ thiết bị phát, nhưng luồng loopback thường xuất hiện như một input đặc biệt và có thể cần driver/virtual cable tùy thư viện. Audacity hướng dẫn chọn Windows WASAPI và input có hậu tố `(loopback)`; một số thiết bị chỉ hoạt động với stereo.

QuiLe-Autovocal sẽ hỗ trợ hai loại nguồn: input vật lý từ audio interface (line in/mixer out) và input loopback/virtual audio của Windows. Auto Key sẽ tích lũy chroma theo nhiều cửa sổ, so khớp profile Major/Minor, làm mượt kết quả và chỉ tự áp dụng khi độ tin cậy vượt ngưỡng.

Nguồn: https://manual.audacityteam.org/man/tutorial_recording_computer_playback_on_windows.html
Nguồn: https://arxiv.org/html/2505.17259v1

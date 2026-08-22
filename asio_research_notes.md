# Ghi chú kỹ thuật ASIO

- python-sounddevice cung cấp `AsioSettings(channel_selectors=...)` qua tham số `extra_settings` của `Stream`, cho phép chọn các kênh ASIO cụ thể.
- Mô hình buffer native của PortAudio/ASIO phải tuân theo các ràng buộc min, max và granularity do driver báo; không được ép mọi thiết bị dùng 32 hoặc 48 samples.
- `blocksize` của callback và buffer native của driver là các lớp khác nhau; độ trễ thực tế còn gồm input/output buffering, xử lý và phần cứng.
- Nguồn: https://python-sounddevice.readthedocs.io/en/0.3.15/api/platform-specific-settings.html
- Nguồn: https://github.com/PortAudio/portaudio/wiki/BufferingLatencyAndTimingImplementationGuidelines

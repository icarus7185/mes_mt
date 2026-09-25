# Bộ prompt dựng project


## B. Triển khai

** Khung repo**

````text
Tạo khung repo theo brief và SPEC_SYSTEM_OVERVIEW.md: các package, thư mục data (kèm .placeholder), requirements.txt đã ghim version, pytest.ini và .gitignore (ignore *.jpg).
Chưa cần viết logic.
````

** Code từng service**

````text
Code service <monitor | asst | prod_line> theo spec của nó, DOMAIN_MODEL.md, api-spec.md và CODING_RULES.md.
Nên làm theo thứ tự monitor → asst → prod_line để có service phía sau chạy thử.
Riêng asst: code xong thì gọi /api/train một lần để có sẵn file model.
Xong thì chạy service lên, thử vài request, rồi báo tôi kết quả.
````

** Unit test**

````text
Viết unit test cho cả 3 service trong tests/<service>/. Acceptance criteria nào kiểm tra được bằng unit test thì phải có test.
Không gọi Hugging Face hay service thật, cái gì cần thì mock. Test nào đụng đến file thì dùng tmp_path.
````

** CI và README (cổng B)**

````text
Thêm GitHub Actions: chạy test khi có PR vào main, cài torch bản CPU cho nhẹ.
Thêm issue template cho bug, feature và spike.
Viết README.md gồm: giới thiệu, cấu trúc thư mục, cách cài (có bước giải nén test_images.zip), cách chạy, cách test.
````

### Sửa lỗi và thay đổi

Dùng sau khi hệ thống đã chạy được. Sửa gì thì cập nhật spec và test cho khớp, để tài liệu không bị lệch so với code.

** Sửa lỗi (mẫu chung)**

````text
Tôi gặp lỗi này ở service <tên service>:
<dán log / traceback / mô tả hiện tượng>
Tìm nguyên nhân trước, giải thích cho tôi, rồi mới sửa. Viết thêm test tái hiện lỗi này, sửa xong thì test phải pass. Đừng sửa lan sang chỗ khác.
````

** Sửa lỗi: đọc nhầm file .placeholder**

````text
Kiểm tra các chỗ đọc file trong thư mục */data/. Chỗ nào cũng phải lọc theo đuôi file phù hợp, không được đọc, trả về hay xoá nhầm .placeholder.
Sửa chỗ nào sai và thêm test cho từng chỗ đó.
````

** Sửa lỗi: asst còn sót file**

````text
Khi monitor đang tắt, gửi ảnh có lỗi sang asst thì file trong asst/data/img_out không bị xoá. Theo spec, asst không được giữ lại ảnh nào, kể cả khi gửi sang monitor thất bại. Sửa lại và thêm test cho trường hợp monitor không phản hồi.
````

** Thay đổi cấu hình**

````text
Tôi muốn monitor giữ 20 ảnh thay vì 10, và tỉ lệ gửi record lỗi giảm xuống 10%. Đổi trong config, rồi tìm và cập nhật mọi chỗ trong docs và README đang ghi số cũ.
````

** Thêm chức năng: tải lịch sử dự đoán**

````text
Thêm vào monitor một endpoint để tải file records_history.csv, và một nút "Download CSV" trên dashboard. Chưa có file thì báo không có dữ liệu, đừng trả lỗi 500.
Cập nhật SPEC_MONITOR.md, api-spec.md và thêm test.
````

** Thay đổi giao diện: dashboard monitor**

````text
Trên dashboard monitor:
- biểu đồ Usage_kWh thêm một đường nét đứt cho giá trị trung bình;
- bảng record cho lọc theo Load Type (All / Light / Medium / Maximum).
Giữ nguyên style hiện tại, và vẫn phải xem ổn ở theme tối lẫn trên màn hình nhỏ. Làm xong chụp màn hình cho tôi xem.
````

** Thay đổi giao diện: trang prod_line**

````text
Trên trang prod_line, thêm một dòng đếm số lần gửi Success/Failed từ lúc service khởi động, chia riêng cho ảnh và record. Số đếm giữ trong bộ nhớ, restart thì về 0. Nhớ cập nhật SPEC_PROD_LINE.md.
````


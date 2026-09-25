# Bộ prompt dựng project

## C. Kiểm tra

** Viết unit test**

````text
Viết unit test cho 3 service trong tests/<service>/, dựa vào acceptance criteria trong spec của từng service. Đừng dựa vào code, vì mục đích là kiểm tra code có làm đúng spec không.
Ưu tiên các trường hợp dễ sai: thư mục trống, file .placeholder, gửi lỗi, thiếu file model, path traversal, dữ liệu vượt giới hạn.
Không gọi Hugging Face hay service thật, cần thì mock. Test nào đụng đến file thì dùng tmp_path.
Chạy python -m pytest -q. Test nào fail vì code làm khác spec thì giữ nguyên test, đừng sửa code, báo tôi.
````

** Review theo coding rules**

````text
Review code theo docs/CODING_RULES.md và báo lỗi theo dạng `Rule ID — file:line — mô tả`.
Đi qua checklist MUST, rồi sửa các lỗi MUST và chạy lại test.
````

** Chạy thử end-to-end **

````text
Giải nén ảnh mẫu, chạy cả 3 service rồi để khoảng 5 phút. Kiểm tra:
- ảnh lỗi có sang được monitor không, và asst có còn sót file không;
- monitor có giữ đúng 10 ảnh không;
- record có Usage_kWh không, file CSV có được ghi thêm không;
- tỉ lệ gửi lỗi có gần 10% và 20% không;
- tắt asst một lúc thì prod_line có báo Failed mà vẫn chạy tiếp không;
- dashboard hiển thị có đúng không.
Gửi tôi bảng PASS/FAIL. Xong thì dọn thư mục data về như cũ.
````

** Đối chiếu tài liệu với code (cổng C)**

````text
Lấy code hiện tại làm chuẩn, rồi đọc lại toàn bộ tài liệu và README để tìm chỗ nào đã lỗi thời hoặc không khớp với code.
Tài liệu sai thì sửa tài liệu. Còn nếu code sai thì đừng sửa, báo tôi.
Quyết định nào mới chốt thì ghi thêm vào brief.
````

### Kiểm tra theo từng tình huống

Dùng sau mỗi lần sửa lỗi hay thay đổi, hoặc khi nghi có vấn đề ở một chỗ cụ thể. Chỉ báo cáo trước, chưa sửa, trừ khi tôi bảo sửa.

** Review thay đổi trước khi commit (mẫu chung)**

````text
Review giúp tôi các thay đổi chưa commit (git diff). Tìm bug, trường hợp biên bị bỏ sót, và chỗ làm khác spec. Kiểm tra xem test và tài liệu đã được cập nhật theo chưa.
Báo theo dạng file:line — vấn đề — mức độ. Chưa sửa gì cả.
````

** Rà soát các chỗ đọc, ghi, xoá file**

````text
Liệt kê mọi chỗ trong code có đọc, ghi, liệt kê hoặc xoá file trong */data/. Với từng chỗ, kiểm tra:
- có lọc đúng đuôi file không, có đụng nhầm .placeholder không;
- khi có exception giữa chừng thì file tạm có bị sót lại không;
- thư mục chưa tồn tại thì có bị lỗi không.
Lập bảng kết quả, chỗ nào có vấn đề thì kèm cách sửa đề xuất.
````

** Kiểm tra khi service phía sau bị lỗi**

````text
Kiểm tra lần lượt từng trường hợp: monitor tắt, monitor trả lỗi 500, asst trả lời chậm hơn timeout. Với mỗi trường hợp, xem asst và prod_line xử lý ra sao: có crash không, có sót file không, log có ghi rõ không, giao diện có báo Failed không.
Viết thành unit test với mock, đừng phải chạy service thật.
````

** Kiểm tra bảo mật cơ bản**

````text
Rà soát nhanh bảo mật cho 3 service: path traversal ở các endpoint nhận tên file, upload file không phải ảnh hoặc file rất lớn, record gửi thiếu field hoặc sai kiểu, và các endpoint có ghi file hay tốn tài nguyên (như /api/train).
Hệ thống là PoC nên chưa cần auth, chỉ cần chỉ ra rủi ro và mức độ.
````

** Kiểm tra giao diện**

````text
Mở dashboard monitor và trang prod_line trong browser, rồi kiểm tra: theme sáng và tối, màn hình rộng 375px, dùng bàn phím mở và đóng ảnh, và trạng thái lúc chưa có dữ liệu. Chụp màn hình từng trường hợp, rồi ghi ra chỗ nào bị vỡ layout, khó đọc hoặc không bấm được.
````

** Chạy dài hạn**

````text
Chạy cả hệ thống khoảng 1 tiếng. Cứ 10 phút ghi lại một lần: RAM của từng service, số file trong monitor/data/img, kích thước records_history.csv và kích thước các file log.
Chỉ ra thứ gì tăng mãi không dừng mà không có chủ ý (CSV thì được phép tăng).
````

** Kiểm tra cài đặt trên máy sạch**

````text
Làm theo đúng README trong một virtualenv mới: cài thư viện, giải nén ảnh mẫu, chạy test, chạy 3 service. Bước nào README ghi thiếu, ghi sai, hoặc phải tự đoán mới làm tiếp được thì ghi lại. Đây cũng là cách để kiểm tra CI có chạy được không.
````

# mes_mt

Hệ thống giám sát lỗi thép bằng YOLO, gồm 3 ứng dụng FastAPI **độc lập**,
mỗi ứng dụng chạy trên một cổng riêng và giao tiếp với nhau qua HTTP theo
mô hình dây chuyền: `prod_line` → `asst` → `monitor`.

```
data/from_camera/  --(random)-->  prod_line  --POST-->  asst  --POST-->  monitor
                                                   |
                                          data/img_in/ (tạm)
                                          data/img_out/ (khi có phát hiện)
                                                                     |
                                                              data/hist/ (tối đa 10 ảnh)
```

## Cấu trúc thư mục

### `prod_line/` — Bộ mô phỏng camera, cổng `8001`

Cứ mỗi `settings.interval_seconds` giây (mặc định 10s), đọc ngẫu nhiên 1
file ảnh trong `data/from_camera/` rồi gửi (`POST`) tới endpoint
`/api/image` của `asst`. Trang chủ `GET /` hiển thị ảnh vừa gửi gần nhất
và thời điểm đã gửi.

- `prod_line/producer.py` — vòng lặp nền chạy trong `lifespan` của app;
  sau khi gửi thành công sẽ lưu ảnh + thời gian vào `prod_line/state.py`.
- `prod_line/state.py` — nơi lưu tạm (trong bộ nhớ) ảnh gửi gần nhất.
- `prod_line/routers/api.py` — `GET /api/image/latest`,
  `GET /api/image/meta` phục vụ trang chủ.
- `prod_line/routers/dashboard.py` — `GET /` render trang chủ.
- `prod_line/services/image_service.py` — chọn ngẫu nhiên 1 file ảnh.
- `prod_line/config.py` — `image_in_dir` (`data/from_camera`),
  `interval_seconds`, `asst_image_url`.

### `asst/` — Bộ xử lý YOLO, cổng `8002`

`POST /api/image` nhận ảnh từ `prod_line`, lưu tạm vào `data/img_in/`,
rồi đưa qua model YOLO để nhận diện lỗi:

- **Nếu YOLO không phát hiện gì** → chỉ ghi log kết quả bình thường, xoá
  file tạm, **không** lưu vào `data/img_out/` và **không** gửi cho
  `monitor`.
- **Nếu YOLO có phát hiện lỗi** → lưu ảnh kết quả vào `data/img_out/`
  (tên file được nối thêm giờ:phút:giây lúc xử lý), xoá file ảnh gốc tạm
  trong `data/img_in/`, gửi ảnh kết quả cho `monitor`, sau khi gửi thành
  công thì xoá luôn file ảnh đó khỏi `data/img_out/`.

- `asst/routers/api.py` — endpoint lưu/xử lý/dọn dẹp/gửi tiếp nói trên.
- `asst/services/image_service.py` — chuyển đổi bytes ⇄ ảnh, lưu file.
- `asst/services/yolo_service.py` — tải model YOLO từ Hugging Face Hub và
  chạy suy luận; `predict()` trả về `(None, [])` nếu không phát hiện gì,
  hoặc `(ảnh_đã_vẽ, [tên_class, ...])` nếu có phát hiện.
- `asst/config.py` — `image_in_dir`, `image_out_dir`, `monitor_image_url`,
  repo/tên file model Hugging Face.

### `monitor/` — Bảng giám sát, cổng `8003`

`POST /api/image` nhận ảnh kết quả từ `asst` và lưu (archive) vào
`data/hist/`, chỉ giữ lại **tối đa 10 ảnh mới nhất** (ảnh cũ hơn sẽ tự
động bị xoá). Trang `GET /` hiển thị:

- Ảnh nhận được gần nhất + thời gian nhận.
- Album gồm toàn bộ ảnh hiện có trong `data/hist/`.

- `monitor/routers/api.py` — `POST /api/image` (nhận + lưu),
  `GET /api/image/latest`, `GET /api/image/meta` (ảnh/thời gian gần
  nhất), `GET /api/hist` (danh sách album), `GET /api/hist/{filename}`
  (lấy 1 ảnh trong album).
- `monitor/services/history_service.py` — lưu ảnh vào `data/hist/` và tự
  dọn bớt để chỉ giữ `hist_max_files` ảnh mới nhất (mặc định 10).
- `monitor/templates/`, `monitor/static/` — giao diện dashboard + JS/CSS.
- `monitor/config.py` — `hist_dir`, `hist_max_files`.

## Cài đặt & chạy

```bash
pip install -r requirements.txt
```

Mở 3 terminal riêng, chạy từng service (chạy theo thứ tự nào cũng được —
nếu service phía sau chưa lên thì service phía trước sẽ tự thử lại ở
lượt kế tiếp):

```bash
uvicorn monitor.main:app --port 8003
```

```bash
uvicorn asst.main:app --port 8002
```

```bash
uvicorn prod_line.main:app --port 8001
```

Sau đó mở:

- http://localhost:8001/ — xem `prod_line` vừa gửi ảnh gì, lúc nào.
- http://localhost:8003/ — xem dashboard `monitor` (ảnh mới nhất + album).

**Lưu ý:** tất cả đường dẫn thư mục (`data/...`, `logs/...`) đều là
đường dẫn tương đối, nên phải chạy `uvicorn` từ thư mục gốc của dự án.

## Ghi log

Mỗi app ghi log ra file riêng trong thư mục `logs/` (tạo tương đối theo
thư mục đang chạy service đó), đồng thời in ra console:

- `logs/prod_line.log` — thời gian + tên file đã gửi cho `asst`.
- `logs/asst.log` — thời gian + tên file của mỗi request nhận được, tên
  file đã lưu khi có phát hiện lỗi (kèm danh sách class), và thời điểm
  đã gửi tiếp cho `monitor`.
- `logs/monitor.log` — thời gian + tên file của mỗi request nhận được từ
  `asst`.

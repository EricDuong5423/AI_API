# 🤖 AI-Powered Engineering API

Đây là một backend API sử dụng **Python (Flask)** để tích hợp với **Gemini AI** và **MongoDB**, phục vụ cho các tác vụ kỹ thuật như:

- Lựa chọn động cơ điện phù hợp
- Chọn vật liệu dựa trên ảnh bảng dữ liệu
- Trích xuất thông số từ ảnh kỹ thuật

---

## 🧩 Công nghệ sử dụng

- Python 3.10+
- Flask + Flask-CORS
- Google Gemini API (via `google.genai`)
- MongoDB (qua `pymongo`)
- Dotenv (`python-dotenv`) để quản lý biến môi trường

---

## 🚀 Cách chạy API trên localhost

### 1. Clone và vào thư mục project

```bash
cd AI_API
```

### 2. Tạo môi trường ảo (nên dùng)

```bash
python -m venv venv
venv\Scripts\activate   # Trên Windows
# source venv/bin/activate  # Trên macOS/Linux
```

### 3. Cài đặt thư viện cần thiết

```bash
pip install -r requirements.txt
```

> Nếu chưa có `requirements.txt`, bạn có thể tự tạo bằng:

```bash
pip freeze > requirements.txt
```

### 4. Tạo file `.env` với các biến sau:

```env
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=mongodb+srv://your_mongo_uri
IMAGE_URL=https://link-den-bang-vat-lieu.jpg
```

---

### 5. Chạy API

```bash
python app.py
```

> Mặc định sẽ chạy ở cổng `http://localhost:8080`

---

## 📡 Các API endpoint

### 🔹 `POST /api-ai/find-engine`

Tìm động cơ phù hợp với công suất và vận tốc yêu cầu.

```json
{
  "cong_suat_can_tim": 5,
  "van_toc_quay_can_tim": 1400
}
```

**Trả về:**

```json
{
  "best_motor_id": "abc123",
  "reason": "Động cơ này phù hợp vì..."
}
```

---

### 🔹 `POST /api-ai/find-material`

Chọn vật liệu phù hợp dựa trên ảnh bảng và thông số:

```json
{
  "sH": 130,
  "z": 20,
  "v": 3.5
}
```

---

### 🔹 `POST /api-ai/extract-input-image`

Gửi ảnh (dạng `multipart/form-data`) để trích xuất các thông số kỹ thuật:

```bash
curl -X POST -F "file=@form_input.png" http://localhost:8080/api-ai/extract-input-image
```

Trả về:

```json
{
  "F": 230,
  "v": 2.5,
  "D": 100,
  ...
}
```

---

## 📌 Ghi chú

- Đảm bảo bạn đã cấu hình đầy đủ API key và MongoDB URI.
- Ảnh đầu vào nên rõ nét, đúng định dạng.
- Gemini API yêu cầu kết nối Internet.

---

## 🧑‍💻 Tác giả

Dương Thanh Tú - CO3109 - AI Backend for Engineering Automation

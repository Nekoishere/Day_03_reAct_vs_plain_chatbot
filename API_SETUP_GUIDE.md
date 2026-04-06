# Hướng dẫn Cài đặt & Chạy REST API cho ReAct Agent

Tài liệu này được tách riêng để hướng dẫn chi tiết cách cấu hình và khởi chạy máy chủ REST API bằng FastAPI, giúp bạn dễ dàng đưa Agent này giao tiếp với các nền tảng khác (VD: Web App, Mobile App,...).

## Yêu cầu bắt buộc

Môi trường của bạn phải có:
- Python 3.9+
- Các thư viện API đã được khai báo ở `requirements.txt` (`fastapi`, `uvicorn`, `pydantic`).
- File `.env` chứa `OPENAI_API_KEY` (và tuỳ chọn `GEMINI_API_KEY` làm fallback).

## Các bước Cài đặt

**1. Khởi tạo và kích hoạt môi trường ảo (Virtual Environment):**
```bash
python -m venv venv

# Kích hoạt trên Windows:
venv\Scripts\activate      

# Kích hoạt trên MacOS/Linux:
# source venv/bin/activate 
```

**2. Cài đặt các thư viện phụ thuộc:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**3. Đảm bảo biến môi trường:**
Trong file `.env`, agent cần biết API key và Model bạn dùng. Ví dụ:
```env
OPENAI_API_KEY=sk-xxxx...
GEMINI_API_KEY=AIzaSy...    # (Fallback dự phòng khi OpenAI bị Rate Limit 429)

DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

## Khởi chạy Máy chủ API

Sử dụng uvicorn để bật server API, file code API nằm ở `src/api/api.py`:
```bash
uvicorn src.api.api:app --host 0.0.0.0 --port 8000 --reload
```
(*Lưu ý: Nếu file `api.py` của bạn nằm ở thư mục gốc, hãy sửa lệnh thành `uvicorn api:app --reload`*).

Sau khi khởi chạy thành công:
1. Truy cập vào **Swagger UI** để test code trực quan: [http://localhost:8000/docs](http://localhost:8000/docs)
2. Hoặc cấu hình Giao thức gọi HTTP (ví dụ từ Postman):
   - **Method**: `POST`
   - **Endpoint**: `http://localhost:8000/chat`
   - **Body (JSON)**:
     ```json
     {
         "message": "Kết quả 5 trận gần nhất của MU là gì?",
         "mode": "react"
     }
     ```
   - Cuối cùng, API sẽ trả về câu trả lời dưới dạng **Plain Text thô** (Chỉ chứa kết quả cuối dùng, không bao gồm cấu trúc suy luận).

---
*Ghi chú: Nếu hệ thống báo thiếu module, hãy chắc chắn bạn đã kích hoạt môi trường ảo (`venv`) trước khi gọi lệnh `uvicorn`.*

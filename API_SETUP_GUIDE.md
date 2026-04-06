# Hướng dẫn Cài đặt & Chạy Football ReAct API

Tài liệu này hướng dẫn cách khởi chạy **Football AI Agent** dưới dạng REST API sử dụng **FastAPI** và **Uvicorn**.

---

## 1. Yêu cầu hệ thống (Prerequisites)
- Python 3.9+
- Các API Keys của OpenAI và (tuỳ chọn) Gemini.

## 2. Cài đặt thư viện (Installation)
Cài đặt toàn bộ các thư viện cần thiết, bao gồm thư viện core của Agent và các thư viện hỗ trợ API (`fastapi`, `uvicorn`, `pydantic`).

Chạy lệnh sau tại thư mục gốc của dự án:
```bash
pip install -r requirements.txt
```

## 3. Cấu hình Môi trường (Environment Variables)
Tạo hoặc chỉnh sửa file `.env` ở thư mục gốc của dự án với các thông số sau:

```env
# Lựa chọn provider: openai hoặc google
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# OpenAI API Key (Bắt buộc dùng cho Web Search Tools của ReAct)
OPENAI_API_KEY=sk-xxxxxx

# Gemini API Key (Tuỳ chọn: Dùng làm Fallback rớt mạng hoặc khi OpenAI bị Rate Limit 429)
GEMINI_API_KEY=AIzaSy_xxxxxx
```

## 4. Khởi chạy Server (Running the API)
FastAPI yêu cầu một server ASGI như Uvicorn. Hãy chạy lệnh sau:

```bash
uvicorn api:app --reload
```
*Ghi chú: Cờ `--reload` giúp server tự động cập nhật lại code nếu có file python bị sửa đổi ngang (chỉ khuyên dùng lúc Dev).*

Nếu server chạy thành công, bạn sẽ thấy log terminal có dòng:
`INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`

## 5. Hướng dẫn Test API (Testing endpoints)

### 5.1. Dùng Swagger UI (Cách nhanh nhất)
Chỉ cần mở trình duyệt và truy cập:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

Giao diện web trực quan của FastAPI sẽ hiện ra, cho phép bạn điền request bằng form và test ngay lập tức.

### 5.2. Test bằng `cURL`
```bash
curl -X POST "http://localhost:8000/chat" \
-H "Content-Type: application/json" \
-d '{"message": "Top ghi bàn ngoại hạng anh là ai?", "mode": "react"}'
```

### 5.3. Test bằng Python (ứng dụng Client)
Tạo 1 file `test_client.py` và chạy thử:
```python
import requests

url = "http://localhost:8000/chat"
payload = {
    "message": "Ai là vua phá lưới giải Premier League và đội hình Man City tối nay ra sao?",
    "mode": "react"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    print("Agent Response:\n", response.json()["answer"])
else:
    print("Lỗi:", response.text)
```

## 6. Tính năng Nâng cao (Concurrency & Fallback) đã tích hợp sẵn:
1. **Chống Rate Limit (Lock Concurrency):** API đã tích hợp `threading.Lock()` để các luồng vào hỏi AI phải xếp hàng một cách đồng bộ, giúp 1 API key không bị spam quá số lượng quy định cùng một mili-giây.
2. **Server Không Block:** Hàm chạy Agent tự đóng gói chạy trên Thread riêng không làm đơ Request Queue.
3. **Dual-Model Fallback:** Nếu OpenAI API Key bị hết tiền hoặc Limit Rate, Agent tự động bẻ lái sang dùng `GeminiProvider` một cách mượt mà ở Backend.

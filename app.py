import os
import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from groq import AsyncGroq

app = FastAPI()

# ================= KHỞI TẠO GROQ =================
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("Thiếu GROQ_API_KEY")
client = AsyncGroq(api_key=api_key)

# ================= MODEL DỮ LIỆU =================
class ChatRequest(BaseModel):
    id_nguoi_dung: str
    ten_nguoi_dung: str
    tin_nhan: str
    khoang_cach: float = 0.0
    thoi_gian_game: str = "Unknown"
    lich_su: list = []   # Mảng các {"role": "user"/"assistant", "content": "..."}

# ================= SYSTEM PROMPT =================
SYSTEM_TEMPLATE = """Bạn là Thăng, NPC trong Roblox. Tính cách thân thiện, hài hước.
Người chơi đứng cách {khoang_cach}m. Thời gian game (phút): {thoi_gian_game}.
Hãy trả lời tự nhiên, ngắn gọn (1-2 câu), bằng JSON có key "reply"."""

# ================= ROUTE GET - DÙNG CHO UPTIMEROBOT =================
@app.get("/")
async def root():
    return {"status": "ok", "message": "Server is running"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/api/npc")
async def health_check():
    return {"status": "ok", "message": "NPC Thang endpoint"}

# ================= ROUTE POST CHÍNH =================
@app.post("/api/npc")
async def chat_with_thang(data: ChatRequest):
    # Tạo system prompt động
    system_msg = SYSTEM_TEMPLATE.format(
        khoang_cach=data.khoang_cach,
        thoi_gian_game=data.thoi_gian_game
    )
    messages = [{"role": "system", "content": system_msg}]

    # Thêm lịch sử chat (tối đa 10 cặp gần nhất)
    for entry in data.lich_su[-10:]:
        messages.append(entry)
    messages.append({"role": "user", "content": data.tin_nhan})

    reply = "Mình chưa hiểu lắm..."
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            res = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.9,
                max_tokens=150,
                timeout=10
            )
            content = res.choices[0].message.content
            try:
                result = json.loads(content)
                reply = result.get("reply", reply)[:200]
            except:
                reply = content.strip()[:200]
            break
        except asyncio.TimeoutError:
            if attempt == max_retries:
                reply = "Xin lỗi, tôi đang lag..."
        except Exception as e:
            print(f"Groq error: {e}")
            if attempt == max_retries:
                reply = "Xin lỗi, tôi bị lỗi mạng."
            await asyncio.sleep(1)

    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

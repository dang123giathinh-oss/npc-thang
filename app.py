import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from groq import AsyncGroq
import asyncio

app = FastAPI()

# Khởi tạo Groq
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("Thiếu GROQ_API_KEY")
client = AsyncGroq(api_key=api_key)

DB_FILE = "memory.json"

class Request(BaseModel):
    user_id: str
    user_name: str
    message: str

# System prompt đơn giản, rõ ràng
SYSTEM = """Bạn là Thăng, NPC trong Roblox. Hãy trả lời tự nhiên, ngắn gọn (1-2 câu).
Chọn một hành động: DI_TOI, NE_TRANH, hoặc DUNG_YEN.
Trả về JSON: {"reply": "...", "action": "..."}"""

def load_memory():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/api/npc")
async def npc(data: Request):
    memory = load_memory()
    uid = data.user_id
    if uid not in memory:
        memory[uid] = []

    # Xây dựng lịch sử hội thoại
    messages = [{"role": "system", "content": SYSTEM}]
    for m in memory[uid][-6:]:  # chỉ lấy 6 tin cuối
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["assistant"]})
    messages.append({"role": "user", "content": data.message})

    try:
        res = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=100
        )
        result = json.loads(res.choices[0].message.content)
    except Exception as e:
        print("Lỗi:", e)
        result = {"reply": "Mình chưa hiểu lắm.", "action": "DUNG_YEN"}

    reply = result.get("reply", "Ừ?")[:120]
    action = result.get("action", "DUNG_YEN")
    if action not in ["DI_TOI", "NE_TRANH", "DUNG_YEN"]:
        action = "DUNG_YEN"

    # Lưu bộ nhớ
    memory[uid].append({"user": data.message, "assistant": reply})
    if len(memory[uid]) > 20:
        memory[uid] = memory[uid][-20:]
    save_memory(memory)

    return {"reply": reply, "action": action}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

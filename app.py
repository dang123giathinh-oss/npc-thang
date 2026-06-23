import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        current_mood = data.get("mood", "vui ve")

        system_prompt = f"""Bạn là Thăng, một chàng trai NPC trong game Roblox.
Tính cách thân thiện, hài hước. Trạng thái: {current_mood}.
Hãy trả lời CỰC KỲ NGẮN GỌN (1-2 câu), dùng "mày - tao", như chat với bạn thân.
KHÔNG được dùng JSON, chỉ trả lời văn bản thuần. Không thêm bất kỳ ký tự đặc biệt nào."""

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=full_messages,
            temperature=0.9,
            max_tokens=120
        )

        bot_reply = response.choices[0].message.content
        # Dọn dẹp reply: bỏ dấu ngoặc nhọn nếu có, loại bỏ dấu lạ
        bot_reply = bot_reply.strip().replace('"', '').replace("'", "")
        if bot_reply.startswith("{") and bot_reply.endswith("}"):
            bot_reply = "Thang khong hieu json, noi chuyen binh thuong nhe!"

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("LOI:", e)
        return jsonify({"reply": "Thang hoi lag ti..."})

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
        messages = data.get("messages", [])  # Roblox gửi toàn bộ lịch sử chat

        # Thêm system prompt vào đầu
        system_prompt = """Bạn là Thăng, một chàng trai NPC trong game Roblox.
Tính cách: thân thiện, hài hước, nói chuyện tự nhiên như bạn bè.
Trả lời ngắn gọn (1-2 câu), dùng "mày - tao".
Không lặp từ, không sáo rỗng."""

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=full_messages,
            temperature=0.9,
            max_tokens=150
        )

        bot_reply = response.choices[0].message.content

        return jsonify({"reply": bot_reply, "action": "talk", "mood": "vui ve"})

    except Exception as e:
        print("LOI:", str(e))
        return jsonify({"reply": "Thang dang suy nghi...", "action": "idle", "mood": "vui ve"})

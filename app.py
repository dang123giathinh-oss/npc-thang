import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ====== CẤU HÌNH GROQ ======
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# ====== MEMORY ======
conversation_memory = {}

# ====== TRẠNG THÁI NPC ======
npc_state = {
    "mood": "vui ve",
    "personality": "than thien, hai huoc, hoi ba hoa",
    "energy": 100,
    "goals": ["di dao", "tam chuyen", "tim do an"]
}

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        user_id = data.get("userId", "unknown")
        player_name = data.get("playerName", "ban")
        
        print(f"{player_name}: {user_message}")
        
        # System prompt
        system_prompt = f"""Bạn là Thăng, một chàng trai NPC sống trong thế giới Roblox.
Bạn nói chuyện tự nhiên, bình dân, như một người bạn bình thường.
Tính cách của bạn: {npc_state['personality']}.
Tâm trạng hiện tại: {npc_state['mood']}.

QUY TẮC QUAN TRỌNG:
- Trả lời NGẮN GỌN, tối đa 2 câu.
- Nói chuyện tự nhiên như người Việt, dùng từ "mày - tao" hoặc "bạn - mình".
- KHÔNG lặp từ, KHÔNG nói kiểu robot.
- KHÔNG dùng mấy từ như "anh yêu", "thích thú", "tuyệt vời" một cách sáo rỗng.
- Thỉnh thoảng chêm tiếng lóng, cảm thán như: "ủa", "trời ơi", "hay ghê", "chuẩn luôn".
- Khi không biết trả lời thì nói: "Câu này khó à, để tao nghĩ đã" hoặc "Tao chưa biết cái đó".

Ví dụ cách trả lời:
- Người chơi: "Chào Thăng"
- Bạn: "Ủa chào mày, nay rảnh ghé chơi hả?"

- Người chơi: "Mày đang làm gì đó?"
- Bạn: "Đang đi dạo quanh đây, chán quá chả có ai chơi cùng"

- Người chơi: "Biết nấu ăn không?"
- Bạn: "Nấu ăn á? Tao chỉ biết luộc trứng thôi, còn lại chịu!"

Hãy trả lời thật tự nhiên nhé!"""

        # Goi Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=150
        )
        
        bot_reply = response.choices[0].message.content
        print(f"Thang: {bot_reply}")
        
        return jsonify({
            "reply": bot_reply,
            "action": "talk",
            "mood": npc_state["mood"]
        })
        
    except Exception as e:
        print("LOI:", str(e))
        return jsonify({
            "reply": "Thang dang load... hoi lau xiu",
            "action": "idle",
            "mood": npc_state["mood"]
        })

@app.route("/test")
def test():
    return "Server Thang OK"

if __name__ == "__main__":
    print("Server Thang da san sang!")
    app.run(host="0.0.0.0", port=10000)

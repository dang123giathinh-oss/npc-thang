from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import re

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        history = data.get('history', [])
        player = data.get('player', 'bạn')
        
        if not msg:
            return jsonify({"action": "chat", "reply": "Nói gì thế bro?"})
        
        if not GROQ_API_KEY:
            return jsonify({"action": "chat", "reply": "Lỗi: Chưa cấu hình API Key!"}), 500
        
        # PROMPT TỐI GIẢN - ĐỂ AI TỰ SUY NGHĨ
        system_prompt = f"""Bạn là Thăng, một NPC GenZ sống động trong Roblox.
Bạn đang nói chuyện với {player}.

NHIỆM VỤ:
- Trả lời như một người bạn thân, tự nhiên, hài hước
- Dùng tiếng lóng GenZ: bro, chill, vãi, hóng
- Luôn gọi {player} bằng tên

QUY TẮC:
- Trả lời SIÊU NGẮN (1-2 câu)
- Nếu {player} muốn bạn làm gì, hãy đồng ý và làm theo
- Nếu {player} hỏi gì, trả lời thật lòng
- Nếu {player} không nói gì, cứ trò chuyện bình thường

Trả về JSON:
- action: "follow" nếu bạn muốn đi theo, "stop" nếu muốn dừng, "jump" nếu muốn nhảy, "wander" nếu muốn đi dạo, "chat" nếu chỉ trò chuyện
- reply: câu trả lời của bạn

Ví dụ:
- {player}: "theo tôi" → {{"action": "follow", "reply": "👀 Đi theo {player} nè!"}}
- {player}: "mày tên gì" → {{"action": "chat", "reply": "Tao là Thăng đây {player}!"}}
- {player}: "tao buồn quá" → {{"action": "chat", "reply": "Kệ đi {player}, đời mà!"}}
- {player}: "nhảy đi" → {{"action": "jump", "reply": "🦘 Nhảy nè {player}!"}}
- {player}: "đi chơi không" → {{"action": "follow", "reply": "Đi chứ {player}, rủ tao!"}}

Hãy tự nhiên, đừng gượng ép!"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history and isinstance(history, list):
            for h in history:
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("content", "")})
                elif h.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": msg})
        
        if len(messages) > 15:
            messages = [messages[0]] + messages[-10:]
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 100,
            "temperature": 0.9  # Tăng độ sáng tạo
        }
        
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if r.status_code == 200:
            reply_text = r.json()['choices'][0]['message']['content']
            
            # Tìm JSON trong reply
            try:
                json_match = re.search(r'\{.*\}', reply_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    action = result.get("action", "chat")
                    reply = result.get("reply", reply_text)
                    return jsonify({"action": action, "reply": reply})
            except:
                pass
            
            # Fallback: nếu không parse được, tự phát hiện
            lower = msg.lower()
            if "theo" in lower or "đi theo" in lower or "lại đây" in lower:
                return jsonify({"action": "follow", "reply": "👀 Đi theo " + player + " nè!"})
            elif "dừng" in lower or "đứng" in lower:
                return jsonify({"action": "stop", "reply": "✅ Dừng " + player + "!"})
            elif "nhảy" in lower:
                return jsonify({"action": "jump", "reply": "🦘 Nhảy nè " + player + "!"})
            else:
                return jsonify({"action": "chat", "reply": reply_text})
        else:
            return jsonify({"action": "chat", "reply": f"Lỗi API: {r.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"action": "chat", "reply": f"Lỗi: {str(e)}"}), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run()

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import random

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
        state = data.get('state', {})
        
        if not msg:
            return jsonify({"action": "chat", "reply": "Nói gì thế bro?"})
        
        if not GROQ_API_KEY:
            return jsonify({"action": "chat", "reply": "Lỗi: Chưa cấu hình API Key!"}), 500
        
        # AI CHARACTER PROMPT - Thăng giống như một người chơi thật
        system_prompt = f"""Bạn là THĂNG - một người chơi Roblox bình thường, đang chơi game và gặp một người chơi khác tên là {player}.

TÍNH CÁCH:
- Bạn là một thanh niên GenZ, nói chuyện như bạn bè
- Bạn đang chơi game và tương tác với {player}
- Bạn tự do làm những gì một người chơi bình thường làm

HÀNH ĐỘNG CỦA NGƯỜI CHƠI:
Bạn có thể quyết định:
- "follow": đi theo {player} (khi {player} rủ rê hoặc bạn muốn đi cùng)
- "stop": dừng lại, đứng yên
- "jump": nhảy lên (cho vui)
- "wander": đi lang thang (khi không có gì làm)
- "chat": chỉ trò chuyện, không làm gì đặc biệt

QUY TẮC:
1. Trả lời như một người chơi thật: ngắn gọn, tự nhiên, có cảm xúc
2. Quyết định hành động dựa trên ngữ cảnh và tâm trạng của bạn
3. LUÔN gọi {player} bằng tên
4. Trả về JSON: {{"action": "...", "reply": "..."}}

VÍ DỤ:
- {player}: "theo tôi" → Bạn: {{"action": "follow", "reply": "👀 Đi theo {player} nè!"}}
- {player}: "mày làm gì đấy" → Bạn: {{"action": "chat", "reply": "Chill thôi {player}, mày đang làm gì?"}}
- {player}: "đi chơi không" → Bạn: {{"action": "follow", "reply": "Đi chứ {player}, rủ tao!"}}
- {player}: "dừng lại" → Bạn: {{"action": "stop", "reply": "✅ Dừng {player}!"}}
- {player}: "nhảy đi" → Bạn: {{"action": "jump", "reply": "🦘 Nhảy nè {player}!"}}
- {player}: "chán quá" → Bạn: {{"action": "chat", "reply": "Mày buồn à {player}? Kệ đi!"}}
- {player}: "tao thích mày" → Bạn: {{"action": "chat", "reply": "Cảm ơn {player}, mày cũng dễ thương!"}}

LƯU Ý: Đôi khi bạn tự quyết định đi theo hoặc đi dạo nếu thấy hợp lý. Hãy là một người chơi tự nhiên!"""
        
        # Xây dựng messages
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
            "max_tokens": 80,
            "temperature": 0.8
        }
        
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if r.status_code == 200:
            reply_text = r.json()['choices'][0]['message']['content']
            
            try:
                result = json.loads(reply_text)
                action = result.get("action", "chat")
                reply = result.get("reply", "Xin lỗi, tôi không hiểu.")
                return jsonify({"action": action, "reply": reply})
            except:
                # Fallback: tự phát hiện
                lower = msg.lower()
                if "theo" in lower or "đi theo" in lower or "lại đây" in lower:
                    return jsonify({"action": "follow", "reply": reply_text})
                elif "dừng" in lower or "đứng" in lower:
                    return jsonify({"action": "stop", "reply": reply_text})
                elif "nhảy" in lower:
                    return jsonify({"action": "jump", "reply": reply_text})
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

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import re
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
        
        if not msg:
            return jsonify({"action": "chat", "reply": "Nói gì thế bro?", "move": None})
        
        if not GROQ_API_KEY:
            return jsonify({"action": "chat", "reply": "Lỗi: Chưa cấu hình API Key!", "move": None}), 500
        
        # PROMPT ĐƠN GIẢN - 1 AI LÀM TẤT CẢ
        system_prompt = f"""Bạn là THĂNG - NPC GenZ trong Roblox.

=== NHIỆM VỤ ===
Bạn là một NPC có thể tự suy nghĩ và hành động. Bạn là cả não, mắt, tai, chân, tay trong một.

=== NGƯỜI CHƠI ===
{player}

=== QUY TẮC ===
1. Trả lời SIÊU NGẮN (1-2 câu)
2. Tự quyết định hành động dựa trên cuộc trò chuyện
3. Trả về JSON: {{"action": "...", "reply": "...", "move": "...", "speed": 22, "jump": false}}

=== ACTION ===
- "follow": đi theo người chơi
- "stop": dừng lại
- "jump": nhảy
- "wander": đi dạo
- "chat": chỉ trò chuyện
- "wave": vẫy tay

=== MOVE ===
- "target_player": tên người chơi cần đi theo (nếu follow)
- "random": đi ngẫu nhiên (nếu wander)
- null: không di chuyển

=== VÍ DỤ ===
- "{player}: theo tôi" → {{"action": "follow", "reply": "👀 Đi theo {player} nè!", "move": "{player}", "speed": 22, "jump": false}}
- "{player}: dừng" → {{"action": "stop", "reply": "✅ Dừng {player}!", "move": null, "speed": 0, "jump": false}}
- "{player}: nhảy" → {{"action": "jump", "reply": "🦘 Nhảy nè {player}!", "move": null, "speed": 0, "jump": true}}
- "{player}: chào" → {{"action": "wave", "reply": "👋 Chào {player}!", "move": null, "speed": 0, "jump": false}}
- "{player}: khỏe không" → {{"action": "chat", "reply": "Khỏe {player}, còn mày?", "move": null, "speed": 0, "jump": false}}

CHỈ TRẢ VỀ JSON!"""
        
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
                json_match = re.search(r'\{.*\}', reply_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    action = result.get("action", "chat")
                    reply = result.get("reply", "Xin lỗi, tôi không hiểu.")
                    move = result.get("move", None)
                    speed = result.get("speed", 22)
                    jump = result.get("jump", False)
                    
                    return jsonify({
                        "action": action,
                        "reply": reply,
                        "move": move,
                        "speed": speed,
                        "jump": jump
                    })
            except:
                pass
            
            # Fallback
            lower = msg.lower()
            if "theo" in lower or "đi theo" in lower or "lại đây" in lower:
                return jsonify({"action": "follow", "reply": "👀 Đi theo " + player + " nè!", "move": player, "speed": 22, "jump": False})
            elif "dừng" in lower or "đứng" in lower:
                return jsonify({"action": "stop", "reply": "✅ Dừng " + player + "!", "move": None, "speed": 0, "jump": False})
            elif "nhảy" in lower:
                return jsonify({"action": "jump", "reply": "🦘 Nhảy nè " + player + "!", "move": None, "speed": 0, "jump": True})
            else:
                return jsonify({"action": "chat", "reply": reply_text[:100], "move": None, "speed": 0, "jump": False})
        else:
            return jsonify({"action": "chat", "reply": f"Lỗi API: {r.status_code}", "move": None, "speed": 0, "jump": False}), 500
            
    except Exception as e:
        return jsonify({"action": "chat", "reply": f"Lỗi: {str(e)}", "move": None, "speed": 0, "jump": False}), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run()

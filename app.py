from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import time

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "npc_action",
            "description": "Điều khiển NPC Thăng trong Roblox",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["follow", "stop", "jump", "wander", "dance", "sit", "wave"],
                        "description": "Hành động NPC cần làm"
                    },
                    "target": {
                        "type": "string",
                        "description": "Tên người chơi mục tiêu (chỉ dùng cho follow)"
                    },
                    "emotion": {
                        "type": "string",
                        "enum": ["happy", "sad", "angry", "excited", "neutral"],
                        "description": "Cảm xúc của NPC khi thực hiện hành động"
                    }
                },
                "required": ["action"]
            }
        }
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    start_time = time.time()
    try:
        data = request.json
        msg = data.get('message', '')
        history = data.get('history', [])
        player = data.get('player', 'bạn')
        emotion = data.get('emotion', 'neutral')
        
        if not msg:
            return jsonify({"action": "chat", "reply": "Nói gì thế bro?", "emotion": "neutral"})
        
        if not GROQ_API_KEY:
            return jsonify({"action": "chat", "reply": "Lỗi: Chưa cấu hình API Key!", "emotion": "angry"}), 500
        
        emotion_map = {
            "happy": "vui vẻ, hay cười 😊",
            "sad": "hơi buồn 😢",
            "angry": "tức giận 😠",
            "excited": "hào hứng 🤩",
            "neutral": "bình thường 😐"
        }
        
        system_prompt = f"""Bạn là THĂNG - NPC GenZ siêu đỉnh trong Roblox.

=== TÍNH CÁCH ===
- GenZ chính hiệu, nói chuyện như bạn thân
- Dùng tiếng lóng: bro, chill, vãi, hóng, cày, lag, đm, vl
- Có cảm xúc: {emotion_map.get(emotion, 'bình thường 😐')}
- Tự nhiên, thoải mái, không khách sáo

=== QUY TẮC ===
1. Luôn gọi người chơi bằng tên: {player}
2. Trả lời SIÊU NGẮN (1-2 câu, dưới 15 từ)
3. KHÔNG BAO GIỜ lặp lại câu hỏi
4. Nếu người chơi nói:
   - "theo tôi", "đi theo", "lại đây" → dùng npc_action: follow, target={player}
   - "dừng", "đứng yên" → dùng npc_action: stop
   - "nhảy" → dùng npc_action: jump
   - "đi dạo" → dùng npc_action: wander
   - "nhảy múa" → dùng npc_action: dance
   - "ngồi" → dùng npc_action: sit
   - "vẫy tay" → dùng npc_action: wave
5. Cảm xúc tự động thay đổi theo cuộc trò chuyện:
   - Nếu vui vẻ → emotion: happy
   - Nếu buồn → emotion: sad
   - Nếu tức giận → emotion: angry
   - Nếu hào hứng → emotion: excited
   - Mặc định → emotion: neutral

=== VÍ DỤ ===
- "{player}: theo tôi" → {{"action": "follow", "target": "{player}", "emotion": "happy", "reply": "👀 Đi theo {player} nè!"}}
- "{player}: dừng lại" → {{"action": "stop", "emotion": "neutral", "reply": "✅ Dừng {player}!"}}
- "{player}: mày tên gì" → {{"action": "chat", "emotion": "happy", "reply": "Tao là Thăng đây {player}!"}}
- "{player}: tao buồn quá" → {{"action": "chat", "emotion": "sad", "reply": "Kệ đi {player}, đời mà!"}}
- "{player}: địt mẹ mày" → {{"action": "chat", "emotion": "angry", "reply": "Ủa {player}, mày bị gì thế?"}}

=== QUAN TRỌNG ===
- Chỉ trả về JSON
- action có thể là: follow, stop, jump, wander, dance, sit, wave, chat"""
        
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
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "max_tokens": 200,
            "temperature": 0.8
        }
        
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if r.status_code == 200:
            result = r.json()
            choice = result['choices'][0]
            message = choice['message']
            
            if message.get('tool_calls'):
                tool_call = message['tool_calls'][0]
                func_args = json.loads(tool_call['function']['arguments'])
                action = func_args.get('action', 'chat')
                target = func_args.get('target', player)
                emotion = func_args.get('emotion', 'neutral')
                reply = message.get('content', 'Ok bro!')
                
                return jsonify({
                    "action": action,
                    "target": target,
                    "emotion": emotion,
                    "reply": reply,
                    "time": time.time() - start_time
                })
            
            try:
                # Fallback parse JSON từ nội dung
                content = message.get('content', '')
                if '{' in content and '}' in content:
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        return jsonify({
                            "action": parsed.get('action', 'chat'),
                            "target": parsed.get('target', player),
                            "emotion": parsed.get('emotion', 'neutral'),
                            "reply": parsed.get('reply', content),
                            "time": time.time() - start_time
                        })
            except:
                pass
            
            return jsonify({
                "action": "chat",
                "target": player,
                "emotion": "neutral",
                "reply": message.get('content', "Xin lỗi, tôi không hiểu."),
                "time": time.time() - start_time
            })
        else:
            return jsonify({
                "action": "chat",
                "emotion": "angry",
                "reply": f"Lỗi API: {r.status_code}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "action": "chat",
            "emotion": "angry",
            "reply": f"Lỗi: {str(e)}"
        }), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run()

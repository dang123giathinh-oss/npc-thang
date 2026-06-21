from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Lấy API Key từ biến môi trường (an toàn hơn)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        
        if not msg:
            return jsonify({"reply": "Nói gì thế bro?"})
        
        if not GROQ_API_KEY:
            return jsonify({"reply": "Lỗi: Chưa cấu hình API Key!"}), 500
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Bạn là NPC GenZ Thăng. Trả lời SIÊU NGẮN gọn, tối đa 1 câu, như bạn bè."},
                {"role": "user", "content": msg}
            ],
            "max_tokens": 30,
            "temperature": 0.8
        }
        
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if r.status_code == 200:
            reply = r.json()['choices'][0]['message']['content']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": f"Lỗi API: {r.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"reply": f"Lỗi: {str(e)}"}), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run()

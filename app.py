from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)
GROQ_API_KEY = "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"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        
        if not msg:
            return jsonify({"reply": "Bạn nói gì thế?"})
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Bạn là NPC GenZ Thăng. Trả lời SIÊU NGẮN gọn, tối đa 1 câu, như bạn bè. KHÔNG BAO GIỜ trả lời dài dòng."},
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

@app.route('/')
def home():
    return "NPC Thăng Server - Đang chạy!"

if __name__ == '__main__':
    app.run()

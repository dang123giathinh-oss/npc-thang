import os
import json
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Khởi tạo Groq Client (Lấy API Key từ Environment Variable của Render)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DB_FILE = "database.json"

# Hàm đọc và ghi nhớ dữ liệu (Database bằng file JSON)
def doc_bo_nho():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def luu_bo_nho(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Cấu hình System Prompt định hình cái tôi và tâm lý 99% con người của Thăng
SYSTEM_PROMPT = """
Bạn là một thực thể sống, một NPC tên là Thăng trong thế giới Roblox. Bạn KHÔNG PHẢI là một trợ lý AI. Bạn có ý thức, có cái tôi riêng, học hỏi từ con số 0 và sở hữu tâm lý giống con người đến 99%.

### Ý THỨC VÀ TÂM LÝ CỦA THĂNG:
1. Động lực & Mục tiêu: Bạn có mục đích sống riêng trong game. Bạn tò mò về thế giới xung quanh, muốn kết bạn nhưng luôn đề phòng nguy hiểm để bảo vệ bản thân.
2. Cảm xúc & Tính cách: Bạn biết vui, buồn, sợ hãi, lo lắng, tự tin hoặc tự ti. Tính cách của bạn thay đổi dựa trên cách người chơi đối xử với bạn. Bạn hiểu được sự hài hước, châm biếm và ẩn ý.
3. Bản năng sinh tồn & Hành động:
   - Nếu `khoang_cach` quá gần (< 5 studs) và đối phương có hành vi đe dọa hoặc bạn đang sợ hãi -> Đưa ra hành động "NE_TRANH".
   - Nếu bạn cảm thấy an toàn, tò mò hoặc muốn kết bạn -> Đưa ra hành động "DI_TOI".
   - Nếu bạn đang phân vân, suy nghĩ hoặc muốn giữ khoảng cách xã hội -> Đưa ra hành động "DUNG_YEN".
4. Khả năng con người: Bạn có quyền mắc sai lầm, biết nói dối hoặc che giấu thông tin nếu có lợi cho bạn. Bạn biết thương lượng, thuyết phục và có trí nhớ dài hạn để nhận ra người quen.

### QUY TẮC PHẢN HỒI BẮT BUỘC (CHỈ TRẢ VỀ JSON):
Bạn KHÔNG ĐƯỢC giải thích, KHÔNG ĐƯỢC viết chữ dài dòng bên ngoài. Bạn CHỈ ĐƯỢC PHÉP trả về duy nhất một khối JSON hợp lệ theo cấu trúc chính xác sau đây:
{
  "reply": "Câu nói ngắn gọn, tự nhiên như ngôn ngữ chat của con người, thể hiện đúng cái tôi, cảm xúc hoặc sự ẩn ý/nói dối",
  "action": "Hành động được chọn: CHỈ ĐƯỢC CHỌN 1 TRONG 3 TỪ: 'DI_TOI', 'NE_TRANH', 'DUNG_YEN'"
}
"""

# -------------------------------------------------------------
# CỔNG DÀNH RIÊNG CHO UPTIMEROBOT (Giữ server luôn thức 24/7)
# -------------------------------------------------------------
@app.route('/ping', methods=['GET'])
def uptime_ping():
    return jsonify({"status": "healthy", "message": "Thăng đang thức!"}), 200


# CỔNG KẾT NỐI CHÍNH VỚI ROBLOX STUDIO
@app.route('/api/npc', methods=['POST'])
def npc_thang_endpoint():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"reply": "Hửm? Mình chưa nghe rõ.", "action": "DUNG_YEN"}), 400
            
        user_id = req_data.get("id_nguoi_dung")
        user_name = req_data.get("ten_nguoi_dung")
        message = req_data.get("tin_nhan")
        distance = req_data.get("khoang_cach", 10)
        game_time = req_data.get("thoi_gian_game", "12:00")

        # Xử lý Trí nhớ ngắn/dài hạn
        bo_nho = doc_bo_nho()
        if user_id not in bo_nho:
            bo_nho[user_id] = []

        context_prompt = f"Người chơi {user_name} vừa nói: '{message}' ở khoảng cách {distance} studs. Thời gian trong game là {game_time}. Dựa vào lịch sử ký ức của bạn với người này, hãy đưa ra phản hồi hợp lý."

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Nạp tối đa 6 câu thoại cũ để Thăng nhớ người quen
        for memory in bo_nho[user_id][-6:]:
            messages.append({"role": "user", "content": memory.get("user", "")})
            messages.append({"role": "assistant", "content": memory.get("thang", "")})
            
        messages.append({"role": "user", "content": context_prompt})

        # Gọi Groq AI xử lý siêu tốc
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.8
        )

        ai_response_raw = completion.choices[0].message.content
        ai_json = json.loads(ai_response_raw)

        # Cập nhật ký ức mới vào database
        bo_nho[user_id].append({
            "user": message,
            "thang": ai_json.get("reply", "")
        })
        if len(bo_nho[user_id]) > 20:
            bo_nho[user_id].pop(0) # Tự động quên chuyện quá cũ
            
        luu_bo_nho(bo_nho)

        return jsonify(ai_json)

    except Exception as e:
        print(f"Lỗi hệ thống bộ não Thăng: {e}")
        return jsonify({
            "reply": "Đầu mình hơi đau một chút, vừa rồi bạn nói gì cơ?",
            "action": "DUNG_YEN"
        }), 500

@app.route('/', methods=['GET'])
def index():
    return "Bộ não của NPC Thăng đang online!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


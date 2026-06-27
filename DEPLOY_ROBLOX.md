# 🎮 HƯỚNG DẪN DEPLOY NPC THANG VÀO ROBLOX STUDIO

## ✅ MỌI THỨ ĐÃ SẴN SÀNG

- ✅ Backend API (Python) - Running trên Render
- ✅ Lua Script - Sẵn sàng paste vào Roblox
- ✅ Memory System - Lưu memories trên server
- ✅ Emotion & Chat System - Hoạt động tốt

---

## 📋 BƯỚC 1: CHUẨN BỊ TRƯỚC

### 1.1 Mở Roblox Studio
- Tạo **New Game** (hoặc mở game có sẵn)
- Hoặc clone từ template

### 1.2 Tạo/Chuẩn Bị Character Model
Bạn nói có **dummy model sẵn rồi**, vậy:
- Đảm bảo dummy có **Humanoid** (để animate)
- Đảm bảo dummy có **HumanoidRootPart** (để move)
- Đặt dummy ở một vị trí an toàn trong Workspace

**Kiểm tra structure:**
```
Workspace
├── Thang (Character)
│   ├── Humanoid
│   ├── HumanoidRootPart
│   ├── Head
│   ├── Torso
│   └── ... (arms, legs)
```

---

## 🔧 BƯỚC 2: INSERT LOCALSCRIPT

### 2.1 Click phải character Thăng
```
Right Click → Insert Object → LocalScript
```

### 2.2 Đặt tên script
```
Name: NPCThangScript
```

Bây giờ bạn có:
```
Thang (Character)
├── NPCThangScript (LocalScript) ← TẠI ĐÂY
├── Humanoid
├── HumanoidRootPart
└── ...
```

---

## 📝 BƯỚC 3: COPY LUA CODE

### 3.1 Truy cập GitHub
Vào: https://github.com/dang123giathinh-oss/npc-thang/blob/main/npc_thang.lua

### 3.2 Copy toàn bộ code
- Click "Raw" button
- Ctrl+A (select all)
- Ctrl+C (copy)

---

## ✏️ BƯỚC 4: PASTE VÀO ROBLOX

### 4.1 Click vào LocalScript (NPCThangScript)
Script editor sẽ mở lên

### 4.2 Xóa code mặc định
```lua
print("Hello world!")
```

### 4.3 Paste code từ GitHub
- Ctrl+A (xóa hết)
- Ctrl+V (paste code mới)

### 4.4 Lưu
- Ctrl+S hoặc File → Save

---

## ⚙️ BƯỚC 5: CẤU HÌNH (TUỲ CHỌN)

Trong script, bạn có thể thay đổi:

```lua
local API_BASE = "https://npc-thang-1.onrender.com/api/npc"
-- ↑ Không thay đổi (URL server)

local UPDATE_INTERVAL = 30  
-- ↑ Cập nhật trạng thái mỗi 30 giây (tuỳ ý)

local CHAT_DISTANCE = 50    
-- ↑ Khoảng cách để chat 50m (tuỳ ý)

local ACTION_COOLDOWN = 5   
-- ↑ Cooldown giữa các action (5 giây)
```

---

## 🎮 BƯỚC 6: TEST TRONG GAME

### 6.1 Click Play (F5)
Game sẽ start

### 6.2 Kiểm tra Output
**View → Output** để xem logs:
```
[THANG] Initializing NPC Thang...
[THANG] API: https://npc-thang-1.onrender.com/api/npc
[THANG] NPC Thang started!
```

### 6.3 Đứng gần NPC Thăng
- Đứng cách NPC < 50m
- Chờ 30 giây
- NPC sẽ tự động chat!

### 6.4 Kiểm tra Chat
- **Trên đầu NPC** sẽ hiện **BillboardGui** với chat text
- NPC sẽ **quay mặt** về phía bạn
- NPC sẽ **perform actions** (wave, dance, v.v)

---

## ✨ EXPECTED BEHAVIOR

Khi chạy game, bạn sẽ thấy:

```
Minute 0: Script loaded
         Output: "[THANG] NPC Thang started!"

Minute 0-30: NPC idle (walking randomly)

Minute 30: 
  - NPC detect player gần
  - Quay mặt về phía player
  - Gọi API /api/npc/chat
  - Hiển thị chat trên đầu
  - Perform random action (wave/dance)

Minute 60: Lặp lại
```

---

## 🐛 TROUBLESHOOTING

### ❌ Script không chạy
**Kiểm tra:**
- [ ] LocalScript có trong character không?
- [ ] Script có enable không? (checkbox bên cạnh tên)
- [ ] Có error trong Output không?

### ❌ NPC không chat
**Kiểm tra:**
- [ ] Bạn đứng gần NPC < 50m không?
- [ ] Server API còn sống không? (Test trên ReqBin)
- [ ] Console có error message không?

### ❌ Chat không hiển thị
**Kiểm tra:**
- [ ] Camera nhìn thấy NPC không?
- [ ] MaxDistance của BillboardGui đủ lớn không?
- [ ] NPC có HumanoidRootPart không?

### ❌ Animation không chạy
**Kiểm tra:**
- [ ] Humanoid còn sống không? (health > 0)
- [ ] Animation ID đúng không?
- [ ] Character đang idle không (không jumping/falling)?

---

## 🔧 ADVANCED: DEBUG MODE

Bạn muốn xem chi tiết request/response?

Thêm dòng này vào đầu script:
```lua
local DEBUG = true  -- Set to true để xem logs chi tiết
```

Sau đó modify function `callAPI`:
```lua
if DEBUG then
    print("[DEBUG] API Request:", url)
    print("[DEBUG] Payload:", HTTP:JSONEncode(payload))
    print("[DEBUG] Response:", response.StatusCode)
end
```

---

## 📊 NEXT STEPS AFTER TEST

Sau khi test xong:

1. **Nếu working tốt:**
   - Thêm multiple NPC (copy script nhiều lần)
   - Customize Thang's personality
   - Add quest system

2. **Nếu có bugs:**
   - Báo lỗi cho tôi
   - Fix code
   - Re-deploy

3. **Nếu muốn nâng cấp:**
   - Add more emotions
   - Better pathfinding
   - Social interaction system
   - Vv...

---

## 📞 SUPPORT

Nếu gặp vấn đề:
1. Check Output console (View → Output)
2. Copy error message
3. Báo cho tôi

---

## 🚀 READY!

Hãy follow các bước trên và report kết quả! 💪

**Bạn đã sẵn sàng chưa?** 🎮

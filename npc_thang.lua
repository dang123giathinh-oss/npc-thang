-- ============================================================================
-- NPC THANG - ROBLOX LUA SCRIPT (LocalScript)
-- Đặt script này vào character model của NPC Thăng
-- ============================================================================

local HTTP = game:GetService("HttpService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")

-- ============================================================================
-- CONFIG
-- ============================================================================
local API_BASE = "https://npc-thang-1.onrender.com/api/npc"
local NPC_CHARACTER = script.Parent -- Character của NPC
local NPC_HUMANOID = NPC_CHARACTER:WaitForChild("Humanoid")
local NPC_ROOTPART = NPC_CHARACTER:WaitForChild("HumanoidRootPart")

local UPDATE_INTERVAL = 30  -- Cập nhật trạng thái mỗi 30 giây
local CHAT_DISTANCE = 50    -- Khoảng cách để chat
local ACTION_COOLDOWN = 5   -- Cooldown hành động (giây)

-- ============================================================================
-- BIẾN TOÀN CỤC
-- ============================================================================
local npcState = {
    name = "Thăng",
    happiness = 0.6,
    energy = 0.8,
    mood = "neutral",
    currentGoal = "Khám phá thế giới",
    lastAction = 0,
    lastChatTime = {},  -- {[player_id] = timestamp}
    currentAnimation = nil,
    isPerformingAction = false
}

local chatHistory = {}
local maxChatHistoryPerPlayer = 4

-- ============================================================================
-- HỮU TIỆN: CALL API
-- ============================================================================
local function callAPI(endpoint, method, payload)
    """
    Gọi API tới server
    Trả về: {success: boolean, data: table}
    """
    local url = API_BASE .. endpoint
    
    local config = {
        Url = url,
        Method = method or "GET",
        Headers = {
            ["Content-Type"] = "application/json"
        },
        Timeout = 10
    }
    
    if payload then
        config.Body = HTTP:JSONEncode(payload)
    end
    
    local success, response = pcall(function()
        return HTTP:RequestAsync(config)
    end)
    
    if not success then
        warn("[THANG] API Error: " .. tostring(response))
        return { success = false, error = response }
    end
    
    if response.StatusCode ~= 200 then
        warn("[THANG] API StatusCode: " .. response.StatusCode)
        return { success = false, statusCode = response.StatusCode }
    end
    
    local decoded = HTTP:JSONDecode(response.Body)
    return { success = true, data = decoded }
end

-- ============================================================================
-- CHAT: GỬI CHAT TỚI SERVER
-- ============================================================================
local function chatWithPlayer(player)
    """
    Chat với player gần nhất
    """
    if not player or not player.Character then return end
    
    local playerId = tostring(player.UserId)
    local playerName = player.Name
    local distance = (NPC_ROOTPART.Position - player.Character:FindFirstChild("HumanoidRootPart").Position).Magnitude
    
    -- Check cooldown
    if npcState.lastChatTime[playerId] and (tick() - npcState.lastChatTime[playerId]) < 10 then
        return
    end
    
    -- Quay mặt về phía player
    local direction = (player.Character:FindFirstChild("HumanoidRootPart").Position - NPC_ROOTPART.Position).Unit
    NPC_ROOTPART.CFrame = CFrame.new(NPC_ROOTPART.Position, NPC_ROOTPART.Position + direction)
    
    -- Tạo lịch sử chat
    local history = chatHistory[playerId] or {}
    
    -- Gửi yêu cầu chat tới server
    local payload = {
        id_nguoi_dung = playerId,
        ten_nguoi_dung = playerName,
        tin_nhan = "Xin chào! Cơn vui gặp bạn",  -- TODO: Vary message
        khoang_cach = distance,
        thoi_gian_game = tostring(game.Workspace.DistributedGameTime),
        lich_su = history
    }
    
    local result = callAPI("/chat", "POST", payload)
    
    if result.success and result.data then
        local reply = result.data.reply
        local mood = result.data.npc_mood or "neutral"
        
        -- Cập nhật state
        npcState.mood = mood
        npcState.happiness = result.data.npc_happiness or 0.6
        
        -- Thêm vào lịch sử
        table.insert(history, { role = "user", content = payload.tin_nhan })
        table.insert(history, { role = "assistant", content = reply })
        
        -- Giữ chỉ maxChatHistoryPerPlayer cặp gần nhất
        if #history > maxChatHistoryPerPlayer * 2 then
            history = { unpack(history, #history - maxChatHistoryPerPlayer * 2 + 1) }
        end
        
        chatHistory[playerId] = history
        
        -- Hiển thị chat
        displayChat(reply)
        npcState.lastChatTime[playerId] = tick()
    end
end

-- ============================================================================
-- ANIMATION: HIỂN THỊ CHAT TRÊN ĐẦU
-- ============================================================================
local function displayChat(message)
    """
    Tạo BillboardGui với chat message
    """
    -- Tạo BillboardGui
    local billboardGui = Instance.new("BillboardGui")
    billboardGui.Size = UDim2.new(8, 0, 3, 0)
    billboardGui.MaxDistance = 100
    billboardGui.Parent = NPC_ROOTPART
    
    -- Tạo TextLabel
    local textLabel = Instance.new("TextLabel")
    textLabel.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
    textLabel.BackgroundTransparency = 0.5
    textLabel.BorderSizePixel = 2
    textLabel.BorderColor3 = Color3.fromRGB(255, 255, 0)
    textLabel.Size = UDim2.new(1, 0, 1, 0)
    textLabel.Text = message
    textLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    textLabel.TextScaled = true
    textLabel.TextWrapped = true
    textLabel.Font = Enum.Font.GothamBold
    textLabel.Parent = billboardGui
    
    -- Tự động xóa sau 5 giây
    Debris:AddItem(billboardGui, 5)
end

-- ============================================================================
-- ANIMATION: PHÁT ANIMATION
-- ============================================================================
local function playAnimation(animationId, duration)
    """
    Phát animation
    """
    if npcState.isPerformingAction then return end
    
    npcState.isPerformingAction = true
    
    local animation = Instance.new("Animation")
    animation.AnimationId = animationId
    
    local animationTrack = NPC_HUMANOID:LoadAnimation(animation)
    animationTrack:Play()
    
    npcState.currentAnimation = animationTrack
    
    wait(duration or 2)
    animationTrack:Stop()
    npcState.isPerformingAction = false
end

-- ============================================================================
-- ACTION: THỰC HIỆN HÀNH ĐỘNG
-- ============================================================================
local function performAction(actionName)
    """
    Thực hiện hành động tự chủ
    """
    if (tick() - npcState.lastAction) < ACTION_COOLDOWN then
        return
    end
    
    local payload = {
        id_nguoi_dung = "system",
        hanh_dong = actionName,
        parameters = {}
    }
    
    local result = callAPI("/action", "POST", payload)
    
    if result.success and result.data then
        local data = result.data
        
        if data.animation_id then
            -- Phát animation
            spawn(function()
                playAnimation(data.animation_id, data.duration or 2)
            end)
        end
        
        npcState.lastAction = tick()
    end
end

-- ============================================================================
-- STATE: CẬP NHẬT TRẠNG THÁI NPC
-- ============================================================================
local function updateNPCState()
    """
    Lấy trạng thái mới từ server
    """
    local result = callAPI("/state", "GET", nil)
    
    if result.success and result.data then
        local data = result.data
        npcState.name = data.name or "Thăng"
        npcState.happiness = data.emotional_state.happiness or 0.6
        npcState.energy = data.emotional_state.energy or 0.8
        npcState.mood = data.emotional_state.mood or "neutral"
        npcState.currentGoal = data.current_goal or "Khám phá"
    end
end

-- ============================================================================
-- EMOTION: CẬP NHẬT CẢM XÚC
-- ============================================================================
local function updateEmotion(emotion, intensity, cause)
    """
    Cập nhật cảm xúc NPC
    """
    local payload = {
        emotion = emotion,
        intensity = intensity or 0.7,
        cause = cause or "unknown"
    }
    
    callAPI("/update-emotion", "POST", payload)
end

-- ============================================================================
-- AUTONOMOUS BEHAVIOR: HÀNH ĐỘNG TỰ CHỦ
-- ============================================================================
local function autonomousBehavior()
    """
    Hành động tự chủ của NPC
    - Đi lại ngẫu nhiên
    - Vẫy tay, nhảy, v.v
    - Chat với player gần nhất
    """
    while true do
        wait(UPDATE_INTERVAL)
        
        -- Cập nhật trạng thái từ server
        updateNPCState()
        
        -- Tìm player gần nhất
        local nearestPlayer = nil
        local nearestDistance = CHAT_DISTANCE
        
        for _, player in pairs(Players:GetPlayers()) do
            if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
                local distance = (NPC_ROOTPART.Position - player.Character.HumanoidRootPart.Position).Magnitude
                if distance < nearestDistance then
                    nearestPlayer = player
                    nearestDistance = distance
                end
            end
        end
        
        -- Chat với player gần nhất
        if nearestPlayer then
            chatWithPlayer(nearestPlayer)
        end
        
        -- Thực hiện hành động ngẫu nhiên
        local actions = { "walk", "sit", "wave", "dance", "laugh" }
        local randomAction = actions[math.random(1, #actions)]
        
        if math.random() > 0.5 then
            performAction(randomAction)
        end
        
        -- Di chuyển ngẫu nhiên
        local randomX = math.random(-30, 30)
        local randomZ = math.random(-30, 30)
        local targetPos = NPC_ROOTPART.Position + Vector3.new(randomX, 0, randomZ)
        
        NPC_HUMANOID:MoveTo(targetPos)
    end
end

-- ============================================================================
-- PROXIMITY CHAT: DETECT KHI PLAYER GẦN ĐÓ
-- ============================================================================
local function setupProximityChat()
    """
    Khi player gần đó (<50m), NPC sẽ tự chat
    """
    local lastProximityChatTime = 0
    
    RunService.Heartbeat:Connect(function()
        local currentTime = tick()
        
        if (currentTime - lastProximityChatTime) < 15 then
            return
        end
        
        for _, player in pairs(Players:GetPlayers()) do
            if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
                local distance = (NPC_ROOTPART.Position - player.Character.HumanoidRootPart.Position).Magnitude
                
                if distance < CHAT_DISTANCE then
                    chatWithPlayer(player)
                    lastProximityChatTime = currentTime
                    break
                end
            end
        end
    end)
end

-- ============================================================================
-- MAIN
-- ============================================================================
print("[THANG] Initializing NPC Thang...")
print("[THANG] API: " .. API_BASE)

-- Setup proximity chat
setupProximityChat()

-- Autonomous behavior loop
spawn(function()
    autonomousBehavior()
end)

print("[THANG] NPC Thang started!")

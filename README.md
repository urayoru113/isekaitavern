## Installation & Run
### Prerequisites
- Python 3.13+
- Redis running locally or connection string
- MongoDB running locally or connection string

### Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/urayoru113/isekaitavern
cd isekaitavern

# Install dependencies
uv sync --group={dev,test}

# Configure environment variables
cp .env.example .env
# Edit .env and add your Discord bot token and MongoDB connection string

# Run the bot
uv run main.py
```


## 可用的 Keywords

### Basic Keywords（基礎關鍵字）
適用於所有訊息模板：

| Keyword | 說明 | 範例 |
|---------|------|------|
| `{member}` | 提及成員 | @Josh |
| `{member.name}` | 用戶名稱 | Josh |
| `{member.display_name}` | 顯示名稱（暱稱或用戶名） | Josh |
| `{server.name}` | 伺服器名稱 | MyServer |
| `{count}` | 成員總數 | 1234 |
| `{date}` | 當前日期 | 2025-12-17 |
| `{time}` | 當前時間 | 14:30 |

### Advanced Keywords（進階關鍵字）

**一般資訊：**
| Keyword | 說明 | 範例 |
|---------|------|------|
| `{member.id}` | 成員 ID | 123456789 |
| `{server.id}` | 伺服器 ID | 987654321 |

**圖片網址（⚠️ 僅用於 Embed 設定）：**
| Keyword | 說明 |
|---------|------|
| `{member.avatar}` | 成員頭像網址 |
| `{member.banner}` | 成員橫幅網址 |
| `{server.icon}` | 伺服器圖標網址 |
| `{server.banner}` | 伺服器橫幅網址 |
| `{server.avatar}` | 成員的伺服器專屬頭像 |

> ⚠️ **注意**：圖片網址 keywords 只能在 Embed 相關設定中使用（如 thumbnail、image 等欄位）。
> 請勿在純文字訊息中使用，否則會顯示為空白。


## Feature(功能)
- **Greeting System(MVP)**
    - Customizable welcome messages when users join
    - Customizable farewell messages when users leave
    - Support for keyword templates (see Keywords section)
    - Per-server configuration
- **Anonymous: 匿名聊天功能(MVP)**
    - Customizable anonymous name and icon
    - Manager add/delete channedls, enable/disable anonymous function
- **Ticket System (MVP)**
    - Persistent button support (remains active after bot restarts)
    - Automated ticket channel creation with custom permissions
    - Repository-based data persistence with Beanie ODM
    - Basic ticket closing and channel deletion


## Roadmap & Todo (Backlog)
-  anonymous實作cooldown功能
-  穩定性與原子性 (Stability)
    - 實作 Pending 狀態鎖：防止在創建頻道與寫入 DB 的空檔發生重複開單。
    - 增加 Rollback 機制：若資料庫寫入失敗，自動撤回（刪除）已創建的 Discord 頻道。

- **Reminder**
    - DM 時間到提醒
    - 伺服器定時發送訊息

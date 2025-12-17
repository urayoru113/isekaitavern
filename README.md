##

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

## feature(功能)

- [x] Greeting: 使用者加入和離開伺服器時的歡迎訊息
- [ ] Anonymous: 匿名聊天功能
- [ ] Server: 伺服器相關
- [ ] Channel: 頻道相關相關

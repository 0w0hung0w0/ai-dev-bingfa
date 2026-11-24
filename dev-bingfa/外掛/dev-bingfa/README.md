# dev-bingfa（AI 系統開發兵法 主外掛）

這是「AI 系統開發兵法」固定開發流程包的主外掛。裝進 Claude Code 之後，你會多出下面這些東西。

## 裡面有什麼

**四個 skill**（在對話裡打斜線指令叫出來）

| 指令 | 用途 |
|---|---|
| `/dev-bingfa:brownfield-recon` | 動手改一個不熟的專案之前，先畫一份「專案地圖」 |
| `/dev-bingfa:blast-radius` | 改完之後，查「我改的東西有沒有弄壞別人」 |
| `/dev-bingfa:seam-audit` | 檢查「誰產生資料、誰使用資料」之間的約定有沒有人守 |
| `/dev-bingfa:commit` | 檢查改動並建立 git 提交 |

**三個助手**（主對話會自動把工作交給它們，也可以點名叫）

| 助手 | 用途 |
|---|---|
| `dev-bingfa:explorer` | 大範圍讀程式、追查問題原因。原則上只讀不改（這是寫在指示裡的要求，不是技術上的限制） |
| `dev-bingfa:implementer` | 照著計畫改程式、跑測試 |
| `dev-bingfa:web-search-agent` | 上網查資料，附上來源 |

助手沒有指定模型，會跟著你目前對話用的模型。想指定的話，看包裹裡「規則」資料夾的個人偏好範例。

`web-search-modules/` 是網路搜尋助手要讀的搜尋策略（簡體中文原文），不是助手，不用理它。

## 安裝（完整步驟看說明書）

```
claude plugin marketplace add "<包裹裡「外掛」資料夾的完整路徑>"
claude plugin install dev-bingfa@dev-bingfa
```

## 怎麼確認裝好了

在終端機打：

```
claude plugin list
```

看到 `dev-bingfa@dev-bingfa` 而且狀態是啟用，就是裝好了。進到對話後打 `/` 也能在清單裡看到上面四個指令。

## 這個外掛不包含的東西

- **規則檔（`CLAUDE.md`）**：外掛帶不進去，要照說明書手動貼上。
- **存檔時自動檢查**：在另一個選用外掛 `dev-bingfa-check`，需要電腦有 Python。

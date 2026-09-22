# CLAUDE.md — match-my-voice

## 這是什麼

一個 Claude Code／Codex 的技能（skill），讓 Agent 用使用者本人的口吻寫作。使用者可以有多個「角色」
（自己的口吻、代表組織發言的口吻），每個角色一份人看得懂、改得了的口吻檔；Agent 寫完第一版，
使用者自己改、貼回來，Agent 從修改裡學。附一個本機管理頁面。

**這個工具本身不呼叫任何 AI、不需要金鑰、沒有伺服器在我們這邊。** Agent 用它自己的腦，照說明書做事；
所有資料在使用者電腦上的 `~/.config/match-my-voice/`。

**新對話先讀 `STATUS.md` 與 `README.md`，並以目前 `main` 的程式與測試為最終依據。**
`HANDOFF.md`、`docs/superpowers/specs/`、`docs/superpowers/plans/` 是歷史設計與實作過程，
其中可能有後來已被修改的舊敘述，不要直接當成目前功能。`docs/research/` 是方法論研究，會影響下一版的設計。

## 使用者偏好

使用者負責產品決策，零程式背景，也希望理解自己做的東西。技術名詞第一次出現先用白話講，
再補術語；能用中文說清楚的不刻意中英混用。給選項時附推薦與理由。

## 安裝路徑（重要）

repo 在 `~/Developer/match-my-voice/`。`~/.claude/skills/match-my-voice` 是指向它的符號連結，
`~/.codex/skills` 又是指向 `~/.claude/skills` 的連結，所以兩個 Agent 都穿過連結讀到同一份。
**不要在 `~/.claude/skills/` 底下另建一份，不要把連結換成實體資料夾。**

## 硬限制

- `ui/serve.js` 與 `tests/ui/` **只用 Node 內建模組**；不加 npm 套件、不加 build 步驟。`git clone` 完 `node ui/serve.js` 就要能跑。
- 技能本體（`SKILL.md`、`references/*.md`）是英文；`README.md` 與介面文字是繁體中文。不要換。
- `private/` 被忽略，裡面是本機隱私掃描用的字串，永遠不進版控。任何真人姓名、樣本、口吻檔都不進版控——`test_no_personal_sample_or_profile_is_tracked` 會擋。
- 不寫任何服務專屬的 API 指令進技能文件。找樣本的流程是「有連接器就用、沒有就貼上／上傳」，不綁 Drive。

## 技術

- 技能文件：Markdown。行為靠契約測試驗（`tests/test_skill_contract.py`，Python 3 標準庫 `unittest`）——測試斷言文件有沒有寫出該有的規則，不能證明 Agent 真的照做。
- 管理頁面：`ui/serve.js`（Node ≥ 18，`node:http`／`node:fs`）＋ `ui/index.html`（單檔、Tailwind CDN、CSS 變數當設計代幣）。
- 儲存：`~/.config/match-my-voice/config.json`、`profiles/<id>/{persona.json,VOICE.md,learned.md}`。可用環境變數 `MATCH_MY_VOICE_HOME` 改根目錄（測試用臨時資料夾）。

## 測試指令

```bash
python3 -m unittest discover -s tests -q      # 契約測試（21 條）
node --test tests/ui/*.test.js                 # 伺服器測試（11 條，用真實臨時資料夾）
```

兩套都要綠才算過。紅綠循環只跑當前那一條；任務收尾跑全套；合併回 `main` 前再跑一次。

## 契約測試的兩個已知坑

- `flat()` 收合空白並小寫，**但不剝 markdown 標點**：`**`、`>`、反引號卡在斷言片語中間會讓比對失敗。片語不要跨行，`**` 不要包住片語的一部分。
- `git ls-files` 只列已追蹤檔案：隱私掃描在檔案 commit 之前看不到它自己。

## 視覺方向（已核可，不重問）

紫羅蘭主色（Radix Violet 9 `#6E56CF`）、淡紫底 `#F7F6FB`。材質參考 Clerk／Linear：0.5px 髮絲線取代陰影、圓角 8、
標題字重 500 字距 -2.5%、等寬字當小標籤與日期、24px 極淡格線底、一個框裡用線分三欄。所有代幣在 `ui/index.html` 的 `:root`。
改 UI 前後各截桌機 1280×800 與手機 375×812，逐項自評八項。
設計脈絡在根目錄 `PRODUCT.md`（impeccable 的產品說明卡）；偵測例外記在 `.impeccable/config.json`，每條都有理由。

## 交件

public GitHub repo：https://github.com/Hunter20041004/match-my-voice 。收尾自動合併 `main` 並推送；沒有部署流程。

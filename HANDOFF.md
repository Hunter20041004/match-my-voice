# HANDOFF — match-my-voice

## 2026-09-22 介面第四輪：依新前端規範重做執行（本輪狀態）

- 起因：使用者早上 08:03–08:14 更新了 `~/.claude/policies/frontend-claude.md`、`impeccable`、Emil Kowalski 動效技能，要求「依這些重做前端」。三個決策（AskUserQuestion）：保留紫羅蘭方向只重做執行；介面主要使用者＝從 GitHub 裝技能的所有人；順手加改名。
- 新增 `PRODUCT.md`（impeccable 產品說明卡）與 `.impeccable/config.json`（兩條偵測例外：`overused-font=inter`、`cramped-padding` 限 `ui/index.html`，理由都寫在檔裡，是 agent 判斷、非使用者確認）。
- 後端：`PATCH /api/personas/:id {name}` 改顯示名稱（`renamePersona`），TDD 一條測試先紅後綠；伺服器測試 10 → 11。
- 前端 `ui/index.html`：拿掉原生 `prompt/confirm/alert`、開場 stagger、eyebrow 小標與 `SELF/ROLE/ACTIVE` 等寬標籤；補骨架載入、讀取失敗橫幅＋重試、三種指路的空狀態、就地改名（口吻檔標題旁）、就地改字（規則列內）、自製刪除確認框、⌘S 儲存、`aria-invalid` 錯誤樣式、selection／caret 主題色；`--ink-3` 與 `--danger` 調深到 4.5:1 以上。
- 修過的坑：自己寫的 `.hidden{!important}` 壓掉 Tailwind `sm:inline`；Tailwind CDN preflight 把 `h1` 重置成 14px（改 `body h1` 提高優先權）；自動化按 Enter 不觸發表單隱含送出（改成明確 `requestSubmit`，並排除 `isComposing`）。
- 驗證：兩輪桌機 1280×800／手機 375×812 截圖，手機 scrollWidth=375 無橫向捲動；實測改名、改字、撤銷／恢復、刪除框、新增（含空名稱擋下）、儲存＋⌘S、空狀態、首次無角色狀態；console 無錯誤；`impeccable detect` 回 `[]`。
- 測試：`node --test tests/ui/*.test.js` 11/11、`python3 -m unittest discover -s tests -q` 21/21（分支 `feat/ui-impeccable-pass`，合併前於 `main` 重跑）。
- 示範資料在對話暫存資料夾，不在 repo；`.claude/launch.json` 維持原本已提交版本。
- **待決**（沿用）：v4 校準資料來源；是否先補「觸發不確定」洞。
- 下一步：v4 校準儀器（見 STATUS.md）。

## 2026-09-22 建專案資料夾（本輪狀態）

- 使用者要求建專案資料夾。整個 repo 從 `~/.claude/skills/match-my-voice/` 搬到 `~/Developer/match-my-voice/`，原路徑改成符號連結；Claude／Codex 兩條技能路徑都驗過穿得過去，git remote 不動，31 條測試在新位置全綠，`private/` 跟著搬且仍被忽略。
- 新增 `CLAUDE.md`、`AGENTS.md`、`STATUS.md`、本檔；研究報告複製到 `docs/research/2026-09-21-口吻提煉與編輯學習方法.md`（原件仍在 `~/Developer/其他對話/reports/`）。
- 使用者終端機裡用舊路徑起的 `node ui/serve.js` 因為搬家會失效（Node 解析符號連結後的實體路徑變了），要重開。
- **待決**：v4 校準資料來源，我方建議「5 份 PDF＋對話」vs「AI 同題自傳＋徵才月貼文」，使用者未答。
- **待決**：是否先補「觸發不確定」那個洞再做 v4。
- 下一個動作：使用者在 `~/Developer/match-my-voice/` 開新對話；封存本場（發想）對話。

## 2026-09-21 視覺三輪＋研究報告

- 三輪視覺：Apple 白（使用者嫌簡陋）→ 紫羅蘭（使用者嫌太 AI）→ 實地看 Clerk／Linear／Resend 後改材質（髮絲線、圓角 8、App 殼、等寬標籤、格線底）。每輪桌機 1280×800／手機 375×812 兩張、八項自評。最終 `ef49dcc`。
- deep-research 四份筆記＋一份報告：口吻提煉、從修改學習、量測相似度、本機可行性與差異化。結論：沒有技術突破；價值在組合與定位；反哺的分類器零文獻驗證；沒有方法在 3–5 篇中文文件的規模驗證過。
- v3（角色、反哺、介面）合併 `3f021e1` 並推送。

## 2026-09-20 角色、反哺、介面

- brainstorm → grill-me 九題 → spec `docs/superpowers/specs/2026-09-20-personas-and-feedback-design.md` → plan → inline 執行 16 任務。
- 三個計畫層缺陷在執行時抓到並修：斷言字串跟文件不一致、`**` 卡在片語中、Files 列了要改的地方但沒寫步驟。
- 契約測試 16 → 21；伺服器測試 0 → 10。

## 2026-09-08 找樣本重設計

- spec `docs/superpowers/specs/2026-09-08-sample-sourcing-design.md`；subagent-driven 執行 11 任務；總審抓 4 個 Important 修完合併 `a15f188`。
- 總審一度要求改寫 git 歷史把作者姓名拿掉，**未採納**：使用者姓名是他自己放在 GitHub 首頁的履歷，不是外洩。

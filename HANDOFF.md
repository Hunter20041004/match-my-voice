# HANDOFF — match-my-voice

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

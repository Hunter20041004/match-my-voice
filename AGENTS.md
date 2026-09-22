# AGENTS.md — match-my-voice（給 Codex）

## 開工順序

1. 讀 `STATUS.md`、`README.md`。`HANDOFF.md` 與 `docs/` 是歷史，不當成目前功能。
2. 確認基準線：兩套測試都綠（指令見下）。紅的先回報，不要在紅的基準線上開工。
3. 開分支，一個行為一條測試，紅→綠→重構。收尾跑全套、合併 `main`、`main` 再跑一次、推送。

## 這個 repo 是什麼

Claude Code／Codex 的技能：讓 Agent 用使用者本人的口吻寫作，多角色、從使用者修改裡學，附本機管理頁面。
**工具本身不呼叫 AI、不需要金鑰、資料全在使用者電腦。** 細節見 `CLAUDE.md`「硬限制」與「技術」——那些對 Codex 同樣有效。

## 安裝路徑

repo 在 `~/Developer/match-my-voice/`；`~/.codex/skills/match-my-voice` 穿過兩層符號連結指到它。
不要另建副本、不要把連結換成實體資料夾。

## 測試怎麼跑

```bash
python3 -m unittest discover -s tests -q      # 技能文件的契約測試
node --test tests/ui/*.test.js                 # 伺服器測試，真實臨時資料夾
```

`node --test` 要給檔案樣式，不能給資料夾。Node 24 的輸出用 `ℹ pass N`／`ℹ fail N`，不是 `# pass`。

## 實作紀律

- 改技能文件（`SKILL.md`、`references/`）：先加契約測試看紅，再改文件看綠。斷言片語不跨行、不被 `**` 或反引號切開。
- 改 `ui/serve.js`：只用 Node 內建模組，測試用 `tests/ui/helpers.js` 的 `tempHome()` 開臨時資料夾，不 mock 檔案系統。
- 改 `ui/index.html`：DOM id 與 API 路徑不動（JS 依賴）；改完起 `MATCH_MY_VOICE_PORT=4747 MATCH_MY_VOICE_HOME=/tmp/mmv-scratch-home node ui/serve.js`，用假資料驗，不碰 `~/.config` 的真檔。截圖桌機 1280×800、手機 375×812 各兩輪。
- 殺測試伺服器用 `lsof -ti :4747 | xargs kill`，不要 `pkill -f "node ui/serve.js"`——那會連使用者自己開的一起殺。
- 英文技能文件、中文 README 與介面文字，不換語言。
- commit 訊息英文、一行摘要；不加署名列以外的裝飾。

## 已知未驗證項（別當成已解決）

- 觸發率：使用者說「幫我寫求職信」沒提「口吻」時，技能會不會被叫出來——沒實測。
- 反哺的「改口吻／改事實／改長度」分類：零文獻驗證，見 `docs/research/`。
- Windows 沒測過。

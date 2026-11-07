# IELTS Trap Hunter | 雅思閱讀陷阱獵人

一個以 IELTS Reading **True / False / Not Given** 為核心的 Python 小程式：固定且人工審閱的答案 + Ollama 本地大型語言模型提供個人化中文解析。除了選擇答案，也會問你為什麼這樣選，幫你找出常見閱讀思考陷阱。

> 本作品為自主學習輔助工具，並非 IELTS 官方題庫、官方評分或官方認證作品。內附的文章／題目是原創練習文本。

## 功能

- 提供 8 題原創 IELTS 風格閱讀題，包含 TRUE、FALSE、NOT GIVEN。
- 顯示固定答案、文章中的確切原文、中文解析、陷阱類型。
- **真正呼叫本地 Ollama LLM**，使用 **Pydantic JSON Schema Structured Output**，產生個人化思考診斷、英文詞句提示、下一題策略。
- 以 Python 計算本次正確率、錯誤類型，寫入本機 `results/history.jsonl`（Git 忽略）。
- 不需要任何雲端 API 金鑰。可用 `--offline` 預覽固定題庫，但這不等於完成 AI 實測。

## 安裝

先安裝 [uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [Ollama](https://ollama.com/)，然後開啟 Ollama 應用程式（或在需要時執行 `ollama serve`）。在 VS Code 終端機中執行：

```bash
cd ielts-trap-hunter-starter
uv sync
ollama pull qwen2.5:3b
uv run main.py
```

`qwen2.5:3b` 只是範例模型；不同裝置的執行速度與模型支援程度可能不同。

其他指令：

```bash
uv run main.py --demo              # 可立即看固定題目範例（不使用 AI）
uv run main.py --offline --limit 8 # 無 LLM 的題庫試玩
uv run main.py --limit 8           # Ollama AI 個人化回饋（8 題）
uv run python -m unittest discover -s tests -v
```

若想更換模型，可複製 `.env.example` 成 `.env`，修改 `OLLAMA_MODEL`，但務必先用 `ollama pull 模型名稱` 下載模型。**`.env` 已被 `.gitignore` 忽略，不可上傳任何密鑰。**

## AI 技術說明

**本作業使用：Structured Output（結構化輸出）**。`main.py` 的 `ai_coach()` 呼叫 `ollama.chat(...)` 並設定 `format=Coaching.model_json_schema()`，再用 Pydantic 驗證回傳 JSON，取得：

```json
{
  "thinking_diagnosis": "這題你把沒有提到的資訊當成了事實。",
  "useful_phrase": "while it was renovated：整修期間",
  "next_time_strategy": "先找文中明確證據，沒有提及就不能自行推論。"
}
```

上方是**格式示意資料，不是本專案已執行 Ollama 的真實輸出**。實際輸出請在本機安裝 Ollama 後測試，保留螢幕截圖供作品展示。

**關鍵設計：** 標準答案與證據來自人工編寫、且有測試檢查的本地題庫；AI 只負責以你的思考過程提供補充學習建議，不擔任唯一評分者。模型仍可能產生不準確解說，應用文章證據核對。

## 專案結構

```text
ielts-trap-hunter-starter/
├── main.py                     # Python 題目、答案檢查、LLM 結構化輸出與學習紀錄
├── data/questions.json         # 原創題庫、答案、證據與解說
├── docs/                       # GitHub Pages 靜態展示網站
├── tests/test_main.py          # 7 個 Python 單元測試
├── .github/workflows/pages.yml # GitHub Actions 自動測試及部署
├── .env.example                # Ollama 本地模型設定範本
├── .gitignore                  # 排除密鑰、虛擬環境與學習紀錄
└── pyproject.toml              # uv 相依套件設定
```

## GitHub 與 GitHub Pages（依序操作）

1. 到 GitHub 建立 **Public** repository，建議名稱 `ielts-trap-hunter`，不要勾選自動初始化 README（本專案已有）。
2. 在解壓縮的專案資料夾執行 `git init`、`git branch -M main`、`git add .`、`git commit -m "Initial IELTS Trap Hunter project"`。
3. 到 GitHub repo 複製你自己的 URL，再執行 `git remote add origin 你的-repo-URL` 及 `git push -u origin main`。
4. **老師要至少五個有意義的 commit**。不要為湊數製造空白提交；請在正式提交前分階段完成題庫、LLM、單元測試、網站、部署等更動。若已一次提交完，也可後續實際增修功能並留下清楚修改紀錄。
5. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**。
6. Push 到 `main` 後，到 Actions 查看 `Test and deploy IELTS Trap Hunter` 的 `test` 和 `deploy` 兩個 job 都是綠燈。
7. 網站預期會是 `https://你的帳號.github.io/ielts-trap-hunter/`。請以 GitHub 發布的實際 URL 為準。

注意：**GitHub Pages 只託管靜態展示網站，不會直接呼叫你電腦上的 Ollama。** 網站內建可互動的固定題庫 demo，真正 AI 解說由本機 Python 程式產生；這個界線必須在報告中說清楚。

## 作品頁四個必填區塊

`docs/index.html` 已包含：**做了什麼、怎麼執行、執行結果、AI 使用說明**。作品頁的互動題是靜態測試，請在本機跑過 `uv run main.py` 後把真實 AI 結果截圖補上，才是完整展示。

## AI 使用紀錄（提交前請依自己的真實使用情況修改）

- **使用工具**：ChatGPT（規劃、初版程式與文件協助）；Ollama（執行時生成個人化學習解說）。
- **使用位置**：Python 呼叫 API、設計資料模型、README、網站草稿與測試案例。
- **自己修改/驗證**：請在實際完成後描述你親自閱讀題目、測試 FALSE vs NOT GIVEN、修正程式、檢查 Actions 是否部署成功，以及模型實際執行輸出。
- **限制**：AI 生成的教學解說不保證完全正確；固定題目的答案與原文依據優先；本產品不是官方 IELTS 評分系統。

## 正確性檢驗

`uv run python -m unittest discover -s tests -v` 執行測試，包括答案合法性、原文依據必須存在於文章、涵蓋三種題型、評分、歷史紀錄和故意造錯的題庫拒收測試，以及使用模擬 Ollama 回應測試 JSON Schema。結構化資料符合 JSON Schema **不代表內容一定正確**，所以標準答案不由 LLM 任意產生。

## 參考文件

- [IELTS Academic Reading 題型定義](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-reading)
- [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [uv 官方文件](https://docs.astral.sh/uv/)
- [GitHub Pages Actions 部署](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

# 星座模擬系統（constellation_simulation）

本專案為一套基於 Django 框架的星座模擬與資料管理平台。適合用於衛星星座相關的模擬、數據管理與產出報表等需求。

## 目錄結構說明

```
.
├── .env / .env.sample         # 環境變數設定檔
├── .gitignore                 # Git 忽略清單
├── Pipfile / Pipfile.lock     # Python 套件管理（Pipenv）
├── README.MD                  # 專案說明文件
├── entrypoint.sh              # 啟動腳本
├── logs/                      # 系統運行日誌
├── main/                      # Django 專案主程式
│   ├── asgi.py                # ASGI 入口
│   ├── wsgi.py                # WSGI 入口
│   ├── settings/              # Django 設定（local, production, test）
│   ├── urls.py                # URL 路由
│   ├── apps/                  # 主要應用模組（見下方說明）
│   ├── utils/                 # 工具函式
│   └── db.sqlite3             # SQLite 資料庫（開發用）
├── manage.py                  # Django 管理指令入口
├── requirements/              # 依賴套件需求（不同環境）
├── shell/                     # 測試與輔助腳本
├── simulation_result/         # 各模擬結果資料夾
├── tmp/                       # 暫存檔案（如模擬產生的 PDF 報告）
└── .venv/                     # Python 虛擬環境
```

### main/apps 主要模組

- `meta_data_mgt/`：
    - 負責元資料管理，包含 actors、models、api、services、templates、tests 等子目錄，實作元資料 CRUD、序列化、測試等。
    - actors：元資料的行為邏輯實作。
    - models：元資料的模型定義。
    - api：元資料的 API 定義。
    - services：元資料的服務邏輯實作。
    - templates：元資料的模板文件。
    - tests：元資料的測試案例。
- `simulation_data_mgt/`：
    - 負責模擬資料管理，包含 actors、models、api、services、templates、tests 等子目錄，實作模擬流程、資料序列化、服務與測試等。
    - actors：模擬資料的行為邏輯實作。
    - models：模擬資料的模型定義。
    - api：模擬資料的 API 定義。
    - services：模擬資料的服務邏輯實作。
    - templates：模擬資料的模板文件。
    - tests：模擬資料的測試案例。

兩大模組皆符合 Django 標準結構，便於維護與擴充。

## 其他目錄與檔案用途

- `main/settings/`：不同環境（local, production, test）設定。
- `requirements/`：依賴套件需求（分不同環境 base/local/production/test）。
- `simulation_result/`：各類型模擬結果資料夾。
- `tmp/`：暫存模擬產生的報告（如 PDF）。
- `logs/`：系統運行日誌。
- `shell/`：常用測試與輔助腳本（如自動建立 app、執行測試等）。
- `entrypoint.sh`：容器或伺服器啟動腳本。
- `.env`、`.env.sample`：環境變數設定範例與實際檔案。

## 安裝與執行說明

### 1. 安裝 Python 及 Pipenv

請先安裝 Python（建議 3.8+）與 Pipenv：

```bash
pip install pipenv
```

### 2. 複製專案與建立虛擬環境

```bash
git clone <your-repo-url>
cd constellation_simulation
pipenv install --dev
```

### 3. 設定環境變數

複製 `.env.sample` 為 `.env`，並依需求修改內容：

```bash
cp .env.sample .env
```

### 4. 初始化資料庫（如有需要）

```bash
pipenv run python manage.py migrate
```

### 5. 啟動開發伺服器

```bash
pipenv run python manage.py runserver
```

### 6. 其他腳本

- `shell/` 目錄下有多個自動化腳本與測試腳本，可依需求執行。

---

如需更詳細的模組功能說明，歡迎補充 apps 目錄下各子模組的具體用途。
如果你有特定的安裝或啟動流程，也可補充說明。

如需更細的 requirements 或 Pipfile 內容，請提供檔案內容或允許我存取，謝謝！
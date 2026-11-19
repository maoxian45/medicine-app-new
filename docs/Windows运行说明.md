# Windows 运行说明

## 首次安装

安装 Python 3.11 或以上（勾选 Python Launcher）、Node.js 22 LTS（包含 npm）。安装后重新打开终端。

在项目根目录双击 setup-windows.cmd，联网安装依赖。虚拟环境由本机生成，不能从其他电脑复制 .venv。

## 每次启动

1. 双击 start-backend.cmd，保持窗口运行。健康检查：http://127.0.0.1:8000/api/health；接口文档：http://127.0.0.1:8000/docs。
2. 双击 start-frontend.cmd，保持窗口运行。
3. 浏览器打开 http://127.0.0.1:5173，家庭演示账号 family / family-demo。独立管理端为 http://127.0.0.1:5173/admin，账号 admin / admin-demo。

关闭这两个窗口即可停止，也可在窗口按 Ctrl+C。8000 或 5173 端口被占用时先停止原服务。不要直接双击 index.html。

## 验证流程

进入家庭成员新增成员 → 返回药箱 → 选择该成员 → 在核对表填写药名、使用者、一次用量、频次 → 勾选确认并保存 → 刷新页面，确认数据仍在。

说明书解析区可粘贴原文，或主动选择标明“演示样例”的数据；解析不会自动保存。今日提醒页面展示原数据库已有提醒，暂无提醒时会显示空状态。

## 命令行方式

根目录：

```powershell
py -3 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
..\.venv-win\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

另开一个终端，进入 frontend-web：

```powershell
npm.cmd ci
npm.cmd run dev
```

## 构建和后端测试

frontend-web 中执行 npm.cmd run build，生成 dist。本次使用 Vite 开发服务演示；若单独部署 dist，服务器还需配置 /api 代理。

backend 中执行 ..\.venv-win\Scripts\python.exe -m pytest tests -q。测试已使用临时数据库，与演示数据隔离。

数据库在 backend/data/medicine.db，首次启动自动建表并提供默认成员。此目录和虚拟环境不提交到 Git。

知识库首次提供有来源的草稿，管理员审核发布后用户才可查询；AI 配置位于管理端。实际完成情况以《文档功能对照.md》为准。

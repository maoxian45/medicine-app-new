# 药明白

家庭药箱网页版，使用 Vue、FastAPI 和 SQLite。支持家庭成员、说明书识别与核对、药箱与组合风险检查、用药提醒与记录、老人模式，以及知识库管理和 AI 问答。

## Windows 启动

1. 安装 Python 3.11+（含 Python Launcher）和 Node.js 22 LTS。
2. 首次在项目根目录运行 `setup-windows.cmd` 安装依赖。
3. 分别运行 `start-backend.cmd` 和 `start-frontend.cmd`，保持两个窗口打开。

| 入口 | 本地账号 |
| --- | --- |
| [家庭端](http://127.0.0.1:5173/) | `family` / `family-demo` |
| [知识库管理端](http://127.0.0.1:5173/admin) | `admin` / `admin-demo` |
| [Swagger 接口文档](http://127.0.0.1:8000/docs) · [后端健康检查](http://127.0.0.1:8000/api/health) | 业务接口使用对应角色的登录令牌 |

## 联调与验收

- Vite 将 `/api` 转发到后端。数据库首次启动时创建在 `backend/data/medicine.db`。演示密码可在 [环境变量配置](backend/.env.example) 对应的 `backend/.env` 中修改。
- 管理员先审核发布知识和规则草稿，再用家庭账号验证知识查询、成分匹配与风险检查。AI 真实调用需在管理端配置服务地址、模型和密钥。
- 家庭端演示流程为新增成员 → 扫描或填写说明书 → 核对并检查风险 → 保存入箱 → 设置提醒 → 确认服药并验证撤销。首次图片 OCR 需联网下载识别资源，可用[说明书样图](frontend-web/test-fixtures/ocr/)复测。

在项目根目录执行：

```powershell
.\.venv-win\Scripts\python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend-web run build
```

## 资料

根目录 README 看怎么启动、用什么账号；前端目录的 README 看页面改哪个文件、接口怎么传参数、联调先测什么；`docs/分工.md` 按人写了负责哪个包、要写什么、要测什么。单独的接口约定和联调清单收进了前端交接，详细字段可以看 Swagger。

- [团队分工](docs/分工.md)
- [前端交接](frontend-web/README.md)

# 药明白 Windows 网页版

Vue + FastAPI + SQLite。家庭用户端保留最初手机式 HTML 风格；知识库管理端为独立桌面工作台。

## 运行

首次安装 Python 3.11+（含 Python Launcher）、Node.js 22 LTS，执行 setup-windows.cmd。分别运行 start-backend.cmd 和 start-frontend.cmd。

- 家庭端：http://127.0.0.1:5173 ，账号 family，密码 family-demo。
- 知识管理端：http://127.0.0.1:5173/admin ，账号 admin，密码 admin-demo。
- 接口文档：http://127.0.0.1:8000/docs 。家庭和管理接口需要对应登录令牌。

这台电脑依赖已准备。当前已有家庭基础管理、知识维护与审核、规则风险、AI 接入与配置、老人简易模式等；不是全部需求的最终验收版。

- [文档功能对照和未完成项](docs/文档功能对照.md)
- [Windows 运行说明](docs/Windows运行说明.md)
- [分工与接口约定](docs/分工与接口约定.md)

知识样例初始为草稿，管理员审核发布后用户可查询。AI 尚未配置外部服务，填写配置后才会真实调用。原始 HTML 在 docs/html原型，作为样式参考，不作为功能验收依据。

## 分工

- frontend-web：wmx，两个 UI 包（家庭与管理）。
- backend/routers：sjw，控制包与启动脚本。
- backend/services：qhy，业务服务、认证、知识、AI、风险。
- backend/models、backend/repositories、backend/database.py：wzy，模型、数据访问与数据库。

数据在 backend/data/medicine.db。密钥在 backend/.env，均忽略提交。当前只有一个本地家庭演示账号；多家庭隔离、图片 OCR、提醒推送等进度见对照表。

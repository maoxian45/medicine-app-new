# 药明白后端

药明白 App 的 FastAPI 后端，负责家庭成员、药品等业务数据管理，以及药品说明书 OCR 文字解析、风险提示、用药卡片和语音播报文本生成。

当前项目采用 **SwiftUI 原生 iOS App + FastAPI + SQLite**。iPhone 使用 iOS Vision Framework 在本地完成 OCR，随后将识别出的说明书原始文字发送到后端解析。后端运行在 Windows 电脑上，可由同一 Wi-Fi 下的 iPhone 访问。

## 当前开发状态

已完成：

- FastAPI 项目入口
- CORS 配置
- `/api/health` 健康检查
- SQLite 数据库初始化
- 家庭成员数据接口
- 药品数据接口
- 说明书文字解析接口
- OCR 原始文字清洗
- 药品名称、规格、一次用量、每日次数、服药时间、服用方式提取
- 贮藏方式和有效期提取
- 禁忌与注意事项拆分
- 风险关键词和风险标签识别
- 前端用药卡片数据生成
- 老人模式语音播报文本生成
- 样例药品兜底及数据来源标记
- 提醒计划接口
- 服药记录接口
- 今日用药状态接口
- Swagger 自动接口文档
- 自动化测试（说明书解析、药品字段契约、成员/提醒删除与服药撤销），当前共 38 项测试

尚未完成：

- iOS 前端真实网络联调

## 项目结构

```text
backend/
├── main.py                         # FastAPI 应用入口
├── database.py                     # SQLite 连接和建表初始化
├── requirements.txt                # Python 依赖
├── routers/
│   ├── __init__.py
│   ├── members.py                  # 家庭成员接口
│   ├── medicines.py                # 药品接口
│   ├── reminders.py                # 提醒计划接口
│   ├── records.py                  # 服药记录接口
│   ├── today.py                    # 今日用药状态接口
│   └── instruction.py              # 说明书解析接口
├── services/
│   ├── __init__.py
│   ├── instruction_parser.py       # OCR 文字清洗、字段提取、风险识别和卡片生成
│   └── sample_medicine_loader.py   # 演示兜底数据读取与匹配
├── sample_data/
│   └── sample_medicines.json       # 团队自建演示兜底数据
├── tests/
│   ├── __init__.py
│   └── test_instruction_parser.py  # 说明书解析自动化测试
├── data/
│   └── medicine.db                 # 本地 SQLite 数据库，运行后自动生成
└── README.md
```

## 环境要求

- Windows
- Python 3.11 或更高版本
- PowerShell

## 安装依赖

先进入项目根目录，再执行：

```powershell
cd .\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果已经创建过 `.venv`，不需要重复创建虚拟环境，只需激活并安装依赖：

```powershell
cd .\backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果 PowerShell 不允许执行激活脚本，可以先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

也可以不激活环境，直接使用虚拟环境中的 Python：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 启动后端

在 `backend` 目录中执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

如果虚拟环境已经激活，也可以执行：

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

看到下面的信息表示服务已经启动：

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete.
```

停止服务：在运行服务的 PowerShell 或 VSCode 终端中按 `Ctrl+C`。

## 查看健康状态和 Swagger

电脑浏览器打开：

```text
http://127.0.0.1:8000/api/health
```

预期返回：

```json
{
  "status": "ok",
  "service": "medicine-app-backend",
  "message": "后端运行正常"
}
```

Swagger 文档地址：

```text
http://127.0.0.1:8000/docs
```

在 Swagger 页面中点击 `Try it out`，可以直接发送测试请求。

## 运行自动化测试

在 `backend` 目录中执行：

```powershell
python -m pytest -v
```

当前测试覆盖：

- OCR 文字清洗
- 完整说明书解析
- 禁忌与注意事项拆分
- 样例药品兜底
- 无关文字不误匹配
- 药品 `expiry_date` 字段契约
- 家庭成员按 ID 删除及不存在成员的 404 提示
- 无服药记录的提醒直接删除；有历史记录的提醒停用并保留服药历史
- 服药记录撤销后，今日状态恢复为待服药
- 同一提醒当天的重复服药确认拦截
- 提醒必须绑定存在的具体家庭成员
- 关联提醒的服药记录必须保持成员、药品和剂量一致
- 生产日期、保质期和具体有效期计算与旧数据迁移
- 删除药品只停用其 `medicine_id` 关联的提醒，不误伤同名药
- 儿童喂药记录字段迁移、保存，以及按儿童/药品/日期范围查询

正常结果：

```text
38 passed
```

## 数据库

SQLite 文件位置：

```text
backend/data/medicine.db
```

服务第一次启动时会自动创建数据库和数据表，并初始化以下家庭成员：

- 我
- 爷爷
- 奶奶
- 小宝

当前数据表：

- `members`：家庭成员
- `medicines`：药品信息
- `reminders`：提醒计划
- `records`：服药记录

## 已实现接口

### 健康检查

```text
GET /api/health
```

### 家庭成员

```text
GET  /api/members
GET  /api/members/{id}
POST /api/members
DELETE /api/members/{id}
```

### 提醒计划

```text
GET    /api/reminders
GET    /api/reminders?include_inactive=true
GET    /api/reminders/{id}
POST   /api/reminders
DELETE /api/reminders/{id}
```

删除提醒时：没有服药记录会直接删除；已有服药记录则将 `is_active` 设为 `false`。默认提醒列表和今日状态不会返回停用提醒，历史服药记录会保留。
创建提醒可传入 `medicine_id` 绑定具体药品；当前为兼容旧前端，暂时允许不传，但传入时必须是已有药品。
提醒不能绑定“全部人”等共享对象，且成员名称必须存在于家庭成员列表中。

删除药品时，后端会直接删除药品本身，并将 `medicine_id` 相同且仍启用的提醒设为停用；服药记录不删除。关联只按 `medicine_id` 判断，不会按药名匹配，因此同名药品或旧版未绑定药品 ID 的提醒不会被误停用。

新增成员请求示例：

```json
{
  "emoji": "👩",
  "name": "妈妈",
  "role": "家庭成员",
  "status": "",
  "age": "成人",
  "weight": "",
  "allergy": "无"
}
```

### 药品

```text
GET  /api/medicines
GET  /api/medicines/{id}
GET  /api/medicines?owner=爷爷
POST /api/medicines
PUT  /api/medicines/{id}
DELETE /api/medicines/{id}
```

新增药品请求示例：

```json
{
  "emoji": "💊",
  "name": "布洛芬缓释胶囊",
  "spec": "0.3g × 20 粒",
  "category": "成人常备药",
  "owner": "我",
  "dose": "1 粒",
  "frequency": "每日 2 次",
  "meal_time": "饭后",
  "method": "温水送服",
  "location": "客厅药箱",
  "production_date": "2024-01-15",
  "shelf_life": "36个月",
  "expiry_date": "2027-01-15",
  "stock": "16 粒",
  "status": "正常",
  "risks": ["慎用", "过敏"],
  "note": "请按照说明书或医生建议服用。",
  "original_text": "示例 OCR 文本"
}
```

编辑药品使用 `PUT /api/medicines/{id}`，请求体与新增药品相同；删除药品使用
`DELETE /api/medicines/{id}`，成功时返回 `204 No Content`。

药品日期字段规则：

- `production_date`：生产日期，格式为 `YYYY-MM-DD`；为空时允许保存。
- `shelf_life`：保质期，格式为“`36个月`”；未填写生产日期时默认返回 `36个月`。
- 填写 `production_date` 后，后端按保质期自动计算并保存 `expiry_date`。
- 旧数据中 `expiry_date` 为“`36个月`”的记录，会迁移为 `shelf_life`，不再把它当作具体有效期。

### 说明书文字解析

```text
POST /api/instruction/parse
```

该接口接收 iOS Vision 识别出的说明书原始文字，并返回前端可展示的结构化用药卡片。接口只负责解析，不会自动保存药品到 SQLite。

请求示例：

```json
{
  "ocr_text": "维生素C片\n规格：100mg\n用法用量：口服，一次1片，每日1次，饭后服用。\n密封保存。\n有效期36个月。"
}
```

正常响应示例：

```json
{
  "emoji": "💊",
  "name": "维生素C片",
  "spec": "100mg",
  "category": "",
  "owner": "",
  "dose": "1片",
  "frequency": "1次",
  "meal_time": "饭后",
  "method": "口服",
  "location": "密封保存",
  "expiry": "36个月",
  "stock": "",
  "status": "待确认",
  "risks": [],
  "contraindications": [],
  "precautions": [],
  "note": "",
  "original_text": "维生素C片\n规格：100mg\n用法用量：口服，一次1片，每日1次，饭后服用。\n密封保存。\n有效期36个月。",
  "speech_text": "药品名称，维生素C片。识别到的用法为，一次1片，每日1次，饭后服用，口服。以上为说明书文字识别结果，使用前请再次核对原说明书。",
  "needs_confirmation": true,
  "data_source": "ocr",
  "used_sample_fallback": false,
  "sample_id": "",
  "fallback_fields": [],
  "demo_only": false
}
```

主要返回字段：

- `name`：药品名称
- `spec`：药品规格
- `dose`：一次用量
- `frequency`：每日次数
- `meal_time`：服药时间
- `method`：服用方式
- `location`：贮藏方式
- `expiry`：有效期
- `risks`：风险标签
- `contraindications`：禁忌信息
- `precautions`：注意事项
- `speech_text`：老人模式语音播报文本
- `needs_confirmation`：是否需要用户确认，目前始终为 `true`
- `used_sample_fallback`：是否使用演示样例补充缺失字段
- `fallback_fields`：由样例数据补充的字段
- `demo_only`：返回结果是否含演示数据

## 样例药品兜底

当 OCR 只识别到少量文字，但能够匹配团队准备的演示样例时，后端会补充部分缺失字段。

例如只传入：

```json
{
  "ocr_text": "布洛芬缓释胶囊"
}
```

返回结果中会包含：

```json
{
  "data_source": "ocr+sample",
  "used_sample_fallback": true,
  "sample_id": "demo_ibuprofen_capsule",
  "fallback_fields": [
    "spec",
    "category",
    "dose",
    "frequency",
    "meal_time",
    "method",
    "location",
    "expiry",
    "risks",
    "contraindications",
    "precautions"
  ],
  "demo_only": true
}
```

前端检测到 `used_sample_fallback` 为 `true` 时，必须明确提示：

```text
部分信息来自演示兜底数据，请核对药品包装和原说明书。
```

样例数据仅用于比赛原型演示，不能替代药品原说明书、医生或药师指导。

## 前端对接流程

```text
iOS 拍照或选择图片
→ Vision Framework 本地 OCR
→ POST /api/instruction/parse
→ 展示结构化用药卡片
→ 用户核对并修改
→ 用户确认后调用药品保存接口
```

注意：

- 前端传入的字段名必须为 `ocr_text`。
- `ocr_text` 不能为空，否则接口返回 `422`。
- `speech_text` 可直接交给 `AVSpeechSynthesizer` 播报。
- 所有解析结果都需要用户确认，不能直接作为诊断、处方或剂量决策依据。
- 说明书解析接口不会自动写入 `medicines` 表。

## 局域网访问

后端使用 `--host 0.0.0.0` 启动后，可以被同一 Wi-Fi 下的设备访问。

先在电脑执行：

```powershell
ipconfig
```

找到当前 Wi-Fi 的 IPv4 地址，例如：

```text
192.168.1.23
```

然后在 iPhone Safari 中打开：

```text
http://192.168.1.23:8000/api/health
```

前端接口地址示例：

```text
http://192.168.1.23:8000/api/instruction/parse
```

iPhone 真机不能使用：

```text
http://127.0.0.1:8000
```

因为 iPhone 中的 `127.0.0.1` 指向手机自身。

如果电脑浏览器可以访问、iPhone 无法访问，通常需要检查：

- 手机和电脑是否连接同一个 Wi-Fi
- Windows 防火墙是否允许 Python 或 8000 端口
- 后端是否使用 `--host 0.0.0.0` 启动
- iOS 是否已配置本地网络访问权限

## 开发约定

- 家庭成员、药品、提醒和服药记录等业务数据由业务后端负责保存、查询和更新。
- iOS 端负责拍照、相册选择、Vision OCR、页面展示、语音播放和本地通知。
- 说明书解析模块只接收 OCR 文字，不接收图片，也不调用第三方 OCR API。
- 样例兜底数据仅用于演示，必须在前端明确标记。
- 产品定位为说明书整理、阅读辅助、风险提示和用药提醒工具，不提供诊断、处方推荐或剂量决策。
- 数据库设计保持简单，优先满足比赛演示闭环。
- 新增或修改接口后，需要同步更新本 README、Swagger 文档和自动化测试。

## 提醒计划、服药记录和今日状态

### 提醒计划

```text
GET  /api/reminders
GET  /api/reminders/{id}
POST /api/reminders
```

新增提醒请求示例：

```json
{
  "medicine_name": "降压药",
  "member_name": "爷爷",
  "time": "08:00",
  "meal_label": "早餐后",
  "dose": "1 片",
  "status": "待确认"
}
```

### 服药记录

```text
GET  /api/records
GET  /api/records?date=2026-07-20
GET  /api/records?member_id=4&medicine_id=12&start_date=2026-07-20&end_date=2026-07-26
POST /api/records
DELETE /api/records/{id}
```

提交服药记录请求示例：

```json
{
  "reminder_id": 1,
  "medicine_id": 12,
  "member_id": 4,
  "medicine_name": "降压药",
  "member_name": "爷爷",
  "dose": "1 片",
  "recorded_by": "妈妈",
  "temperature": "37.2℃",
  "note": "饭后服用，精神正常",
  "status": "已服药"
}
```

`reminder_id` 可以关联到具体提醒计划；如果暂时没有对应提醒，也可以传 `null`。
服药时间由后端自动记录，前端不需要自行生成时间。

儿童喂药记录可选传入 `medicine_id`、`member_id`、`recorded_by`、`temperature` 和 `note`。传入药品或成员编号时，后端会校验编号存在且与名称一致。查询支持 `member_id`、`medicine_id`、`start_date`、`end_date`：不带任何筛选条件时，为兼容现有前端，仍只返回今日记录；带成员或药品筛选时可查询对应历史记录。后端只保存实际记录并拦截同一提醒当天的重复确认，不会计算儿童剂量或判断是否允许再次喂药。

### 今日状态

```text
GET /api/today
GET /api/today?date=2026-07-20
```

返回内容包括：

- 当日提醒总数 `total`
- 已完成数量 `completed`
- 待完成数量 `pending`
- 每条提醒的药品、成员、时间、剂量和当前状态

状态判断规则：

- 提醒没有对应服药记录时：`待服药`
- 提醒已有对应服药记录时：`已服药`

后端会优先按照 `reminder_id` 匹配服药记录；如果没有传入 `reminder_id`，则按照药品名、成员名和剂量进行兼容匹配。

删除服药记录即表示撤销“已服药”确认；再次读取 `/api/today` 时，对应提醒会恢复为 `待服药`。
同一条提醒当天只能确认一次，重复提交会返回 `409`。
若提交时带有 `reminder_id`，成员、药品和已填写的剂量必须与该提醒一致。
## 说明书解析与卡片生成

说明书解析模块负责接收 iOS Vision Framework 识别出的 OCR 原始文字，
并生成前端可展示、可编辑和可播报的结构化用药卡片。

### 1. 获取标准样例列表

```http
GET /api/instruction/samples

# 前端交接

负责人 **wmx**。启动、演示账号和构建命令见[项目 README](../README.md)。

## 改哪里

| 要改的内容 | 文件 |
| --- | --- |
| 导航、页面切换、全局样式 | `src/App.vue`、`src/style.css` |
| 接口、登录令牌 | `src/api.js`。开发环境由 `vite.config.js` 把 `/api` 转发到 8000 |
| 首页、登录、成员 | `src/views/Home.vue`、`Login.vue`、`Members.vue` |
| 药品 OCR、核对、风险确认和药箱 | `src/views/Medicines.vue` |
| 提醒、服药记录、老人模式 | `src/views/Records.vue`、`Elder.vue` |
| 知识搜索、风险报告、AI | `src/views/Knowledge.vue`、`Risks.vue`、`AIChat.vue` |
| 知识审核和 AI 配置 | `src/views/Admin.vue`，入口 `/admin` |

## 注意

1. 管理端审核发布药品知识和风险规则。家庭端确认能搜到已发布药品。
2. 在「扫一扫」上传 [OCR 样图](test-fixtures/ocr/)。首次需要联网下载识别资源。核对原文和表单，补全缺项，选择成员，检查风险后保存。保存遇到 409 时重新检查风险。
3. 回药箱确认数据已保存。设置提醒，确认服药，再撤销并检查今日状态；切到老人模式确认数据同步。
4. 改接口时找 **sjw** 确认参数和响应。业务规则找 **qhy**，字段和数据迁移找 **wzy**。

下一轮联调优先确认库存和位置编辑后的核对状态，以及真实 AI 配置后的追问、引用和错误提示。儿童历史补录和多家庭隔离见项目 README。

## 接口怎么接

下表是完整请求路径。在 `src/api.js` 的 `api()` 或 `post()` 里传路径时省略开头的 `/api`，公共函数会补上。错误码约定：400 参数组合不成立（说明书解析二选一）、401 未登录或令牌过期、403 角色不符、404 记录不存在、409 冲突（重复确认或风险未确认）、422 字段不合格、502/503 AI 服务异常或未配置。

| 要做什么 | 接口和关键字段 |
| --- | --- |
| 登录和退出 | `POST /api/auth/login` 传 `username`、`password`，返回 `token` 和 `role`（8 小时有效）。家庭端与管理端令牌分开存放，不能混用。退出用 `POST /api/auth/logout`。 |
| 成员管理 | `GET /api/members`、`GET /api/members/{id}`；新增 `POST /api/members`，编辑 `PUT /api/members/{id}`（传完整字段：`name`、`role`、`age`、`weight`、`allergy` 等），删除 `DELETE /api/members/{id}`。成员改名会同步药品 `owner` 和提醒 `member_name`；重名返回 409，不存在返回 404。 |
| 查药品知识 | `GET /api/knowledge/drugs?keyword=...` 只返回已发布知识；详情 `GET /api/knowledge/drugs/{id}`，未发布返回 404；纠错 `POST /api/knowledge/feedback`。 |
| 解析说明书 | `POST /api/instruction/parse`，`ocr_text` 和 `sample_id` 必须二选一（都提供或都不提供返回 400，样例不存在返回 404）。返回含 `missing_fields`、`parse_quality`、`speech_text`、`elder_speech_text`。样例列表用 `GET /api/instruction/samples`。 |
| 入箱前/编辑前检查风险 | `POST /api/interactions/check`：`member_id` 必填；`candidate_name`、`candidate_ingredients`（数组）；编辑时传 `exclude_medicine_id` 排除药品自身；`foods`（食物饮品名称数组）。返回 `items`、`count`、`highest_level`、`message`、`missing`、`population_notes`。成员药箱报告用 `GET /api/members/{member_id}/risk-report`。 |
| 保存和编辑药品 | `POST /api/medicines`：`name`、`ingredients`（数组）、`owner`（成员名称）、`confirmed`、`risk_accepted`；日期三字段 `production_date`（YYYY-MM-DD）、`shelf_life`（如「36个月」）、`expiry_date`（有生产日期时按保质期自动计算）。已核对时缺药名/成分/使用者/用量/频次返回 422，命中风险未确认返回 409。`PUT /api/medicines/{id}` 是**全量替换**，必须回传完整药品对象；改 `name`、`owner`、`ingredients`、`dose`、`frequency`、`method`、`spec` 会要求重新核对（422），命中风险要 `risk_accepted`（409），并停用该药品的关联提醒；只改 `stock`、`location`、`note` 保留原核对状态。药箱列表用 `GET /api/medicines?owner=...`。 |
| 提醒和记录 | `/api/reminders` 增删查，`PATCH /api/reminders/{id}` 传 `is_active` 停用或恢复，`GET` 支持 `include_inactive`。今日状态 `GET /api/today?date=YYYY-MM-DD`。`POST /api/records` 确认服药或手动补录，`DELETE /api/records/{id}` 撤销（不存在返回 404）。历史 `GET /api/records`：`date` 单日，或 `start_date`/`end_date` 范围，可叠加 `member_id`、`medicine_id`。儿童补录额外传 `recorded_by`、`temperature`（字符串）、`note`、`taken_at`（**必须带时区**的 ISO 8601，只能用于不带 `reminder_id` 的手动记录，且不能晚于当前时间）。传了 `medicine_id`/`member_id` 时名称必须与对应记录一致，同一提醒当天重复确认返回 409。 |
| AI 和管理端 | `POST /api/ai/chat` 传 `question`、`session_id`、`drug_name`；`GET /api/ai/status`、`GET /api/ai/sessions`、`GET /api/ai/sessions/{id}`。管理端 `GET /api/admin/knowledge` 含草稿，`POST` 新增、`PUT` 修改（修改后回到草稿），`POST /api/admin/knowledge/{id}/approve` 或 `/disable` 审核发布或停用，`GET /api/admin/knowledge/{id}/versions` 查版本；`GET /api/admin/feedback`；`GET/PUT /api/admin/ai/config`。`kind` 取 `drug`、`rule`、`food_rule`、`population_rule`；规则类必填 `left`（药品成分）、`right`（另一成分/食物饮品/成员角色）、`impact`，`population_rule` 的 `right` 只能是「成人/老人/儿童/照护者」；所有条目必填 `source_name`、`https://` 开头的 `source_url`、`chapter`、`source_version`、`original`。 |

完整字段和状态码见后端启动后的 [Swagger](http://127.0.0.1:8000/docs)。前端公共请求函数会读取后端的 `detail`，业务请求收到 401 时会清理对应登录状态。

同一个选图入口通过内容校验匹配仓库中的小柴胡颗粒和布洛芬片原图。匹配的原图显示人工核对结果并标注来源，可选择成员，核对必填信息后继续检查风险和入箱。布洛芬片回放包含原图规格；选择成人成员时带入原图成人用法，儿童剂量表需核对。其他图片执行实时 OCR。

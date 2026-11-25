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

下表是完整请求路径。在 `src/api.js` 的 `api()` 或 `post()` 里传路径时省略开头的 `/api`，公共函数会补上。

| 要做什么 | 接口和关键字段 |
| --- | --- |
| 登录和退出 | `POST /api/auth/login` 传 `username`、`password`，返回 `token` 和 `role`。后续请求带对应角色的 Bearer 令牌。退出用 `POST /api/auth/logout`。 |
| 查成员、查药品知识 | `GET /api/members` 取成员列表；`GET /api/knowledge/drugs?keyword=...` 查已发布的药品知识和成分。 |
| 解析说明书 | `POST /api/instruction/parse` 传 `ocr_text` 或 `sample_id`，二选一。根据返回的 `missing_fields` 提醒用户补全。样例列表用 `GET /api/instruction/samples`。 |
| 入箱前检查风险 | `POST /api/interactions/check` 传 `member_id`、`candidate_name`、`candidate_ingredients`。用返回的 `items`、`count`、`message`、`missing` 展示结果，命中风险时让用户确认。已有药箱风险报告用 `GET /api/members/{member_id}/risk-report`。 |
| 保存和编辑药品 | `POST /api/medicines` 传核对后的药品字段、`owner`（成员名称）、`confirmed`、`risk_accepted`。成功返回 201，409 时清掉旧风险结果再检查。药箱列表用 `GET /api/medicines`，库存和位置编辑用 `PUT /api/medicines/{id}`。 |
| 提醒和记录 | `/api/reminders` 管理计划，`GET /api/today` 查今日状态，`POST /api/records` 确认服药，`DELETE /api/records/{id}` 撤销。历史可按 `member_id`、`medicine_id`、`start_date`、`end_date` 筛选。儿童体温 `temperature` 按字符串传。 |
| AI 和管理端 | `POST /api/ai/chat` 提问，`GET /api/ai/sessions` 查历史。管理端用 `/api/admin/knowledge` 管理知识，用 `GET/PUT /api/admin/ai/config` 查看和保存 AI 配置。 |

完整字段和状态码见后端启动后的 [Swagger](http://127.0.0.1:8000/docs)。前端公共请求函数会读取后端的 `detail`，业务请求收到 401 时会清理对应登录状态。

同一个选图入口通过内容校验匹配仓库中的小柴胡颗粒和布洛芬片原图。匹配的原图显示人工核对结果并标注来源，可选择成员，核对必填信息后继续检查风险和入箱。布洛芬片回放包含原图规格；选择成人成员时带入原图成人用法，儿童剂量表需核对。其他图片执行实时 OCR。

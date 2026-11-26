"""药明白后端服务入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from repositories.knowledge import initialize
from routers.instruction import router as instruction_router
from routers.knowledge import admin_router, auth_router
from routers.knowledge import router as knowledge_router
from routers.medicines import router as medicines_router
from routers.members import router as members_router
from routers.records import router as records_router
from routers.reminders import router as reminders_router
from routers.today import router as today_router
from services.auth import require_family

# 启动前读取 backend/.env，账号密码与 AI 配置都由它提供。
load_dotenv(Path(__file__).parent / '.env')

TAGS_METADATA = [
    {"name": "系统", "description": "健康检查与服务状态。"},
    {"name": "登录", "description": "本地演示账号登录与退出，令牌有效期 8 小时。"},
    {"name": "家庭成员", "description": "家庭成员的查询、新增、编辑与删除。"},
    {"name": "药品", "description": "说明书核对后入箱、药箱查询与编辑；改动核心字段需要重新核对。"},
    {"name": "说明书解析", "description": "OCR 文字或标准样例解析为结构化用药卡片。"},
    {"name": "提醒计划", "description": "服药提醒的创建、停用与删除。"},
    {"name": "服药记录", "description": "确认服药、撤销与历史查询；儿童补录记录实际服药时间。"},
    {"name": "今日状态", "description": "按日期汇总提醒与服药记录。"},
    {"name": "知识与AI", "description": "家庭端：已发布知识检索、风险检查与用药知识问答。"},
    {"name": "知识管理", "description": "管理员：知识草稿、审核发布、版本历史与 AI 配置。"},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    initialize()
    yield


app = FastAPI(
    title="药明白 API",
    description="药明白 App 的业务数据后端。家庭端接口需要家庭令牌，管理端接口需要管理员令牌。",
    version="0.3.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(knowledge_router)
for family_router in (
    members_router,
    medicines_router,
    instruction_router,
    reminders_router,
    records_router,
    today_router,
):
    app.include_router(family_router, dependencies=[Depends(require_family)])


@app.get(
    "/api/health",
    tags=["系统"],
    summary="健康检查",
)
def health_check() -> dict[str, str]:
    """返回后端服务当前状态，不校验令牌。"""

    return {
        "status": "ok",
        "service": "medicine-app-backend",
        "message": "后端运行正常",
    }

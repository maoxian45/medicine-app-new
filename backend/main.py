"""药明白后端服务入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.instruction import router as instruction_router
from routers.members import router as members_router
from routers.medicines import router as medicines_router
from routers.records import router as records_router
from routers.reminders import router as reminders_router
from routers.today import router as today_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="药明白 API",
    description="药明白 App 的业务数据后端",
    version="0.3.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(members_router)
app.include_router(medicines_router)
app.include_router(instruction_router)
app.include_router(reminders_router)
app.include_router(records_router)
app.include_router(today_router)


@app.get(
    "/api/health",
    tags=["系统"],
)
def health_check() -> dict[str, str]:
    """返回后端服务当前状态。"""

    return {
        "status": "ok",
        "service": "medicine-app-backend",
        "message": "后端运行正常",
    }

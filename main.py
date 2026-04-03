from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from scheduler import create_scheduler
import logging

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/trigger/{period}")
def trigger(period: str):
    """Manually trigger a brief. period = morning | evening | azure-costs"""
    from services.brief_builder import build_brief
    from services.mailer import send_email
    from config import TO_EMAIL

    if period == "azure-costs":
        from scheduler import send_azure_cost_brief
        send_azure_cost_brief()
        return {"status": "sent", "period": period}

    if period == "azure-costs-last-month":
        from scheduler import send_azure_cost_brief
        send_azure_cost_brief(last_month=True)
        return {"status": "sent", "period": period}

    if period not in ("morning", "evening"):
        return JSONResponse({"error": "period must be morning, evening, or azure-costs"}, status_code=400)

    subject, html = build_brief(period.capitalize())
    send_email(TO_EMAIL, subject, html)
    return {"status": "sent", "period": period}

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

ROOT = Path(__file__).resolve().parent
MENU = [
    {"id": "americano", "name": "아메리카노", "description": "깊고 깔끔한 에스프레소", "price": 4000, "category": "커피", "emoji": "☕"},
    {"id": "latte", "name": "카페 라떼", "description": "부드러운 우유와 에스프레소", "price": 4800, "category": "커피", "emoji": "🥛"},
    {"id": "vanilla", "name": "바닐라 라떼", "description": "달콤한 바닐라의 향", "price": 5300, "category": "커피", "emoji": "✨"},
    {"id": "espresso", "name": "에스프레소", "description": "짧고 진하게 즐기는 커피", "price": 3500, "category": "커피", "emoji": "☕"},
    {"id": "cappuccino", "name": "카푸치노", "description": "풍성한 우유 거품과 에스프레소", "price": 4800, "category": "커피", "emoji": "☕"},
    {"id": "mocha", "name": "카페 모카", "description": "초콜릿과 에스프레소의 달콤한 조화", "price": 5300, "category": "커피", "emoji": "🍫"},
    {"id": "caramel", "name": "카라멜 마키아토", "description": "카라멜을 더한 달콤한 커피", "price": 5500, "category": "커피", "emoji": "☕"},
    {"id": "coldbrew", "name": "콜드브루", "description": "차갑게 우려낸 깔끔한 커피", "price": 4500, "category": "커피", "emoji": "🧊"},
    {"id": "matcha", "name": "말차 라떼", "description": "진한 말차와 우유", "price": 5500, "category": "음료", "emoji": "🍵"},
    {"id": "chocolate", "name": "초콜릿 라떼", "description": "진하고 부드러운 초콜릿", "price": 5000, "category": "음료", "emoji": "🍫"},
    {"id": "strawberry", "name": "딸기 라떼", "description": "달콤한 딸기와 우유", "price": 5500, "category": "음료", "emoji": "🍓"},
    {"id": "ade", "name": "레몬 에이드", "description": "상큼하게 톡 쏘는 레몬", "price": 5500, "category": "음료", "emoji": "🍋"},
    {"id": "grapefruit", "name": "자몽 에이드", "description": "새콤달콤한 자몽과 탄산", "price": 5500, "category": "음료", "emoji": "🍊"},
    {"id": "earlgrey", "name": "얼그레이 티", "description": "향긋한 베르가못 홍차", "price": 4500, "category": "티", "emoji": "🫖"},
    {"id": "chamomile", "name": "캐모마일 티", "description": "은은하고 편안한 허브차", "price": 4500, "category": "티", "emoji": "🌼"},
    {"id": "green-tea", "name": "녹차", "description": "깔끔하고 산뜻한 녹차", "price": 4500, "category": "티", "emoji": "🍵"},
    {"id": "croissant", "name": "크루아상", "description": "겉은 바삭 속은 촉촉", "price": 3800, "category": "디저트", "emoji": "🥐"},
    {"id": "cheesecake", "name": "치즈 케이크", "description": "진하고 부드러운 치즈 케이크", "price": 6000, "category": "디저트", "emoji": "🍰"},
    {"id": "cookie", "name": "초콜릿 쿠키", "description": "초콜릿이 콕콕 박힌 쿠키", "price": 3000, "category": "디저트", "emoji": "🍪"},
]


class OrderItem(BaseModel):
    menu_id: str
    quantity: int = Field(ge=1, le=99, strict=True)


class OrderRequest(BaseModel):
    items: list[OrderItem] = Field(min_length=1, max_length=50)


class MongoOrderStore:
    def __init__(self, database):
        self.orders = database.orders
        self.counters = database.counters

    def add(self, items, total):
        counter = self.counters.find_one_and_update(
            {"_id": "order_number"}, {"$inc": {"value": 1}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
        order = {"order_number": counter["value"], "items": items, "total": total,
                 "created_at": datetime.now(timezone.utc)}
        self.orders.insert_one(order.copy())
        return order


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT / '.env')
    uri = os.getenv('MONGODB_URI')
    if not uri:
        raise RuntimeError('MONGODB_URI 환경 변수를 설정하세요.')
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command('ping')
        app.state.orders = MongoOrderStore(client[os.getenv('MONGODB_DATABASE', 'cafe_kiosk')])
        yield
    finally:
        client.close()


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')


@app.get('/api/menu')
def menu():
    return MENU


@app.post('/api/orders', status_code=201)
def create_order(request: OrderRequest):
    lookup = {item['id']: item for item in MENU}
    items = []
    for entry in request.items:
        product = lookup.get(entry.menu_id)
        if not product:
            raise HTTPException(status_code=400, detail='존재하지 않는 메뉴입니다.')
        items.append({'menu_id': entry.menu_id, 'name': product['name'], 'price': product['price'], 'quantity': entry.quantity})
    total = sum(item['price'] * item['quantity'] for item in items)
    return app.state.orders.add(items, total)

# 오늘의 카페 키오스크

FastAPI로 만든 카페 주문 테스트 화면입니다. 결제는 모의 처리이며 주문은 MongoDB에 저장됩니다.

## 로컬 실행 (Windows PowerShell)

Python 3.10 이상을 설치한 뒤 이 폴더에서 실행하세요.

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env의 MONGODB_URI에 MongoDB 연결 문자열을 입력하세요.
.\.venv\Scripts\python -m uvicorn main:app --reload
```

브라우저에서 http://127.0.0.1:8000 을 열고 메뉴를 담아 주문하세요. API 문서는 http://127.0.0.1:8000/docs 에서 확인할 수 있습니다. 종료하려면 터미널에서 Ctrl+C를 누르세요.

## 이후 배포와 데이터베이스

Render의 Python 웹 서비스용 `render.yaml`을 준비했습니다. Render 환경 변수에 `MONGODB_URI`를 설정하세요. 데이터베이스 이름은 `MONGODB_DATABASE`로 변경할 수 있으며 기본값은 `cafe_kiosk`입니다. MongoDB Atlas에서 접속할 환경의 네트워크 접근도 허용해야 합니다. 주문은 `orders` 컬렉션에, 주문번호 카운터는 `counters` 컬렉션에 저장됩니다. `.env`는 저장소에 올리지 마세요. 실제 결제 연동은 별도로 필요합니다.

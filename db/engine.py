from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 從環境變數讀取資料庫網址
# 如果讀不到 (例如本地沒設定)，可以設定一個預設值，或者讓它報錯
DATABASE_URL = os.getenv("DATABASE_URL")

# Vercel/Neon 有時提供的網址是 postgres:// 開頭，SQLAlchemy 需要 postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # 這裡您可以放回原本寫死的網址當作 fallback，或是直接拋出錯誤提醒自己要去設環境變數
    # 建議：在本機開發時，將網址寫在 .env 檔案中
    print("Warning: DATABASE_URL not found in environment variables.")

# 建立資料庫引擎
engine = create_engine(DATABASE_URL)

# 建立 SessionLocal 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別
Base = declarative_base()

# 取得資料庫連線的依賴函式 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
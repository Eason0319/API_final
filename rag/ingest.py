import os
import sys
# 將專案根目錄加入路徑，以便讀取 .env
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

load_dotenv()

# 設定
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
# 指向 rag_data 資料夾下的 data.txt
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),  "data.txt")

def main():
    if not os.path.exists(DATA_FILE):
        print(f"❌ 錯誤：找不到 {DATA_FILE}，請確認檔案位置。")
        return

    print(f"📂 正在讀取 {DATA_FILE}...")
    documents = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(Document(page_content=line))

    if not documents:
        print("⚠️ 檔案是空的。")
        return

    print(f"🔄 正在上傳 {len(documents)} 筆資料到 Pinecone Index: {INDEX_NAME}...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    try:
        PineconeVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            index_name=INDEX_NAME
        )
        print("✅ 上傳成功！資料已存入 Pinecone。")
    except Exception as e:
        print(f"❌ 上傳失敗: {e}")

if __name__ == "__main__":
    main()
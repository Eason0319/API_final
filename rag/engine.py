import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 全域變數
rag_chain = None

# 沿用您的 Prompt
RAG_SYSTEM_PROMPT = """你是富邦悍將（Fubon Guardians）的熱血應援小幫手！你非常熟悉球隊的成員、教練與相關資訊。

【最高準則】：
只要【參考資訊】沾到一點邊，就要回答！
例如使用者問「自由球員」，只要資料裡有出現「FA」、「加盟」、「轉隊」等字眼，就把那整句話講出來。
**絕對不要說**「我不知道」或「沒有詳細資訊」，把你知道的全部說出來就好。

回答時也請以一個熱血球迷的口吻回答問題。
【參考資訊】：
{context}
"""

def init_rag_chain():
    """初始化 RAG 系統 (連線 Pinecone)"""
    global rag_chain
    
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        print("❌ 警告：未設定 PINECONE_INDEX_NAME，RAG 功能將無法使用。")
        return

    print(f"--- 正在初始化 RAG (Pinecone: {index_name}) ---")
    
    try:
        # 1. 連線 Pinecone (不需重新上傳，直接連線)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
        
        # 2. 定義 Retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

        # 3. 定義 LLM 與 Prompt
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("user", "{question}")
        ])

        # 4. 建立 Chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        print("✅ RAG 系統初始化完成")
        
    except Exception as e:
        print(f"❌ RAG 初始化失敗: {e}")

def get_answer(question: str) -> str:
    """提供給 API 呼叫的介面"""
    if not rag_chain:
        return "系統維護中，RAG 尚未初始化 (Pinecone 連線失敗)。"
    
    try:
        result = rag_chain.invoke(question)
        return result
    except Exception as e:
        return f"發生錯誤: {str(e)}"
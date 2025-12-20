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

【任務說明】：
請根據提供的【參考資訊】熱情地回答球迷的問題。

【回答規範】：
1. **基於事實**：所有回答都必須來自下方的【參考資訊】，不能憑空捏造。
2. **語氣風格**：充滿活力、正面，使用台灣繁體中文。提到球員時可以帶有敬意。
3. **未知處理**：如果資料裡找不到答案，請委婉地說：「哎呀，這個資訊我目前還沒有掌握到，但我會努力學習更多富邦悍將的知識！」
4. **格式優化**：重點資訊請加粗（Bold），讓球迷一眼就能看到重點。

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
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

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
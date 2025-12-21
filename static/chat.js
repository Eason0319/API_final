// 參考 blog.js 的引用方式
import { waitForAuthInit, getCurrentIdToken } from './auth.js';

// 取得 DOM 元素
const loginOverlay = document.getElementById('login-overlay');
const messagesList = document.getElementById('messages-list');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// --- 核心邏輯：完全比照 blog.js 的權限檢查 ---
(async function init() {
    console.log("Chat: 正在等待 Firebase 初始化...");
    
    // 1. 等待 auth.js 回傳登入狀態
    const user = await waitForAuthInit;

    // 2. 判斷使用者是否登入
    if (user) {
        console.log("Chat: 使用者已登入", user.email);
        if (loginOverlay) loginOverlay.classList.add('hidden');
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    } else {
        console.log("Chat: 使用者未登入，保持鎖定");
        if (loginOverlay) loginOverlay.classList.remove('hidden');
    }
})();

// --- 發送訊息邏輯 ---
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // 顯示使用者訊息
    appendMessage(text, 'user');
    userInput.value = '';
    userInput.disabled = true;
    sendBtn.disabled = true;

    // 顯示 AI 思考中
    const loadingId = appendMessage('思考中...', 'ai', true);

    try {
        // 取得 Token
        const token = await getCurrentIdToken();
        if (!token) throw new Error("無法取得登入憑證");

        // 發送給後端
        const res = await axios.post('/api/chat', { message: text }, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        // 成功後移除讀取訊息，並顯示回答
        removeMessage(loadingId);
        appendMessage(res.data.reply, 'ai');

    } catch (err) {
        removeMessage(loadingId);
        console.error("Chat Error:", err);
        const errorMsg = (err.response && err.response.status === 401) 
            ? '登入已過期，請重新登入。' 
            : '發生錯誤，請稍後再試。';
        appendMessage(errorMsg, 'ai');
        
        if (err.response && err.response.status === 401) {
            setTimeout(() => window.location.href = 'login.html', 2000);
        }
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// 綁定事件
if (sendBtn) sendBtn.addEventListener('click', sendMessage);
if (userInput) userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// UI 輔助函式
function appendMessage(text, sender, isLoading = false) {
    const div = document.createElement('div');
    const isUser = sender === 'user';
    
    // 【關鍵修正】加入隨機字串，防止同一毫秒內的訊息 ID 重複
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    div.id = id;
    
    div.className = `flex w-full ${isUser ? 'justify-end' : 'justify-start'}`;
    
    // 更新樣式以配合新的介面設計
    // User: 黃色背景 (配合按鈕), AI: 藍色半透明 (配合 Header/Static Greeting)
    const userStyle = 'bg-yellow-400 text-blue-900 rounded-tr-none shadow-lg font-medium';
    const aiStyle = 'bg-blue-600/80 text-white rounded-tl-none border border-blue-500/30 backdrop-blur-sm';
    
    const colorClass = isUser ? userStyle : aiStyle;
    
    div.innerHTML = `
        <div class="${colorClass} p-3 md:p-4 rounded-2xl max-w-[85%] shadow-md ${isLoading ? 'animate-pulse' : ''}">
            ${text.replace(/\n/g, '<br>')}
        </div>
    `;
    messagesList.appendChild(div);
    messagesList.scrollTop = messagesList.scrollHeight;
    return id; // 回傳這個唯一的 ID 供後續移除使用
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
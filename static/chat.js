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
    
    // 1. 等待 auth.js 回傳登入狀態 (這是 blog.js 成功的關鍵)
    const user = await waitForAuthInit;

    // 2. 判斷使用者是否登入
    if (user) {
        console.log("Chat: 使用者已登入", user.email);
        
        // 已登入：隱藏遮罩 (使用 Tailwind 語法隱藏)
        if (loginOverlay) {
            loginOverlay.classList.add('hidden'); // 確保遮罩消失
        }
        
        // 解鎖輸入框
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    } else {
        console.log("Chat: 使用者未登入，保持鎖定");
        // 未登入：遮罩預設就是顯示的，不需要做動作，或者強制顯示
        if (loginOverlay) {
            loginOverlay.classList.remove('hidden');
        }
    }
})();

// --- 發送訊息邏輯 (保持不變) ---
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // 顯示使用者訊息
    appendMessage(text, 'user');
    userInput.value = '';
    userInput.disabled = true;
    sendBtn.disabled = true;

    // 顯示 AI 思考中
    const loadingId = appendMessage('正在查詢資料庫...', 'ai', true);

    try {
        // 取得 Token (後端驗證用)
        const token = await getCurrentIdToken();
        if (!token) throw new Error("無法取得登入憑證");

        // 發送給後端
        const res = await axios.post('/api/chat', { message: text }, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

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
    const id = 'msg-' + Date.now();
    div.id = id;
    div.className = `flex w-full ${isUser ? 'justify-end' : 'justify-start'}`;
    const colorClass = isUser ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-slate-700 text-gray-100 rounded-tl-none border border-slate-600';
    
    div.innerHTML = `
        <div class="${colorClass} p-3 rounded-2xl max-w-[85%] shadow-md ${isLoading ? 'animate-pulse' : ''}">
            ${text.replace(/\n/g, '<br>')}
        </div>
    `;
    messagesList.appendChild(div);
    messagesList.scrollTop = messagesList.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
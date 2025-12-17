// index.js （ES Module + Top-Level Await）
import { getCurrentIdToken, waitForAuthInit } from './auth.js';
const listEl = document.getElementById('list');

function cardHTML(p) {
  const author = p.author.name ?? '';
  const title = p.title ?? '無標題';
  const href = `/post.html?slug=${encodeURIComponent(p.slug || '')}`;

  return `
    <a href="${href}"
       class="group block rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md p-6 shadow-lg 
              hover:shadow-blue-500/30 hover:-translate-y-1 transition-all duration-300 h-full flex flex-col">
      
      <h3 class="text-xl font-bold text-white mb-2 line-clamp-2 group-hover:text-yellow-400 transition-colors duration-300">
        ${title}
      </h3>
      
      <p class="text-blue-200 text-sm mb-3">作者：${author}</p>
      
      <div class="h-1 w-16 bg-yellow-400 rounded-full mb-3 group-hover:w-24 transition-all duration-300"></div>

    </a>
  `;
}

(async function loadPosts() {
  try {
    listEl.innerHTML = '<div class="text-blue-200">正在取得登入狀態...</div>';
    
    // 【修改】1. 等待 Firebase 驗證完成
    const user = await waitForAuthInit;

    // 【修改】2. 檢查回傳的 user 物件
    if (!user) {
      // user 是 null，確定未登入
      listEl.innerHTML = '<div class="text-yellow-400 text-center font-bold text-lg">請先登入以看到文章 😞</div>';
      return; 
    }

    // 【修改】3. 如果 user 存在，*才*去取得 Token
    listEl.innerHTML = '<div class="text-blue-200">已登入，正在載入文章...</div>';
    const token = await getCurrentIdToken(); // 這裡 user 必定存在

    if (!token) {
        // 雖然 user 存在，但 token 取得失敗 (罕見)
        throw new Error("已登入，但無法取得 Token。");
    }

    // 【修改】4. 在請求中附上 Token (這部分不變)
    const res = await axios.get('/api/posts', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      timeout: 10000
    });
    
    const posts = res.data;

    if (!Array.isArray(posts) || posts.length === 0) {
      listEl.innerHTML = '<div class="text-slate-500">目前沒有文章。</div>';
    } else {
      listEl.innerHTML = posts.map(p => cardHTML(p)).join('');
    }
  } catch (err) {
    if (err.response && err.response.status === 401) {
      listEl.innerHTML = '<div class="text-yellow-400 text-center font-bold text-lg">您的登入已過期，請重新登入以查看文章。</div>';
    } else {
      listEl.innerHTML = `<div class="text-rose-600">讀取失敗：${err.message}</div>`;
    }
    console.error('列表載入錯誤', err);
  }
})();
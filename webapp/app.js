const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const initData = tg.initData;
let currentUser = null;

// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('text-blue-600');
        btn.classList.add('text-gray-400');
    });
    const activeBtn = document.querySelector(.nav-btn[data-target=" + tabId + "]);
    if(activeBtn) {
        activeBtn.classList.remove('text-gray-400');
        activeBtn.classList.add('text-blue-600');
    }
    
    if (tabId === 'experts') loadExperts();
    if (tabId === 'cabinet') loadCabinet();
    if (tabId === 'admin') loadAdminPanel();
}

// Image Preview
function previewImages(input, previewId) {
    const container = document.getElementById(previewId);
    container.innerHTML = '';
    if (input.files) {
        Array.from(input.files).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'image-preview';
                container.appendChild(img);
            }
            reader.readAsDataURL(file);
        });
    }
}

// Initial Load
async function initApp() {
    try {
        const res = await fetch('/api/user', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ initData })
        });
        if (res.ok) {
            currentUser = await res.json();
            if (currentUser.is_admin) {
                document.getElementById('navAdmin').classList.remove('hidden');
            }
        }
    } catch(e) { console.error(e); }
}

// Tab 1: AI Check Submit
document.getElementById('aiForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btnText = document.getElementById('aiBtnText');
    const loader = document.getElementById('aiLoader');
    btnText.innerText = 'Yuborilmoqda...';
    loader.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('initData', initData);
    formData.append('criteria', document.getElementById('aiCriteria').value);
    formData.append('topic', document.getElementById('aiTopic').value);
    formData.append('text', document.getElementById('aiText').value);
    
    const files = document.getElementById('aiFiles').files;
    for(let i=0; i<files.length; i++) {
        formData.append('files', files[i]);
    }
    
    try {
        await fetch('/api/upload_ai', { method: 'POST', body: formData });
        tg.showAlert("Essengiz AI ga yuborildi. Natijani bot orqali kuting!");
        document.getElementById('aiForm').reset();
        document.getElementById('aiPreview').innerHTML = '';
    } catch(err) {
        tg.showAlert("Xatolik yuz berdi.");
    } finally {
        btnText.innerText = 'Tekshirishga yuborish';
        loader.classList.add('hidden');
    }
});

// Tab 2: Experts List
async function loadExperts() {
    document.getElementById('orderForm').classList.add('hidden');
    const container = document.getElementById('expertList');
    container.innerHTML = '<div class="text-center py-10"><div class="loader mx-auto"></div></div>';
    try {
        const res = await fetch('/api/experts');
        const experts = await res.json();
        container.innerHTML = '';
        if (experts.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-500">Faol ekspertlar yoq.</p>';
            return;
        }
        experts.forEach(exp => {
            const stars = exp.reviews > 0 ? '⭐'.repeat(Math.round(exp.rating)) : 'Yangi';
            container.innerHTML += 
                <div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 mb-3">
                    <h3 class="font-bold text-lg">👤  + exp.name + </h3>
                    <p class="text-sm text-yellow-500 mb-2"> + stars +  ( + exp.reviews +  ta sharh)</p>
                    <p class="text-sm text-gray-600 dark:text-gray-300 italic mb-4"> + exp.bio + </p>
                    <button onclick="openOrderForm( + exp.id + )" class="w-full bg-blue-50 text-blue-600 dark:bg-gray-700 dark:text-blue-400 font-bold py-2 rounded-xl">Ekspertni tanlash</button>
                </div>
            ;
        });
    } catch(e) { container.innerHTML = '<p class="text-center text-red-500">Xatolik yuz berdi</p>'; }
}

async function openOrderForm(expId) {
    document.getElementById('orderExpertId').value = expId;
    document.getElementById('expertList').innerHTML = '';
    document.getElementById('orderForm').classList.remove('hidden');
    
    try {
        const res = await fetch('/api/settings');
        const settings = await res.json();
        document.getElementById('orderPrice').innerText = settings.price;
        document.getElementById('orderCard').innerText = settings.card;
    } catch(e){}
}

function closeOrderForm() {
    document.getElementById('orderForm').classList.add('hidden');
    loadExperts();
}

// Tab 2: Order Submit
document.getElementById('humanForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btnText = document.getElementById('humanBtnText');
    const loader = document.getElementById('humanLoader');
    btnText.innerText = 'Yuborilmoqda...';
    loader.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('initData', initData);
    formData.append('expert_id', document.getElementById('orderExpertId').value);
    formData.append('text', document.getElementById('orderText').value);
    formData.append('receipt', document.getElementById('orderReceipt').files[0]);
    
    const files = document.getElementById('orderFiles').files;
    for(let i=0; i<files.length; i++) {
        formData.append('files', files[i]);
    }
    
    try {
        await fetch('/api/upload_human', { method: 'POST', body: formData });
        tg.showAlert("Chek va esse yuborildi. Admin tasdiqlashi bilan ekspertga yuboriladi!");
        closeOrderForm();
    } catch(err) {
        tg.showAlert("Xatolik yuz berdi.");
    } finally {
        btnText.innerText = 'Yuborish';
        loader.classList.add('hidden');
    }
});

// Tab 3: Cabinet
async function loadCabinet() {
    const container = document.getElementById('cabinetContent');
    container.innerHTML = '<div class="text-center py-10"><div class="loader mx-auto"></div></div>';
    
    if (!currentUser) await initApp();
    
    let html = 
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
            <h2 class="text-2xl font-bold mb-1">👤  + currentUser.first_name + </h2>
            <p class="opacity-80 text-sm mb-4">Balans:  + currentUser.balance +  UZS</p>
            <div class="flex justify-between bg-white/20 rounded-xl p-3 backdrop-blur-md">
                <div class="text-center w-full">
                    <p class="text-xs opacity-80 uppercase tracking-wider">Tekshirilgan esselar</p>
                    <p class="text-xl font-bold"> + currentUser.stats + </p>
                </div>
            </div>
        </div>
    ;
    
    if (currentUser.expert) {
        const exp = currentUser.expert;
        if (exp.status === 'active') {
            html += 
                <div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 mt-4">
                    <h3 class="font-bold text-lg mb-2">👨‍🏫 Ekspert Profili</h3>
                    <p class="text-sm"><b>Daromad:</b>  + exp.earned +  UZS</p>
                    <p class="text-sm"><b>Reyting:</b>  + ('⭐'.repeat(Math.round(exp.rating)) || 'Yangi') +  ( + exp.reviews +  ta sharh)</p>
                    <button onclick="loadExpertTasks()" class="w-full mt-4 bg-gray-800 text-white rounded-xl py-3 font-bold">Yangi esselarni ko'rish</button>
                    <div id="expertTasksArea" class="mt-4 space-y-3"></div>
                </div>
            ;
        } else if (exp.status === 'pending') {
            html += <div class="bg-yellow-50 text-yellow-600 p-4 rounded-xl mt-4 text-center text-sm font-medium border border-yellow-200">Ekspertlik arizangiz ko'rib chiqilmoqda...</div>;
        } else {
            html += <div class="bg-red-50 text-red-600 p-4 rounded-xl mt-4 text-center text-sm font-medium border border-red-200">Arizangiz rad etilgan.</div>;
        }
    } else {
        html += 
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 mt-4">
                <h3 class="font-bold mb-2">🎓 Ekspert bo'lish</h3>
                <p class="text-sm text-gray-500 mb-4">Esselarni tekshirib pul ishlashni xohlasangiz, ekspertlikka ariza topshiring.</p>
                <textarea id="applyBio" rows="3" placeholder="O'zingiz va tajribangiz haqida yozing..." class="w-full rounded-xl border p-3 mb-3 text-sm dark:bg-gray-700 dark:border-gray-600"></textarea>
                <button onclick="applyExpert()" class="w-full bg-blue-100 text-blue-600 dark:bg-gray-700 dark:text-blue-400 font-bold py-2 rounded-xl">Ariza topshirish</button>
            </div>
        ;
    }
    
    container.innerHTML = html;
}

async function applyExpert() {
    const bio = document.getElementById('applyBio').value;
    if(!bio) return;
    await fetch('/api/apply_expert', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ initData, bio }) });
    tg.showAlert("Arizangiz adminga yuborildi!");
    currentUser.expert = { status: 'pending' };
    loadCabinet();
}

async function loadExpertTasks() {
    const container = document.getElementById('expertTasksArea');
    container.innerHTML = '<div class="loader mx-auto"></div>';
    try {
        const res = await fetch('/api/expert/tasks?initData=' + encodeURIComponent(initData));
        const tasks = await res.json();
        container.innerHTML = '';
        if(tasks.length === 0) {
            container.innerHTML = '<p class="text-sm text-center text-gray-500">Hozircha yangi esse yoq.</p>';
            return;
        }
        tasks.forEach(t => {
            let photosHtml = '';
            if (t.photo_id) {
                // We can't directly show telegram photo_id images in WebApp without downloading them to server.
                // For now, expert will have to use the bot to see images, or we just indicate images exist.
                // Actually, earlier the bot sent images to expert via chat. We can tell them to check bot chat.
                photosHtml = '<p class="text-sm text-blue-500 mb-2">📸 Rasm botingizga yuborilgan yoki yuboriladi.</p>';
            }
            container.innerHTML += 
                <div class="border rounded-xl p-3 dark:border-gray-700">
                    <p class="text-xs text-gray-400 mb-1">Esse # + t.id + </p>
                     + photosHtml + 
                    <p class="text-sm mb-3"> + (t.text || '') + </p>
                    <textarea id="reply_ + t.id + " rows="3" placeholder="Xulosa yozing..." class="w-full rounded-lg border p-2 text-sm mb-2 dark:bg-gray-900 dark:border-gray-600"></textarea>
                    <button onclick="sendReply( + t.id + )" class="bg-green-500 text-white px-3 py-1.5 rounded-lg text-sm w-full font-medium">Javob yuborish</button>
                </div>
            ;
        });
    } catch(e) {}
}

async function sendReply(id) {
    const text = document.getElementById('reply_' + id).value;
    if(!text) return;
    try {
        await fetch('/api/expert/reply', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ initData, essay_id: id, reply_text: text }) });
        tg.showAlert("Javobingiz mijozga yuborildi!");
        loadExpertTasks();
    } catch(e) {}
}

// Tab 4: Admin
async function loadAdminPanel() {
    try {
        const res = await fetch('/api/settings');
        const settings = await res.json();
        document.getElementById('adminPrice').value = settings.price;
        document.getElementById('adminCard').value = settings.card;
        
        const expertsRes = await fetch('/api/experts');
        const experts = await expertsRes.json();
        
        const list = document.getElementById('adminExpertsList');
        list.innerHTML = '';
        if(experts.length === 0) list.innerHTML = '<p class="text-sm text-gray-500">Faol ekspertlar yoq.</p>';
        experts.forEach(exp => {
            list.innerHTML += 
                <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-3 rounded-xl border border-gray-100 dark:border-gray-600">
                    <div>
                        <p class="font-bold text-sm"> + exp.name + </p>
                        <p class="text-xs text-gray-500">Daromad: (Botdan ko'rish kerak)</p>
                    </div>
                    <button onclick="removeExpert( + exp.id + )" class="text-red-500 bg-red-50 p-2 rounded-lg text-xs font-bold">O'chirish 🗑</button>
                </div>
            ;
        });
    } catch(e) {}
}

async function saveAdminSettings() {
    const price = document.getElementById('adminPrice').value;
    const card = document.getElementById('adminCard').value;
    await fetch('/api/admin/settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ initData, price, card }) });
    tg.showAlert("Sozlamalar saqlandi!");
}

async function removeExpert(id) {
    if(confirm("Haqiqatan ham o'chirmoqchimisiz?")) {
        await fetch('/api/admin/remove_expert', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ initData, expert_id: id }) });
        tg.showAlert("O'chirildi!");
        loadAdminPanel();
    }
}

// Startup
initApp();

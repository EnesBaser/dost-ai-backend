<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DostAI Admin</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f0f1a;
      color: #e2e8f0;
      min-height: 100vh;
    }
    .login-screen {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }
    .login-card {
      background: #1a1a2e;
      border: 1px solid #9333ea44;
      border-radius: 16px;
      padding: 40px;
      width: 360px;
      text-align: center;
    }
    .login-card h1 { font-size: 28px; margin-bottom: 8px; }
    .login-card p { color: #94a3b8; margin-bottom: 28px; }
    input[type="password"] {
      width: 100%;
      padding: 12px 16px;
      background: #0f0f1a;
      border: 1px solid #334155;
      border-radius: 10px;
      color: #e2e8f0;
      font-size: 16px;
      margin-bottom: 16px;
      outline: none;
    }
    input[type="password"]:focus { border-color: #9333ea; }
    .btn {
      width: 100%;
      padding: 12px;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-primary {
      background: linear-gradient(135deg, #9333ea, #7c3aed);
      color: white;
    }
    .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .btn-danger {
      background: linear-gradient(135deg, #ef4444, #dc2626);
      color: white;
    }
    .btn-success {
      background: linear-gradient(135deg, #22c55e, #16a34a);
      color: white;
    }
    .btn-warning {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: white;
    }
    .btn-secondary {
      background: #334155;
      color: #e2e8f0;
    }

    .dashboard { display: none; padding: 24px; max-width: 900px; margin: 0 auto; }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 32px;
      padding-bottom: 20px;
      border-bottom: 1px solid #1e293b;
    }
    header h1 { font-size: 24px; }
    header span { color: #94a3b8; font-size: 14px; }

    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
    .stat-card {
      background: #1a1a2e;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 20px;
    }
    .stat-card .label { color: #94a3b8; font-size: 13px; margin-bottom: 8px; }
    .stat-card .value { font-size: 28px; font-weight: 700; color: #9333ea; }
    .stat-card .sub { color: #64748b; font-size: 12px; margin-top: 4px; }

    .section {
      background: #1a1a2e;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
    }
    .section h2 { font-size: 17px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    .action-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    .action-btn {
      padding: 14px 16px;
      border: none;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: center;
    }
    .action-btn:hover { transform: translateY(-2px); opacity: 0.9; }
    .action-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    .log {
      background: #0f0f1a;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 16px;
      font-family: monospace;
      font-size: 13px;
      max-height: 300px;
      overflow-y: auto;
      margin-top: 16px;
    }
    .log-entry { padding: 4px 0; border-bottom: 1px solid #1e293b11; }
    .log-entry.success { color: #22c55e; }
    .log-entry.error { color: #ef4444; }
    .log-entry.info { color: #60a5fa; }
    .log-entry.warning { color: #f59e0b; }

    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      opacity: 0;
      transition: opacity 0.3s;
      z-index: 1000;
    }
    .toast.show { opacity: 1; }
    .toast.success { background: #22c55e; color: white; }
    .toast.error { background: #ef4444; color: white; }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 50px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge-green { background: #22c55e22; color: #22c55e; }
    .badge-red { background: #ef444422; color: #ef4444; }
    .badge-purple { background: #9333ea22; color: #9333ea; }

    .scheduler-info {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-top: 12px;
    }
    .job-card {
      background: #0f0f1a;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 12px 16px;
      flex: 1;
      min-width: 200px;
    }
    .job-card .job-name { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
    .job-card .job-next { font-size: 12px; color: #94a3b8; }
  </style>
</head>
<body>

<!-- Login -->
<div class="login-screen" id="loginScreen">
  <div class="login-card">
    <h1>🤖 DostAI</h1>
    <p>Admin Paneli</p>
    <input type="password" id="adminPassword" placeholder="Şifre" onkeydown="if(event.key==='Enter') login()">
    <button class="btn btn-primary" onclick="login()">Giriş Yap</button>
  </div>
</div>

<!-- Dashboard -->
<div class="dashboard" id="dashboard">
  <header>
    <div>
      <h1>🤖 DostAI Admin</h1>
      <span id="currentTime"></span>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
      <span class="badge badge-green" id="serverStatus">● Kontrol ediliyor...</span>
      <button class="btn btn-secondary" style="width:auto;padding:8px 16px;font-size:13px;" onclick="logout()">Çıkış</button>
    </div>
  </header>

  <!-- Stats -->
  <div class="grid" id="statsGrid">
    <div class="stat-card">
      <div class="label">Sunucu Durumu</div>
      <div class="value" id="statVersion">—</div>
      <div class="sub">Backend versiyonu</div>
    </div>
    <div class="stat-card">
      <div class="label">Scheduler</div>
      <div class="value" id="statScheduler">—</div>
      <div class="sub">APScheduler durumu</div>
    </div>
    <div class="stat-card">
      <div class="label">TR Saati</div>
      <div class="value" id="statTRTime">—</div>
      <div class="sub">Sunucu zamanı</div>
    </div>
  </div>

  <!-- Bildirimler -->
  <div class="section">
    <h2>🔔 Bildirim Yönetimi</h2>
    <div class="action-grid">
      <button class="action-btn btn-primary" onclick="triggerNotification()">
        📤 Tüm Kullanıcılara Gönder
      </button>
      <button class="action-btn btn-success" onclick="testNotification()">
        🧪 Bana Test Gönder
      </button>
      <button class="action-btn btn-secondary" onclick="checkScheduler()">
        🔄 Scheduler Durumu
      </button>
    </div>
    <div class="log" id="notifLog">
      <div class="log-entry info">— Bildirim logları burada görünecek —</div>
    </div>
  </div>

  <!-- Sistem -->
  <div class="section">
    <h2>⚙️ Sistem</h2>
    <div class="action-grid">
      <button class="action-btn btn-secondary" onclick="checkHealth()">
        💚 Health Check
      </button>
      <button class="action-btn btn-warning" onclick="clearLog()">
        🗑️ Logları Temizle
      </button>
    </div>

    <!-- Scheduler jobs -->
    <div class="scheduler-info" id="schedulerInfo" style="display:none;">
      <div class="job-card">
        <div class="job-name">☀️ Sabah Bildirimi</div>
        <div class="job-next" id="morningNext">—</div>
      </div>
      <div class="job-card">
        <div class="job-name">🌤️ Öğlen Bildirimi</div>
        <div class="job-next" id="afternoonNext">—</div>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
  const BASE_URL = window.location.origin;
  const GOOGLE_ID = '117096745782071439494';
  const ADMIN_PASSWORD = 'dostai2026';  // Basit şifre — istersen değiştir

  let isLoggedIn = false;

  // ── Zaman ────────────────────────────────────────────────────────────────
  function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent =
      now.toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
  }
  setInterval(updateTime, 1000);
  updateTime();

  // ── Login ─────────────────────────────────────────────────────────────────
  function login() {
    const pwd = document.getElementById('adminPassword').value;
    if (pwd === ADMIN_PASSWORD) {
      isLoggedIn = true;
      document.getElementById('loginScreen').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      checkHealth();
      checkScheduler();
    } else {
      showToast('Yanlış şifre!', 'error');
      document.getElementById('adminPassword').value = '';
    }
  }

  function logout() {
    isLoggedIn = false;
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('adminPassword').value = '';
  }

  // ── API ───────────────────────────────────────────────────────────────────
  async function apiPost(endpoint) {
    const res = await fetch(BASE_URL + endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Google-ID': GOOGLE_ID,
      },
    });
    return res.json();
  }

  async function apiGet(endpoint) {
    const res = await fetch(BASE_URL + endpoint, {
      headers: { 'X-Google-ID': GOOGLE_ID },
    });
    return res.json();
  }

  // ── Actions ───────────────────────────────────────────────────────────────
  async function triggerNotification() {
    addLog('📤 Tüm kullanıcılara bildirim gönderiliyor...', 'info');
    try {
      const data = await apiPost('/api/notifications/trigger');
      if (data.success) {
        addLog('✅ Job başlatıldı — Railway loglarını kontrol et', 'success');
        showToast('Bildirim job\'ı başlatıldı!', 'success');
      } else {
        addLog('❌ Hata: ' + JSON.stringify(data), 'error');
      }
    } catch (e) {
      addLog('❌ Bağlantı hatası: ' + e, 'error');
    }
  }

  async function testNotification() {
    addLog('🧪 Test bildirimi gönderiliyor...', 'info');
    try {
      const data = await apiPost('/api/notifications/test');
      if (data.success) {
        addLog(`✅ Gönderildi!`, 'success');
        addLog(`📌 Başlık: ${data.title}`, 'info');
        addLog(`💬 Mesaj: ${data.body}`, 'info');
        showToast('Test bildirimi gönderildi!', 'success');
      } else {
        addLog('❌ Hata: ' + JSON.stringify(data), 'error');
      }
    } catch (e) {
      addLog('❌ Bağlantı hatası: ' + e, 'error');
    }
  }

  async function checkScheduler() {
    try {
      const data = await apiGet('/api/scheduler/status');
      const status = data.running ? '🟢 Aktif' : '🔴 Durdu';
      document.getElementById('statScheduler').textContent = status;
      document.getElementById('statTRTime').textContent = data.turkey_time || '—';

      if (data.jobs && data.jobs.length > 0) {
        document.getElementById('schedulerInfo').style.display = 'flex';
        data.jobs.forEach(job => {
          const nextRun = job.next_run
            ? new Date(job.next_run).toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' })
            : 'Bilinmiyor';
          if (job.id === 'morning_notification') {
            document.getElementById('morningNext').textContent = 'Sonraki: ' + nextRun;
          } else if (job.id === 'afternoon_notification') {
            document.getElementById('afternoonNext').textContent = 'Sonraki: ' + nextRun;
          }
        });
        addLog(`🔄 Scheduler: ${status} | ${data.jobs.length} job aktif`, 'info');
      }
    } catch (e) {
      addLog('❌ Scheduler kontrol hatası: ' + e, 'error');
    }
  }

  async function checkHealth() {
    try {
      const data = await apiGet('/health');
      if (data.status === 'ok') {
        document.getElementById('serverStatus').textContent = '● Online';
        document.getElementById('serverStatus').className = 'badge badge-green';
        document.getElementById('statVersion').textContent = data.version || '—';
        addLog('💚 Sunucu sağlıklı: ' + data.version, 'success');
      }
    } catch (e) {
      document.getElementById('serverStatus').textContent = '● Offline';
      document.getElementById('serverStatus').className = 'badge badge-red';
      addLog('❌ Sunucu erişilemiyor!', 'error');
    }
  }

  function clearLog() {
    document.getElementById('notifLog').innerHTML =
      '<div class="log-entry info">— Log temizlendi —</div>';
  }

  // ── Log ───────────────────────────────────────────────────────────────────
  function addLog(message, type = 'info') {
    const log = document.getElementById('notifLog');
    const now = new Date().toLocaleTimeString('tr-TR');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${now}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
  }

  // ── Toast ─────────────────────────────────────────────────────────────────
  function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.className = 'toast', 3000);
  }
</script>
</body>
</html>
```

---

İki şey ekle:

1. `admin.html` dosyasını `dost-ai-backend` reposuna ekle
2. `routes/user.py`'e `/admin` route'unu ekle

Deploy sonrası şu adresten erişirsin:
```
https://dost-ai-backend-v2-production.up.railway.app/admin

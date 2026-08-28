// FreeLLMAPI 一键引导：等服务起来后，建管理员 + 加免密供应商 + 取 unified key
// 用法：先启动服务 (npm run dev -w server)，另开一个终端跑 `node bootstrap.mjs`
const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const EMAIL = process.env.ADMIN_EMAIL || 'admin@local.dev';
const PASSWORD = process.env.ADMIN_PASSWORD || 'freellmapi123';

// 这些平台无需任何密钥即可匿名使用（免费）。注意：pollinations / huggingface /
// opencode 实际上需要各自的免费 key，不能匿名，故不在此列；它们需到 dashboard 手动添加。
const KEYLESS = ['kilo', 'llm7', 'ovh', 'aihorde'];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitPing() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(BASE + '/api/ping');
      if (r.ok) { console.log('[ok] 服务已就绪', BASE); return; }
    } catch {}
    process.stdout.write('.');
    await sleep(1000);
  }
  throw new Error('服务在 60s 内未就绪，请先启动 npm run dev -w server');
}

async function j(url, opts) {
  const r = await fetch(BASE + url, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
  });
  let body = null;
  try { body = await r.json(); } catch {}
  return { status: r.status, body };
}

(async () => {
  await waitPing();

  // 1) 建管理员（首次）或登录（已建过）
  let token;
  let res = await j('/api/auth/setup', { method: 'POST', body: JSON.stringify({ email: EMAIL, password: PASSWORD }) });
  if (res.status === 201) {
    token = res.body.token;
    console.log('[ok] 已创建管理员账号', EMAIL);
  } else if (res.status === 409) {
    res = await j('/api/auth/login', { method: 'POST', body: JSON.stringify({ email: EMAIL, password: PASSWORD }) });
    if (res.status === 200) { token = res.body.token; console.log('[ok] 已登录现有管理员'); }
    else { console.error('[失败] 登录失败:', res.status, res.body); process.exit(1); }
  } else {
    console.error('[失败] 建管理员失败:', res.status, res.body); process.exit(1);
  }

  // 2) 取 unified key
  res = await j('/api/settings/api-key', { headers: { Authorization: 'Bearer ' + token } });
  const apiKey = res.body?.apiKey;
  if (!apiKey) { console.error('[失败] 取 unified key 失败:', res.status, res.body); process.exit(1); }

  // 3) 加免密供应商
  for (const p of KEYLESS) {
    const r = await j('/api/keys', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: JSON.stringify({ platform: p }) });
    if (r.status === 200 || r.status === 201) console.log(`[ok] 已添加免密供应商: ${p}`);
    else console.log(`[跳过] ${p} 添加失败 (${r.status}): ${JSON.stringify(r.body?.error?.message || r.body)}`);
  }

  console.log('\n==================== 完成 ====================');
  console.log('Unified API Key :', apiKey);
  console.log('代理端点        :', BASE + '/v1/chat/completions');
  console.log('\n调用示例 (OpenAI 兼容):');
  console.log(`curl ${BASE}/v1/chat/completions \\\n  -H "Authorization: Bearer ${apiKey}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"model":"auto","messages":[{"role":"user","content":"你好"}]}'`);
})().catch((e) => { console.error('引导失败:', e.message); process.exit(1); });

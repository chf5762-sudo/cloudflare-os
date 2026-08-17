const https = require('https');
const http = require('http');

const BASE_URL = 'https://open-router.beundredig.eu.org/v1';
const API_KEY = 'sk-SMd1Jw3dIf1lTWfHPP3lbRSkP8l4HJDUpAJhTdseFjFhqvB5';

const models = [
  "aistudio/gemini-2.5-flash",
  "aistudio/gemma-4-26b-a4b-it",
  "aistudio/gemma-4-31b-it",
  "aistudio/gemini-3.1-flash-lite",
  "aistudio/gemini-3.5-flash",
  "openrouter/cohere/north-mini-code:free",
  "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
  "openrouter/deepseek/deepseek-v4-pro",
  "openrouter/deepseek/deepseek-v4-flash",
  "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
  "openrouter/openrouter/free",
  "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
  "Chrom-CDP/claude-sonnet-free",
  "Chrom-CDP/claude-haiku-free"
];

async function testModel(modelName) {
  return new Promise((resolve) => {
    const url = new URL(`${BASE_URL}/chat/completions`);
    const payload = JSON.stringify({
      model: modelName,
      messages: [{ role: 'user', content: 'Hello, test response.' }],
      max_tokens: 15
    });

    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 15000
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            const reply = json.choices?.[0]?.message?.content || 'NO_CONTENT';
            resolve({ model: modelName, status: 'OK', code: 200, reply: reply.trim().slice(0, 40) });
          } catch (e) {
            resolve({ model: modelName, status: 'PARSE_ERROR', code: 200, error: e.message });
          }
        } else {
          resolve({ model: modelName, status: 'FAILED', code: res.statusCode, error: data.slice(0, 100) });
        }
      });
    });

    req.on('error', (err) => resolve({ model: modelName, status: 'ERROR', error: err.message }));
    req.on('timeout', () => { req.destroy(); resolve({ model: modelName, status: 'TIMEOUT' }); });

    req.write(payload);
    req.end();
  });
}

async function runTests() {
  console.log('🚀 开始测试 OpenRouter / OpenAI 兼容接口所有的 14 个模型...\n');
  const results = [];
  for (const model of models) {
    process.stdout.write(`Testing [${model}] ... `);
    const res = await testModel(model);
    console.log(res.status === 'OK' ? `✅ PASS (${res.reply})` : `❌ ${res.status} (Code: ${res.code || 'N/A'})`);
    results.push(res);
  }

  console.log('\n📊 详细测试总结结果：');
  console.table(results);
}

runTests();

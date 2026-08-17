module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: __dirname,
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '192.168.10.3:8080',
        MCP_ALLOW_INSECURE: 'true'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};

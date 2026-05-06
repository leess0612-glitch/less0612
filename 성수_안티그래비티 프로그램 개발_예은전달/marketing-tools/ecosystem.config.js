module.exports = {
  apps: [
    {
      name: "marketing-tools",
      script: "server.js",
      cwd: __dirname,
      interpreter: "node",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
    },
    {
      name: "git-watcher",
      script: "C:\\Users\\a\\Desktop\\안티그라비티\\git-watcher.js",
      interpreter: "node",
      autorestart: true,
      watch: false,
    },
  ],
};

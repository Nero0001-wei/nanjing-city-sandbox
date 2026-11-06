# 南京城市沙盘

交互式南京城市微缩沙盘，包含景点模型、地形、昼夜模式及各景点的可编辑建模源文件。

[打开在线预览](https://nero0001-wei.github.io/nanjing-city-sandbox/)

## 本地运行

需要 Node.js 22 或更新版本：

```sh
cd sandbox-app
npm ci
npm run dev
```

运行 `npm test` 检查测试，运行 `npm run build` 构建静态网页。推送至 `main` 后，GitHub Actions 会自动构建并更新 GitHub Pages。

网页源码和资源位于 `sandbox-app/`；各景点的 Blender 母版、生成脚本与效果图保留在对应的景点目录。项目约定见 [AGENTS.md](AGENTS.md)。依赖目录、构建产物和重复交付压缩包不纳入 Git。

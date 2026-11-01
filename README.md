# 凯旋 · AI圈每日简报

这是凯旋的 AI圈每日简报站点。每天一篇精选，做成可以直接阅读的静态页，并保留 Markdown 原文。

在线地址：<https://kaixuan94.github.io/ai-daily-briefing/>

## 目录

- `index.html`：简报目录。以后新的日期会列在这里。
- `briefs/YYYY-MM-DD.md`：当天原文。
- `briefs/YYYY-MM-DD.html`：当天阅读页。
- `assets/style.css`：手机和桌面共用的版式。

GitHub Pages 从 `main` 分支的根目录发布（仓库根目录有 `.nojekyll`，页面按静态文件直接提供）。

## 开启 Pages

若站点还没有生效，在 GitHub 仓库打开 **Settings → Pages**，设置一次：

1. **Build and deployment** 选 **Deploy from a branch**
2. **Branch** 选 `main`，文件夹选 `/ (root)`
3. 保存

构建完成后即可通过上面的地址访问。

## 新增一天

1. 把简报保存为 `briefs/YYYY-MM-DD.md`
2. 安装依赖并重新生成页面：

   ```bash
   pip install markdown
   python3 scripts/render_site.py
   ```

3. 把生成的 HTML 和 Markdown 一起提交到 `main`

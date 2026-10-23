# 个人站

门户、摄影站和技术博客已独立实现。摄影采用选定的 B 深色画廊，博客采用简洁的浅色阅读布局。当前照片与文章均为明确标注的演示内容。

## 本地查看

安装依赖：`python -m pip install -r requirements.txt`。

若系统 Python 不允许直接安装，可用虚拟环境；当前本地开发也支持把博客依赖安装到项目内：`python -m pip install --target .local-deps Pygments markdown-it-py mdit-py-plugins PyYAML`，此目录不进入 Git 或网站输出。Pillow 仍需可用。公式使用随项目保存的 KaTeX 0.19.0 与字体，正常构建不需要 Node.js 或联网；恢复这些资源可运行 `python scripts/fetch-blog-math.py`。

公开内容预览：`python scripts/serve.py`，访问 `http://127.0.0.1:4173/`。服务器只提供构建输出，不提供源码、原始照片或草稿文件。修改内容后重新启动预览，或另执行 `python scripts/build.py` 刷新页面。

本地草稿预览：`python scripts/serve.py --preview --port 4174`，访问 `http://127.0.0.1:4174/`。这会显示草稿和撤下内容，带预览横幅及禁止索引标记。

发布：`python scripts/build.py`，仅部署 `dist/`，**不要上传整个项目或 `.preview-dist/`**。站点域名已配置为 `https://www.yjhtest.xyz`，构建会据此生成站点地图、绝对地址的分享预览和规范链接。仓库目前没有记录托管平台或自动部署配置；将 `dist/` 部署到该域名对应的站点即可。

## 内容与目录

- `index.html`：门户页面入口。
- `src/modules/portal/`：门户配置、脚本、样式。
- `src/modules/photography/`：摄影渲染、交互、相册资料与原始素材。
- `src/modules/blog/`：博客渲染、样式、Markdown 文章、配图、模板及本地公式资源；文章信息可直接写在 Markdown 开头。
- `src/shared/`：共享基础样式。
- `public/portal/`：门户封面。
- `scripts/`：构建、预览与备份。
- `dist/`：自动生成的公开网站，不进入 Git。
- `design-demos/`：历史设计稿，不进入发布输出。
- `docs/`：需求、设计和验证记录。

修改 `site.json` 更新昵称、简介、封面、模块显示和联系链接。`src/modules/portal/config.js` 在构建输出中自动生成，不作为内容编辑入口。没有真实联系方式时不显示假链接。

更新方法与发布状态详见 [内容维护说明](docs/content-guide.md)。博客新文章可复制 `src/modules/blog/templates/post.md`，图片、表格、公式的完整示例见 `src/modules/blog/content/posts/markdown-guide.md`。校验：`python tests/test_build.py` 与 `python tests/test_markdown.py`，顺序运行。备份：`python scripts/backup.py`，在 `backups/` 生成包含可编辑源码、资料和原始素材的 ZIP，可解压到新目录后重新构建。

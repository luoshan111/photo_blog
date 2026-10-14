# 个人站

当前完成个人门户，采用已选择的 B 摄影画廊方向。摄影站、技术博客入口暂连接独立预览页面。

## 本地查看

在项目目录执行 `python -m http.server 4173 --bind 127.0.0.1`，浏览器访问 `http://127.0.0.1:4173/`。门户使用 JavaScript 模块，需要通过本地服务器访问。

## 内容与目录

- `index.html`：门户页面入口。
- `src/modules/portal/`：门户配置、脚本、样式。
- `public/portal/`：门户封面。
- `design-demos/`：此前的设计稿与模块预览，不是正式模块实现。
- `docs/`：需求、设计和验证记录。

修改 `src/modules/portal/config.js` 更新昵称、简介、封面、模块显示及联系链接。没有真实联系方式时不显示假链接。当前封面为 Unsplash 演示素材，不能作为个人作品使用。

后续摄影与博客分别在 `src/modules/photography/` 和 `src/modules/blog/` 实现，仅共用必要的基础组件。

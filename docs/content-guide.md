# 内容维护

## 个人门户

编辑 `site.json`：`name`、`description`、`bio`、`cover`、`coverAlt`、`coverCaption`、`photoCredit`。封面路径相对项目根目录。换成你的作品后同步修改摄影署名。

`contacts` 可填入 `{ "label": "GitHub", "href": "https://github.com/你的账号" }` 或邮箱的 `mailto:` 链接。没有联系方式时显示待填写说明，不生成假链接。

`modules.photography`、`modules.blog` 控制模块开放。设为 `false` 后重新构建：入口、模块页面和索引同时移除，既有链接显示 404 页面。

`moduleOrder` 控制门户入口顺序，`moduleLabels` 与 `moduleDescriptions` 控制入口名称与简介。`avatar` 可填写头像的项目相对路径，留空则不显示头像。

## 开场与转场

当前分配为：首次进入门户播放 C「数据成像」，进入摄影首页播放 A「负片显影」，点击导航「联系」时播放 B「光场折射」并滚动到联系区域。博客和摄影相册内部浏览保持直接访问。

门户完整开场在同一标签页会话内只自动播放一次，页脚「重播开场」可再次观看。摄影首页刷新、摄影相册返回首页、浏览器前进后退不重复开场。博客从其他模块进入首页时播放黑白灰像素揭幕；刷新、博客内部跳转不重复播放，博客首页页脚的「重播入场」可再次观看。支持跳过和 Escape；系统偏好减少动态时不播放。WebGL 不可用时快速显示内容，不阻塞阅读。

编辑 `site.json` 中的 `motion`：`enabled` 控制总开关；`introSeconds`、`photographySeconds`、`blogSeconds`、`contactSeconds` 调整时长，默认 4 / 0.9 / 1.6 / 1.1 秒。修改后重新构建即可。门户、摄影与联系动画使用门户封面，换封面时自动同步。博客动画无需图片，直接透过灰阶像素遮罩逐步显露真实页面，专属 Shader 与样式位于 `src/modules/blog/motion/`。

`url` 已配置为 `https://www.yjhtest.xyz`。构建会用它生成站点地图、规范链接和绝对地址的分享预览；本地预览不受影响。

## 摄影

原始图片放在 `src/modules/photography/assets/`。编辑 `content/albums.json`：每个相册包含独立 `slug`、标题、简介、`published` 和照片列表。

照片包含模块内相对 `file` 路径、独立 `id`、`alt`、可选标题/时间/地点/说明、`published`。数组顺序就是显示顺序。相册与照片的标识使用小写英文、数字、连字符。

只有相册已发布且照片也已发布才进入公开站点。空相册不显示。图片会自动按方向校正并生成 640/1280/1920 长边的 WebP，保留尺寸信息；公开输出不复制原始文件，也不保留 EXIF。这个处理是网页优化，不是防止截图或下载的保证。

## 技术博客

现在推荐**一篇文章一个 `.md`**，不必再创建单独的 JSON。把 `src/modules/blog/templates/post.md` 复制到 `src/modules/blog/content/posts/`，例如命名为 `my-first-post.md`。也可以在 `posts/` 内按文件夹整理文章，构建会自动查找。原有的 `.json + .md` 文章继续兼容；同一文章添加 YAML 信息后，以 Markdown 文件内的信息为准。

文件开头用两行 `---` 包围 YAML 信息，后面直接写正文：

```yaml
---
slug: my-first-post
title: 我的第一篇技术博客
description: 记录一次实践与思考。
date: 2026-10-23
category:
  slug: programming
  name: 编程实践
tags:
  - slug: python
    name: Python
draft: true
published: true
---
```

`slug`、`title`、`date` 必填；slug 使用小写英文、数字、连字符且全站博客不能重复。建议每次填写 `description`、`category`、`tags` 和发布状态。标签没有时填 `tags: []`；未填分类时归为「技术笔记」。`draft` 未填默认 `true`，`published` 未填默认 `true`，两个状态只能填不带引号的 `true` 或 `false`。标题中含 `: ` 等 YAML 特殊字符时用引号包围。文件保存为 UTF-8。

正文大标题由 `title` 提供，正文建议从 `##` 开始。支持标题、段落、有序及无序列表、嵌套列表、引用、代码块、行内代码、粗体、斜体、删除线、链接、图片、表格和数学公式。原始 HTML 按文字处理。

### 图片

推荐按文章建立配图目录，例如：

```text
content/posts/
  my-first-post.md
  images/
    my-first-post/
      diagram.png
```

正文写 `![图片说明](images/my-first-post/diagram.png)`。路径相对于当前 Markdown 文件，支持中文文件名和带空格的路径（用 `<images/我的 配图.png>` 包住路径）。图片说明作为替代文字；可用 `![说明](images/example.png "提示文字")` 添加鼠标悬停提示。支持引用式图片语法，也支持完整的 HTTPS/HTTP 图片地址；外链图片不下载，显示取决于原站，自己的配图优先放本地。

本地支持 PNG、JPEG、WebP、GIF、AVIF；静态图片生成最高 640/1280/1920 宽度的 WebP，保留透明度，带尺寸信息、响应式选择和延迟加载；动画图片保留动画格式。本地图片必须位于博客模块内。缺图时构建会指出文章和路径，避免发布坏图。只输出当前构建收录文章实际引用的图片；草稿专用图片只会进入草稿预览。不要把正文配图混入摄影模块。

### 表格

使用标准管道表格；冒号控制左、中、右对齐：

```markdown
| 方案 | 说明 | 耗时 |
| :--- | :---: | ---: |
| A | **简洁** | 12 |
| B | `缓存` | 8 |
```

表格支持行内文字格式、链接、图片和公式。宽表格在手机上可横向滚动，键盘也可聚焦滚动。单元格中的竖线写作 `\|`，公式中的集合分隔建议用 `\mid`。

### 数学公式

行内公式写 `$E = mc^2$`。独立公式用 `$$` 包围：

```text
$$
\mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^{N}(y_i-f_\theta(x_i))^2
$$
```

支持分式、根号、上下标、求和、积分、矩阵（`bmatrix` 等）和多行推导（`aligned` 等）常用 LaTeX 数学语法，也支持标注为 `math` 的围栏块。排版使用本地 KaTeX 和本地字体，含屏幕阅读器可读的 MathML，不请求第三方 CDN；只有含公式的文章才加载公式脚本。特别长的独立公式可横向滚动。公式语法写错时显示原始公式及错误提示，不影响其余内容。普通代码块、行内代码与转义美元符号不会被当成公式。

完整示例：`content/posts/markdown-guide.md`，构建后访问 `/blog/posts/markdown-guide/`。

代码块在三个反引号后写语言名，例如 `javascript`、`python`、`json`、`bash`，构建时自动高亮；未标注或未知语言按纯文本显示。代码块支持复制，浏览器无法写入剪贴板时会选中代码，方便手动复制。

技术博客导航提供「搜索」和「归档」。搜索包括标题、摘要、分类、标签和正文，可用空格组合多个关键词；归档按年、月自动分组。二者只使用当前构建收录的文章，公开版本不收录草稿与撤下内容。搜索在浏览器本地执行，不向外部服务发送关键词。

公开条件：`draft: false` 且 `published: true`。草稿和撤下文章不生成页面，不出现在分类标签和站点地图中；本地预览可以查看。

分类和标签页面自动从已发布文章生成。文章目录由正文标题生成，点击可跳转，支持重复标题而不重复锚点。

## 构建、预览与备份

- `python scripts/build.py`：重建公开站点 `dist/`。
- `python scripts/serve.py`：本地公开内容预览，默认端口 4173。
- `python scripts/serve.py --preview --port 4174`：本地草稿预览。
- `python scripts/backup.py`：源码与内容备份 ZIP，包含原始图片，只保存到本地。

发布只部署 `dist/`。站点域名为 `https://www.yjhtest.xyz`；本仓库没有记录托管平台或自动部署配置，请把构建后的 `dist/` 内容部署到该域名对应的站点根目录。未知链接、关闭的模块及撤下的内容应由托管服务返回 `404.html`，并保留 HTTP 404 状态。当前本地预览服务器已实现此行为；正式托管需按平台配置。

真实昵称、头像、经历、联系方式、作品与文章仍待补充。域名已配置；实际线上部署状态和托管平台设置不由本仓库记录。

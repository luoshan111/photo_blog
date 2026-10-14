// 个人门户内容配置。未启用的模块不显示入口；填入真实资料即可替换占位内容。
export const portal = {
  name: '个人站',
  description: '用照片记录所见，用代码探索想法。\n这里是我的摄影作品与技术文章的入口。',
  bio: '摄影师，也是一名程序员。\n个人介绍与经历待补充。',
  cover: './public/portal/cover.jpg',
  coverAlt: '群山与云层，摄影演示素材',
  coverCaption: '山野 / 演示选片',
  modules: {
    photography: { enabled: true, href: './design-demos/gallery/index.html?portal=home#photography' },
    blog: { enabled: true, href: './design-demos/technical-blog/index.html?portal=home' },
  },
  // 示例格式：{ label: 'GitHub', href: 'https://github.com/你的账号' }
  contacts: [],
};

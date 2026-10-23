"""CommonMark blog rendering with tables, local images, math and escaped HTML."""
import html
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / '.local-deps'))
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

def code_block(lines, language):
    source = '\n'.join(lines)
    try: lexer = get_lexer_by_name(language or 'text', stripnl=False, ensurenl=False)
    except ClassNotFound: lexer = TextLexer(stripnl=False, ensurenl=False)
    tokens = highlight(source, lexer, HtmlFormatter(nowrap=True))
    if not source.endswith('\n'): tokens = tokens.removesuffix('\n')
    return '<div class="code-block"><div class="code-tools"><span>'+html.escape(language or 'text')+'</span></div><pre tabindex="0" aria-label="代码"><code>'+tokens+'</code></pre></div>'

def math_markup(source, display=False):
    tag = 'div' if display else 'span'
    kind = 'math-display' if display else 'math-inline'
    attrs = ' tabindex="0" role="region" aria-label="数学公式，可横向滚动"' if display else ''
    return f'<{tag} class="{kind}" data-math{attrs}>{html.escape(source)}</{tag}>'

def render(text, image_resolver=None):
    md = MarkdownIt('commonmark', {'html': False}).enable(['table', 'strikethrough'])
    md.use(dollarmath_plugin, allow_labels=False, allow_space=False, allow_digits=False, double_inline=True)
    toc = []

    def fence(renderer, tokens, idx, options, env):
        token = tokens[idx]
        language = token.info.strip().split(' ', 1)[0]
        if language == 'math': return math_markup(token.content.strip(), True) + '\n'
        return code_block(token.content.split('\n'), language) + '\n'

    def inline_math(renderer, tokens, idx, options, env):
        return math_markup(tokens[idx].content)

    def block_math(renderer, tokens, idx, options, env):
        return math_markup(tokens[idx].content.strip(), True) + '\n'

    def double_math(renderer, tokens, idx, options, env):
        return '<span class="math-inline math-inline-display" data-math>' + html.escape(tokens[idx].content) + '</span>'

    def image(renderer, tokens, idx, options, env):
        token = tokens[idx]
        source = token.attrGet('src') or ''
        alt = renderer.renderInlineAsText(token.children or [], options, env)
        title = token.attrGet('title') or ''
        if image_resolver: return image_resolver(source, alt, title)
        return f'<img src="{html.escape(source, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy" decoding="async">'

    def table_open(renderer, tokens, idx, options, env):
        return '<div class="table-scroll" role="region" aria-label="文章表格，可横向滚动" tabindex="0"><table>\n'

    def table_close(renderer, tokens, idx, options, env):
        return '</table></div>\n'

    for name, rule in [('fence', fence), ('image', image), ('math_inline', inline_math),
                       ('math_block', block_math), ('math_inline_double', double_math),
                       ('table_open', table_open), ('table_close', table_close)]:
        md.add_render_rule(name, rule)
    tokens = md.parse(text)
    for index, token in enumerate(tokens):
        if token.type == 'heading_open':
            level = int(token.tag[1:])
            anchor = f'section-{len(toc)+1}'
            token.attrSet('id', anchor)
            title = md.renderer.renderInlineAsText(tokens[index+1].children or [], md.options, {})
            toc.append((anchor, title, level))
    return md.renderer.render(tokens, md.options, {}), toc

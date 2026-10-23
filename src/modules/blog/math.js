import katex from './vendor/katex/katex.mjs';

export function renderMath(element) {
  const source = element.textContent;
  element.classList.remove('math-error');
  const displayMode = element.classList.contains('math-display') || element.classList.contains('math-inline-display');
  try {
    katex.render(source, element, {
      displayMode,
      output: 'htmlAndMathml',
      throwOnError: false,
      trust: false,
      strict: 'ignore',
      maxExpand: 1000,
      maxSize: 20,
      errorColor: '#9d2929',
    });
    if (element.querySelector('.katex-error')) element.classList.add('math-error');
  } catch {
    element.textContent = source;
    element.classList.add('math-error');
    element.title = '公式未能排版，请检查 LaTeX 语法';
  }
}

for (const element of document.querySelectorAll('.prose [data-math]')) renderMath(element);

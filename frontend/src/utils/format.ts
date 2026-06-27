/**
 * 将 Markdown 文本转换为 HTML
 * 支持：标题、粗体、斜体、列表、代码块、换行等基础语法
 */
export function markdownToHtml(text: string): string {
  if (!text) return ''

  let html = text

  // 1. 先保护代码块，避免内部内容被转义或替换
  const codeBlocks: string[] = []
  html = html.replace(/```([\s\S]*?)```/g, (_match, code) => {
    codeBlocks.push(code)
    return `\x00CODE_BLOCK_${codeBlocks.length - 1}\x00`
  })

  // 2. 保护行内代码
  const inlineCodes: string[] = []
  html = html.replace(/`([^`]+)`/g, (_match, code) => {
    inlineCodes.push(code)
    return `\x00INLINE_CODE_${inlineCodes.length - 1}\x00`
  })

  // 3. 转义 HTML 特殊字符（防止 XSS）
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 4. 标题（支持前面有空格，支持 # 后无空格的情况）
  html = html.replace(/^[ \t]*#{3}[ \t]?(.*)$/gim, '<h3>$1</h3>')
  html = html.replace(/^[ \t]*#{2}[ \t]?(.*)$/gim, '<h2>$1</h2>')
  html = html.replace(/^[ \t]*#{1}[ \t]?(.*)$/gim, '<h1>$1</h1>')

  // 5. 粗体 **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // 6. 斜体 *text*（排除已经是**的情况）
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')

  // 7. 无序列表
  const lines = html.split('\n')
  let inList = false
  let result: string[] = []

  for (const line of lines) {
    const trimmed = line.trim()
    if (/^[-*+][ \t]+(.+)/.test(trimmed)) {
      if (!inList) {
        result.push('<ul>')
        inList = true
      }
      const item = trimmed.replace(/^[-*+][ \t]+(.+)/, '$1')
      result.push(`<li>${item}</li>`)
    } else if (inList && trimmed === '') {
      // 列表中的空行，忽略
      result.push(line)
    } else {
      if (inList) {
        result.push('</ul>')
        inList = false
      }
      result.push(line)
    }
  }
  if (inList) result.push('</ul>')
  html = result.join('\n')

  // 8. 有序列表
  let inOrderedList = false
  const orderedResult: string[] = []
  for (const line of html.split('\n')) {
    const trimmed = line.trim()
    if (/^\d+\.[ \t]+(.+)/.test(trimmed)) {
      if (!inOrderedList) {
        orderedResult.push('<ol>')
        inOrderedList = true
      }
      const item = trimmed.replace(/^\d+\.[ \t]+(.+)/, '$1')
      orderedResult.push(`<li>${item}</li>`)
    } else if (inOrderedList && trimmed === '') {
      orderedResult.push(line)
    } else {
      if (inOrderedList) {
        orderedResult.push('</ol>')
        inOrderedList = false
      }
      orderedResult.push(line)
    }
  }
  if (inOrderedList) orderedResult.push('</ol>')
  html = orderedResult.join('\n')

  // 9. 分隔线 ---
  html = html.replace(/^[ \t]*-{3,}[ \t]*$/gim, '<hr>')

  // 10. 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')

  // 11. 段落：将非标签行包裹在 <p> 中
  const finalLines: string[] = []
  const blockTags = ['<h1', '<h2', '<h3', '<ul', '<ol', '<li', '</ul>', '</ol>', '</li>', '<hr', '<pre', '<code', '<div', '</div>', '<p', '</p>']
  for (const line of html.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) {
      // 空行转换为段落间距
      finalLines.push('')
      continue
    }
    const isTag = blockTags.some(tag => trimmed.startsWith(tag))
    if (!isTag) {
      finalLines.push(`<p>${trimmed}</p>`)
    } else {
      finalLines.push(line)
    }
  }
  html = finalLines.join('\n')

  // 12. 处理连续空行和换行
  html = html.replace(/\n+/g, '\n')
  html = html.replace(/\n/g, '')

  // 13. 恢复代码块
  html = html.replace(/\x00CODE_BLOCK_(\d+)\x00/g, (_match, idx) => {
    const code = codeBlocks[parseInt(idx)]
    return `<pre><code>${escapeHtml(code)}</code></pre>`
  })

  // 14. 恢复行内代码
  html = html.replace(/\x00INLINE_CODE_(\d+)\x00/g, (_match, idx) => {
    const code = inlineCodes[parseInt(idx)]
    return `<code>${escapeHtml(code)}</code>`
  })

  return html
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/**
 * 格式化纯文本内容为 HTML（保留换行和空格）
 */
export function formatTextToHtml(text: string): string {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
    .replace(/  /g, ' &nbsp;')
}

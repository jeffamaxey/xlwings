import re

__all__ = ['plugin_task_lists']


TASK_LIST_ITEM = re.compile(r'^(\[[ xX]\])\s+')


def task_lists_hook(md, tokens, state):
    return _rewrite_all_list_items(tokens)


def render_ast_task_list_item(children, level, checked):
    return {
        'type': 'task_list_item',
        'children': children,
        'level': level,
        'checked': checked,
    }


def render_html_task_list_item(text, level, checked):
    checkbox = (
        '<input class="task-list-item-checkbox" '
        'type="checkbox" disabled'
    )
    checkbox += ' checked/>' if checked else '/>'
    if text.startswith('<p>'):
        text = text.replace('<p>', f'<p>{checkbox}', 1)
    else:
        text = checkbox + text

    return f'<li class="task-list-item">{text}' + '</li>\n'


def plugin_task_lists(md):
    md.before_render_hooks.append(task_lists_hook)

    if md.renderer.NAME == 'html':
        md.renderer.register('task_list_item', render_html_task_list_item)
    elif md.renderer.NAME == 'ast':
        md.renderer.register('task_list_item', render_ast_task_list_item)


def _rewrite_all_list_items(tokens):
    for tok in tokens:
        if tok['type'] == 'list_item':
            _rewrite_list_item(tok)
        if 'children' in tok.keys():
            _rewrite_all_list_items(tok['children'])
    return tokens


def _rewrite_list_item(item):
    if not (children := item['children']):
        return
    first_child = children[0]
    text = first_child.get('text', '')
    if m := TASK_LIST_ITEM.match(text):
        mark = m.group(1)
        first_child['text'] = text[m.end():]

        params = item['params']
        params = (params[0], False) if mark == '[ ]' else (params[0], True)
        item['type'] = 'task_list_item'
        item['params'] = params

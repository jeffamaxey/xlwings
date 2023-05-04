from .base import Directive


class Admonition(Directive):
    SUPPORTED_NAMES = {
        "attention", "caution", "danger", "error", "hint",
        "important", "note", "tip", "warning",
    }

    def parse(self, block, m, state):
        if options := self.parse_options(m):
            return {
                'type': 'block_error',
                'raw': 'Admonition has no options'
            }
        name = m.group('name')
        title = m.group('value')
        text = self.parse_text(m)

        rules = list(block.rules)
        rules.remove('directive')
        children = block.parse(text, state, rules)
        return {
            'type': 'admonition',
            'children': children,
            'params': (name, title)
        }

    def __call__(self, md):
        for name in self.SUPPORTED_NAMES:
            self.register_directive(md, name)

        if md.renderer.NAME == 'html':
            md.renderer.register('admonition', render_html_admonition)
        elif md.renderer.NAME == 'ast':
            md.renderer.register('admonition', render_ast_admonition)


def render_html_admonition(text, name, title=""):
    html = f'<section class="admonition {name}' + '">\n'
    if not title:
        title = name.capitalize()
    if title:
        html += f'<p class="admonition-title">{title}' + '</p>\n'
    if text:
        html += text
    return html + '</section>\n'


def render_ast_admonition(children, name, title=""):
    return {
        'type': 'admonition',
        'children': children,
        'name': name,
        'title': title,
    }

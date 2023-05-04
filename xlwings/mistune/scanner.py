import re

class Scanner(re.Scanner):
    def iter(self, string, state, parse_text):
        sc = self.scanner.scanner(string)

        pos = 0
        for match in iter(sc.search, None):
            name, method = self.lexicon[match.lastindex - 1][1]
            if hole := string[pos : match.start()]:
                yield parse_text(hole, state)

            yield method(match, state)
            pos = match.end()

        if hole := string[pos:]:
            yield parse_text(hole, state)


class ScannerParser(object):
    scanner_cls = Scanner
    RULE_NAMES = tuple()

    def __init__(self):
        self.rules = list(self.RULE_NAMES)
        self.rule_methods = {}
        self._cached_sc = {}

    def register_rule(self, name, pattern, method):
        self.rule_methods[name] = (pattern, lambda m, state: method(self, m, state))

    def get_rule_pattern(self, name):
        if name not in self.RULE_NAMES:
            return self.rule_methods[name][0]
        return getattr(self, name.upper())

    def get_rule_method(self, name):
        if name not in self.RULE_NAMES:
            return self.rule_methods[name][1]
        return getattr(self, f'parse_{name}')

    def parse_text(self, text, state):
        raise NotImplementedError

    def _scan(self, s, state, rules):
        sc = self._create_scanner(rules)
        for tok in sc.iter(s, state, self.parse_text):
            if isinstance(tok, list):
                yield from tok
            elif tok:
                yield tok

    def _create_scanner(self, rules):
        sc_key = '|'.join(rules)
        sc = self._cached_sc.get(sc_key)
        if sc:
            return sc

        lexicon = [
            (self.get_rule_pattern(n), (n, self.get_rule_method(n)))
            for n in rules
        ]
        sc = self.scanner_cls(lexicon)
        self._cached_sc[sc_key] = sc
        return sc


class Matcher(object):
    PARAGRAPH_END = re.compile(
        r'(?:\n{2,})|'
        r'(?:\n {0,3}#{1,6})|'  # axt heading
        r'(?:\n {0,3}(?:`{3,}|~{3,}))|'  # fenced code
        r'(?:\n {0,3}>)|'  # blockquote
        r'(?:\n {0,3}(?:[\*\+-]|1[.)]))|'  # list
        r'(?:\n {0,3}<)'  # block html
    )

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def search_pos(self, string, pos):
        if m := self.PARAGRAPH_END.search(string, pos):
            return m.end() if set(m.group(0)) == {'\n'} else m.start() + 1
        else:
            return None

    def iter(self, string, state, parse_text):
        pos = 0
        endpos = len(string)
        last_end = 0
        while 1:
            if pos >= endpos:
                break
            for rule, (name, method) in self.lexicon:
                match = rule.match(string, pos)
                if match is not None:
                    start, end = match.span()
                    if start > last_end:
                        yield parse_text(string[last_end:start], state)

                    if name.endswith('_start'):
                        token = method(match, state, string)
                        yield token[0]
                        end = token[1]
                    else:
                        yield method(match, state)
                    last_end = pos = end
                    break
            else:
                found = self.search_pos(string, pos)
                if found is None:
                    break
                pos = found

        if last_end < endpos:
            yield parse_text(string[last_end:], state)

from typing import Any


class Terminal(str):
    def __new__(cls, value):
        return str.__new__(cls, value)

    def __str__(self):
        return f'"{str.__str__(self.replace("\\", "\\\\").replace('"', '\\"'))}"'

    def copy(self):
        return self


class NonTerminal:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"<{self.name}>"

    def copy(self):
        return self


class BNFRule:
    @classmethod
    def EmptyRule(cls):
        return cls([])

    def copy(self):
        if isinstance(self, SingleRule):
            return SingleRule([r.copy() for r in self.sequence])
        elif isinstance(self, ParrelRule):
            return ParrelRule([r.copy() for r in self.rules])


class SingleRule(BNFRule):
    def __init__(self, seq: list):
        self.sequence = seq

    def __str__(self):
        return " ".join(map(str, self.sequence))

    @classmethod
    def compile(cls, s, i=0):
        rule = []

        i = i
        while i < len(s):
            if s[i] == "<":
                j = s.find(">", i)

                if j == -1:
                    raise ValueError('Expected ">"')

                rule.append(NonTerminal(s[i + 1 : j]))
                i = j + 1
            elif s[i] == '"':
                j = i + 1
                _slash_cnt = 0
                while True:
                    if j == len(s):
                        raise ValueError('Expected closing "')

                    if s[j] == "\\":
                        _slash_cnt += 1
                    elif s[j] == '"':
                        if _slash_cnt % 2 == 0:
                            break
                        else:
                            j -= 1
                            s = s[:j] + s[j + 1 :]
                            _slash_cnt = 0
                    else:
                        _slash_cnt = 0
                    j += 1

                rule.append(Terminal(s[i + 1 : j]))
                i = j + 1
            elif s[i].isspace():
                i += 1
            elif s[i] in "()[]{}|":
                return cls(rule), i
            else:
                raise ValueError(f'Unexpected character "{s[i]}"')

        return cls(rule), float("inf")

    @classmethod
    def from_str(cls, s):
        rule, i = cls.compile(s)

        # ensure 'single' rule
        if i != float("inf"):
            raise ValueError("Expected EOF")

        return rule

    def merge(self, other):
        if isinstance(other, Terminal) or isinstance(other, NonTerminal):
            self.sequence.append(other)
            return self
        if isinstance(other, SingleRule):
            return SingleRule(self.sequence + other.sequence)
        elif isinstance(other, ParrelRule):
            # add as a parrelrule component
            return SingleRule(self.sequence + [other])
        else:
            raise TypeError(f"Cannot merge SingleRule with {type(other)}")

    def clean(self):
        # Merge two beside terminals
        i = 0
        while i < len(self.sequence) - 1:
            if isinstance(self.sequence[i], Terminal) and isinstance(
                self.sequence[i + 1], Terminal
            ):
                self.sequence[i] = Terminal(self.sequence[i] + self.sequence[i + 1])
                del self.sequence[i + 1]
            else:
                i += 1

        # Flatten parrel rules
        rules = [SingleRule.EmptyRule()]

        def _add_new_rule(new_rule: Any, target: list):
            if isinstance(new_rule, Terminal) or isinstance(new_rule, NonTerminal):
                # minimal unit, merge with all previous branches
                for r in target:
                    r.merge(new_rule)

            elif isinstance(new_rule, SingleRule):
                # single rule will be split into parts
                for part in new_rule.sequence:
                    _add_new_rule(part, target)

            elif isinstance(new_rule, ParrelRule):
                # add new branches
                new_rule = new_rule.clean()
                new_target = []
                for branch in new_rule.rules:
                    target_copy = [r.copy() for r in target]
                    _add_new_rule(branch, target_copy)
                    new_target.extend(target_copy)
                target.clear()
                target.extend(new_target)

            else:
                raise TypeError(f"Cannot merge SingleRule with {type(new_rule)}")

        _add_new_rule(self, rules)

        if len(rules) == 1:
            return rules[0]

        return ParrelRule(rules)


class ParrelRule(BNFRule):
    def __init__(self, rules: list) -> None:
        self.rules = rules

    def __str__(self):
        return "(" + ") | (".join(map(str, self.rules)) + ")"

    @classmethod
    def from_single(cls, single_rule: SingleRule):
        return cls([single_rule])

    @classmethod
    def compile(cls, s: str, i=0):
        rules = []
        current_rule = SingleRule.EmptyRule()
        i = i
        while i < len(s):
            if s[i] in ")]}":
                rules.append(current_rule)
                return cls(rules), i

            # parentheses
            if s[i] == "(":
                i += 1
                rule, i = ParrelRule.compile(s, i)
                current_rule = current_rule.merge(rule)
                i += 1  # skip ')' of the inner level

            # or
            elif s[i] == "|":
                rules.append(current_rule)
                current_rule = SingleRule.EmptyRule()
                i += 1

            # space
            elif s[i].isspace():
                i += 1

            # invalid char
            else:
                rule, i = SingleRule.compile(s, i)
                current_rule = current_rule.merge(rule)

        rules.append(current_rule)
        return cls(rules), float("inf")

    @classmethod
    def from_str(cls, s: str):
        rules, i = cls.compile(s)
        if i != float("inf"):
            raise ValueError("Expected EOF")
        return rules

    def clean(self):
        for i in range(len(self.rules)):
            self.rules[i] = self.rules[i].clean()
        return self


def parse_bnf_rule(s: str):
    return SingleRule([ParrelRule.from_str(s)]).clean()


if __name__ == "__main__":
    # print(SingleRule.from_str('<A> "\\"b"'))  # <A> "b"
    print(parse_bnf_rule('(<A> "b") | (<B>|"c") "d"'))

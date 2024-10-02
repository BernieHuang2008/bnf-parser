class Terminal(str):
    def __new__(cls, value):
        return str.__new__(cls, value)

    def __repr__(self):
        return f'"{self.replace("\\", "\\\\").replace('"', '\\"')}"'


class NonTerminal:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<{self.name}>"


class SingleRule:
    def __init__(self, seq: list):
        self.sequence = seq

    def __str__(self):
        return " ".join(map(repr, self.sequence))

    @classmethod
    def compile(cls, s, i=0):
        rule = []

        i = i
        while i < len(s):
            x = s[i]
            if x == "<":
                j = s.find(">", i)

                if j == -1:
                    raise ValueError('Expected ">"')

                rule.append(NonTerminal(s[i + 1 : j]))
                i = j + 1
            elif x == '"':
                j = i + 1
                _slash_cnt = 0
                while True:
                    if j == len(s):
                        raise ValueError('Expected closing "')

                    if s[j] == "\\":
                        _slash_cnt += 1
                    elif s[j] == "\"":
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
            elif x.isspace():
                i += 1
            elif x in ")]}|":
                return cls(rule), i
            else:
                raise ValueError(f'Unexpected character "{x}"')

        return cls(rule), -1

    @classmethod
    def from_str(cls, s):
        rule, i = cls.compile(s)

        # ensure 'single' rule
        if i != -1:
            raise ValueError("Expected EOF")
        
        return rule

if __name__ == "__main__":
    print(SingleRule.from_str('<A> "\\"b"'))  # <A> "b"

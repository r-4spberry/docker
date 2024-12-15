import lark


class NormalizeTree(lark.Transformer):
    """
    This class normalizes a lark.Tree
    Call .transform() method to get a Lark.Tree
    """

    def sum(self, children):
        s = sorted(
            children, key=str
        )  # Sorting the children based on string representation
        return lark.Tree("sum", s)

    def mul(self, children):
        s = sorted(children, key=str)  # Sorting multiplication terms
        return lark.Tree("mul", s)

    def fraq(self, children):
        return lark.Tree("fraq", children)

    def sub(self, children):
        return lark.Tree("sub", children)

    def pow(self, children):
        return lark.Tree("pow", children)

    def log(self, children):
        return lark.Tree("log", children)

    def num(self, children):
        return lark.Tree("num", children)

    def var(self, children):
        return lark.Tree("var", children)

import lark
from lark import Tree, Token
from .normalize import NormalizeTree


class MyParser:
    "This class parses a string with custom grammar into a lark.Tree"

    def __init__(self):

        self.grammar: str = """
        start: expr

        ?expr: term
            | "sum(" expr ("," expr)* ")" -> sum
            | "sub(" expr "," expr ")" -> sub
            | "mul(" expr ("," expr)* ")" -> mul
            | "fraq(" expr "," expr ")" -> fraq
            | "pow(" expr "," expr ")" -> pow
            | "integral(" expr "," expr "," expr ")" -> integral
            | "log(" expr "," expr ")" -> log
            | "udf(" funname "," expr ("," expr)* ")" -> udf
            
            

        ?term: num -> num
            | var -> var

        ?var: "var(" VARFUNNAME ")"
        
        ?funname: VARFUNNAME -> funname
        
        ?num: "num(" NUMBER ")"

        NUMBER: DECIMAL|FLOAT
        
        DECIMAL : /-?(0|[1-9]\d*)/i
        FLOAT: /-?(((\d+\.\d*|\.\d+)(e[-+]?\d+)?|\d+(e[-+]?\d+)))/i
        VARFUNNAME: /[^(),\s]+/





        
        %import common.CNAME
        %import common.LCASE_LETTER
        %import common.WS
        %ignore WS
    """

    def parse(self, str_in: str) -> lark.Tree:
        """
        function used to parse a grammar into Lark.Tree
        """
        ret: lark.Tree

        parser = lark.Lark(grammar=self.grammar)
        ret = parser.parse(str_in)
        return ret

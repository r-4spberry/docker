from typing import List
from .my_parser import MyParser
from copy import deepcopy
from lark import Tree, Token
from .equiv import Equiv
from .normalize import NormalizeTree


class SearchNode:
    def __repr__(self):
        return SearchNode.equationRepr(self.tree)

    def __str__(self):
        return SearchNode.equationRepr(self.tree)

    @staticmethod
    def equationRepr(tree: Tree):
        """
        returns a representation of an equation in form of (a+b+c*d+e)
        """
        arr = []
        ans = ""
        for ch in tree.children:
            if isinstance(ch, Tree):
                arr.append(ch)
        if tree.data == "sum":
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "+" + SearchNode.equationRepr(ch)
            ans = ans + ")"
        elif tree.data == "mul":
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "*" + SearchNode.equationRepr(ch)
            ans = ans + ")"
        elif tree.data == "fraq":
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "/" + SearchNode.equationRepr(ch)
            ans = ans + ")"
        elif tree.data == "sub":
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "-" + SearchNode.equationRepr(ch)
            ans = ans + ")"
        elif tree.data == "pow":
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "**" + SearchNode.equationRepr(ch)
            ans = ans + ")"

        elif tree.data == "log":
            ans = ans + "log("
            ans = ans + SearchNode.equationRepr(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.equationRepr(ch)
            ans = ans + ")"

        elif tree.data == "udf":
            ans = ans + arr[0].children[0]
            ans = ans + "("
            ans = ans + SearchNode.equationRepr(arr[1])
            for ch in arr[2::]:
                ans = ans + "," + SearchNode.equationRepr(ch)
            ans = ans + ")"
        elif tree.data == "var":
            ans = tree.children[0]
        elif tree.data == "num":
            ans = tree.children[0]
        else:
            ans = "???"

        return ans

    @staticmethod
    def getGrammarString_static(tree):
        "called from inside .getGrammarString()"
        arr = []
        ans = ""
        for ch in tree.children:
            if isinstance(ch, Tree):
                arr.append(ch)
        if tree.data == "sum":
            ans = ans + "sum"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "mul":
            ans = ans + "mul"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "fraq":
            ans = ans + "fraq"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"

        elif tree.data == "log":
            ans = ans + "log"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "sub":
            ans = ans + "sub"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "pow":
            ans = ans + "pow"
            ans = ans + "("
            ans = ans + SearchNode.getGrammarString_static(arr[0])
            for ch in arr[1::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "udf":
            ans = ans + "udf"
            ans = ans + "("
            ans = ans + arr[0].children[0]
            ans = ans + ","
            ans = ans + SearchNode.getGrammarString_static(arr[1])
            for ch in arr[2::]:
                ans = ans + "," + SearchNode.getGrammarString_static(ch)
            ans = ans + ")"
        elif tree.data == "var":
            ans = "var(" + tree.children[0] + ")"
        elif tree.data == "num":
            ans = "num(" + tree.children[0] + ")"
        else:
            ans = "???"

        return ans

    def getGrammarStringRepr(self):
        """
        returns a representation of an equation in form of sum(var(a),num(9),var(g))
        """
        return SearchNode.getGrammarString_static(self.tree)

    def __init__(self, equation_or_ancestor):
        parser: MyParser = MyParser()
        if isinstance(equation_or_ancestor, str):
            self.tree: Tree = parser.parse(equation_or_ancestor).children[0]
        elif isinstance(equation_or_ancestor, SearchNode):
            # self.tree: Tree = deepcopy(equation_or_ancestor.tree)
            self.tree: Tree = Tree(
                equation_or_ancestor.tree.data, equation_or_ancestor.tree.children
            )
        elif isinstance(equation_or_ancestor, Tree):
            # self.tree: Tree = deepcopy(equation_or_ancestor)
            self.tree: Tree = Tree(
                equation_or_ancestor.data, equation_or_ancestor.children
            )
        else:
            raise TypeError("Expected a string or a Tree")
        self.normalize()
        self.elemRefs: List[Tree] = self.getElementsReferences(self.tree)
        self.elemEquivs: List[Tree] = []
        self.childNodes: List[SearchNode] = []
        self.ancestorNode = None
        self.expanded: bool = False

    def getAllElemEquivalents(self, arr: List[Tree]) -> List[Tree]:
        """
        returns a list of lists
        in each inner list are equivalents of a corresponding vertex of a Lar.Tree
        """
        ret: List[Tree] = []
        for ref in self.elemRefs:
            ret.append(Equiv.getEquiv(ref))

        return ret

    def getElementsReferences(self, curTree: Tree) -> List[Tree]:
        """
        returns list with references to all vertexes o a Lark.Tree of a node
        """
        arr = []
        arr = arr + [curTree]
        if isinstance(curTree, Tree):
            for child in curTree.children:
                arr = arr + self.getElementsReferences(child)
        return arr

    def getChildNodes(self) -> List:
        """computes all possible equivalents of a tree and returns them in a list.
        DOES NOT ADD them to childNodes of a node"""
        ret: List[SearchNode] = []
        for numRef in range(len(self.elemRefs)):
            for numEq in range(len(self.elemEquivs[numRef])):
                nextChild: SearchNode = SearchNode(self)
                nextChild.elemRefs[numRef].data = self.elemEquivs[numRef][numEq].data
                nextChild.elemRefs[numRef].children = deepcopy(
                    self.elemEquivs[numRef][numEq].children
                )
                ret.append(nextChild)
        for i in ret:
            i.normalize()
            i.recalculateEquivalents()
        return ret

    def findChildNodes(self) -> None:
        "computes all possible equivalents of a tree. adds them to childNodes of a node"
        self.elemEquivs: List[Tree] = self.getAllElemEquivalents(self.elemRefs)
        self.childNodes = self.getChildNodes()
        for node in self.childNodes:
            node.setAncestor(self)

    def setAncestor(self, ancestor: "SearchNode"):
        """
        sets an ancestor of a node
        """
        if not isinstance(ancestor, SearchNode):
            raise TypeError("Expected SearchNode")
        self.ancestorNode = ancestor

    def normalize(self):
        """
        Normalizes a Lark.Tree object of a SearchNode
        Normalization is conducted only for operations non-sensitive to the order of operands
        Otherwise the operation is left unchanged
        """
        normalizer: NormalizeTree = NormalizeTree()
        self.tree = normalizer.transform(self.tree)

    def recalculateEquivalents(self):
        """
        Recalculates equivalents of each vertex in a Lark.Tree object of a SearchNode
        Also updates references of the elements
        """
        self.elemRefs = self.getElementsReferences(self.tree)
        self.elemEquivs = self.getAllElemEquivalents(self.elemRefs)

    def forestPretty(self, depth: int = 3, curDepth: int = 0) -> str:
        """
        Shows a visual representation of a search tree up to a certain depth
        depth - depth
        curDepth - do not use, used for recursion
        """
        ret = "\t" * curDepth + self.__str__() + "\n"
        if curDepth < depth:
            for ch in self.childNodes:
                ret += ch.forestPretty(depth, curDepth + 1)
        elif len(self.childNodes) != 0:
            ret += "\t" * (curDepth + 1) + "..." + "\n"

        return ret

    def lineagePretty(self, depth=5, curDepth=0) -> str:
        """
        Shows a visual representation of SearchNode's ancestors up to a certain depth
        depth - depth
        curDepth - do not use, used for recursion
        """
        ret = ""
        ret = ret + curDepth * "\t" + self.__str__() + "\n"
        if self.ancestorNode is not None and depth > 0:
            ret = ret + self.ancestorNode.lineagePretty(depth - 1, curDepth + 1)
        elif self.ancestorNode is None:
            ret = ret + (curDepth + 1) * "\t" + "END OF LINEAGE" + "\n"
        else:
            ret = ret + (curDepth + 1) * "\t" + "..." + "\n"
        return ret

    def replaceVariable(self, varToSub: Tree, varToSubWith: Tree) -> None:
        """
        replaces all the instances of a variable in an equation to a different variable
        """
        for elem in self.elemRefs:
            if elem == varToSub:
                elem.data = varToSubWith.data
                elem.children = deepcopy(varToSubWith.children)
        # self.elemRefs: List[Tree] = self.getElementsReferences(self.tree)

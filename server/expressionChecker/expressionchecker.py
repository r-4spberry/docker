from typing import AnyStr
from typing import List
from typing import Dict
from typing import Tuple
from .searchnode import SearchNode
from collections import defaultdict
from copy import deepcopy
from .normalize import NormalizeTree
import heapq
from .metrics import Metrics
from lark import Tree, Token


class ExpressionChecker:
    """
    A class used to check if equations can be derived from one another
    """

    def __init__(
        self, str1: AnyStr, str2: AnyStr, searchUpToVariablesSubstitution=False
    ):
        self.searchUpToVariablesSubstitution: bool = searchUpToVariablesSubstitution
        self.heap: List[ExpressionChecker.heapEntry] = []
        "used to store pair of equations and a metric associated with them"
        heapq.heapify(self.heap)

        self.eqMap: Dict[Tree, ExpressionChecker.mapEntry] = dict()
        "used to store representations of trees and if they were found from each root"

        self.initial_str1: str = str1
        self.initial_str2: str = str2

        self.forest1: SearchNode = SearchNode(self.initial_str1)
        self.forest2: SearchNode = SearchNode(self.initial_str2)

        # self.addEqToMap(self.forest1, 1)
        # self.addEqToMap(self.forest2, 2)

        self.strRepr1: str = self.forest1.__str__()
        self.strRepr2: str = self.forest2.__str__()

        self.addToHeap(self.forest1, self.forest2)

        self.lowestDistanceBetweenStr: int = self.heap[0].distance
        self.close1: SearchNode = self.heap[0].node1
        self.close2: SearchNode = self.heap[0].node2

        self.foundEquivalent = False

    class mapEntry:
        """
        entry of a map where the all previously accessed trees lark,Trees are located
        repr - string representation of lark.tree
        node1, node2 - references to some tree in first or second forest that are already visited
        if node1 or node2 is none, then this tree was not accessed from corresponding forest
        """

        def __init__(self, repr: str):
            self.repr: str = repr
            self.node1: SearchNode = None
            self.node2: SearchNode = None

        def __repr__(self):
            ret = "("
            ret = ret + self.repr
            if self.node1 is not None:
                ret = ret + " node1"
            else:
                ret = ret + "  None"

            if self.node2 is not None:
                ret = ret + " node2"
            else:
                ret = ret + "  None"
            ret = ret + ")"
            return ret

    class heapEntry:
        """
        entry of a heap where the next pair of equations to expand is calculated
        metricValue - a value according to which the position in a heap is determined
        distance - a value showing how far away 2 equations are, different from metricValue
        node1, node2 - references to 2 nodes to expand
        """

        def __init__(
            self, eq1: SearchNode, eq2: SearchNode, metric: int, distance: int
        ):
            self.metricValue: int = metric
            self.node1: SearchNode = eq1
            self.node2: SearchNode = eq2
            self.distance: int = distance

        def __lt__(self, other):
            return self.metricValue < other.metricValue

        def __eq__(self, other):
            return self.metricValue == other.metricValue

        def __repr__(self):
            ret = "("
            ret = ret + str(self.metricValue)
            ret = ret + " "
            ret = ret + self.node1.__str__()
            ret = ret + " "
            ret = ret + self.node2.__str__()
            ret = ret + ")"
            return ret

    def addToHeap(
        self,
        eq1: SearchNode,
        eq2: SearchNode,
        metric: callable = Metrics.levenshteinMetric,
    ) -> None:
        """
        adds a pair of SearchNodes to heap keeping the heap order
        """
        streq1: str = ""
        streq2: str = ""

        if eq1 in self.eqMap:
            streq1 = self.eqMap[eq1.tree].repr
        else:
            streq1 = eq1.__str__()

        if eq2 in self.eqMap:
            streq2 = self.eqMap[eq2.tree].repr
        else:
            streq2 = eq2.__str__()

        distance: int = metric(streq1, streq2) / (max(len(streq1), len(streq2)))
        metricValue: int = (
            metric(self.strRepr1, streq1)
            + metric(streq1, streq2)
            + metric(streq2, self.strRepr2)
        )

        value: ExpressionChecker.heapEntry = ExpressionChecker.heapEntry(
            eq1, eq2, metricValue, distance
        )
        heapq.heappush(self.heap, value)

    def getPairWithLowestMetric(self) -> "ExpressionChecker.heapEntry":
        """
        returns a pair from the top of the heap
        """
        try:
            ret: ExpressionChecker.heapEntry = heapq.heappop(self.heap)
        except IndexError as e:
            ret: ExpressionChecker.heapEntry = ExpressionChecker.heapEntry(
                None, None, 99999999999, 99999999999
            )

        return ret

    def addEqToMap(self, eq: SearchNode, first_or_second: int) -> None:
        """
        adds a SearchNode to the map of previously used/visited nodes
        Maps by the tree of a node, not by the node itself
        eq - node to add
        first_or_second - determines whenever the map entry will be  marked as accessed from
        the first equation or the second equation
        """
        if eq.tree not in self.eqMap:
            self.eqMap[eq.tree] = ExpressionChecker.mapEntry(eq.__str__())

        if first_or_second == 1:
            self.eqMap[eq.tree].node1 = eq
        elif first_or_second == 2:
            self.eqMap[eq.tree].node2 = eq

    def search(self, numIter: int = 100):
        """
        It is an iterator,
        return[0] - state (p - progress, n - not found, f - found),
        return[1] - distance between strings in range [0 - 1],
        return[2] - node descended from str1,
        return[3] - node descended from str2,
        """
        iteration: int = 1

        while True:
            # search has been copmlete, equivalence found
            if self.foundEquivalent:
                yield ("f", 1 - self.lowestDistanceBetweenStr, self.close1, self.close2)
                continue

            # search is in progress - can continue
            if iteration % numIter == 0:
                yield ("p", 1 - self.lowestDistanceBetweenStr, self.close1, self.close2)
                continue

            heapEntry = self.getPairWithLowestMetric()

            # search has been complete, no equivalence found
            if (heapEntry.node1 is None) and (heapEntry.node2 is None):
                yield ("n", 1 - self.lowestDistanceBetweenStr, self.close1, self.close2)
                continue

            # try to get equality up to a variables
            if self.searchUpToVariablesSubstitution:
                if (heapEntry.node1 is not None) and (heapEntry.node2 is not None):
                    (upToVariables1, upToVariables2) = (
                        ExpressionChecker.getEqualUpToVariables(
                            heapEntry.node1, heapEntry.node2
                        )
                    )
                    if (upToVariables1 is not None) and (upToVariables2 is not None):
                        upToVariables1.ancestorNode = heapEntry.node1
                        heapEntry.node1.childNodes.append(upToVariables1)
                        upToVariables2.ancestorNode = heapEntry.node2
                        heapEntry.node2.childNodes.append(upToVariables2)
                        self.close1 = upToVariables1
                        self.close2 = upToVariables2
                        self.lowestDistanceBetweenStr = 0
                        self.foundEquivalent = True

            if heapEntry.distance < self.lowestDistanceBetweenStr:
                self.close1 = heapEntry.node1
                self.close2 = heapEntry.node2
                self.lowestDistanceBetweenStr = heapEntry.distance

            exp1: bool = False
            exp2: bool = False

            # expanding all children of node1
            if not heapEntry.node1.expanded:
                exp1 = True
                n = heapEntry.node1
                if (n.tree not in self.eqMap) or (self.eqMap[n.tree].node1 is None):
                    n.findChildNodes()

            # expanding all children of node2
            if not heapEntry.node2.expanded:
                exp2 = True
                n = heapEntry.node2
                if (n.tree not in self.eqMap) or (self.eqMap[n.tree].node2 is None):
                    n.findChildNodes()

            # adding node1 to map
            self.addEqToMap(heapEntry.node1, 1)

            # adding node2 to map
            self.addEqToMap(heapEntry.node2, 2)

            # updating the heap with node1
            if not heapEntry.node1.expanded:
                temp = heapEntry.node1.childNodes + [heapEntry.node1]
                for ch1 in temp:
                    for k in self.eqMap:
                        if self.eqMap[k].node2 is not None:
                            self.addToHeap(ch1, self.eqMap[k].node2)

            # updating the heap with node2
            if not heapEntry.node2.expanded:
                temp = heapEntry.node2.childNodes + [heapEntry.node2]
                for ch2 in temp:
                    for k in self.eqMap:
                        if self.eqMap[k].node1 is not None:
                            self.addToHeap(self.eqMap[k].node1, ch2)

            # marking both nodes expanded
            heapEntry.node1.expanded = True
            heapEntry.node2.expanded = True

            if exp1 or exp2:
                iteration += 1

            # checking if we found an equivalence
            if heapEntry.node1 is not None and (heapEntry.node1.tree in self.eqMap):
                mapEntry: ExpressionChecker.mapEntry = self.eqMap[heapEntry.node1.tree]
                if (mapEntry.node1 is not None) and (mapEntry.node2 is not None):
                    self.close1 = mapEntry.node1
                    self.close2 = mapEntry.node2
                    self.lowestDistanceBetweenStr = 0
                    self.foundEquivalent = True
                    continue

            if heapEntry.node1 is not None and (heapEntry.node1.tree in self.eqMap):
                mapEntry: ExpressionChecker.mapEntry = self.eqMap[heapEntry.node2.tree]
                if (mapEntry.node1 is not None) and (mapEntry.node2 is not None):
                    self.close1 = mapEntry.node1
                    self.close2 = mapEntry.node2
                    self.lowestDistanceBetweenStr = 0
                    self.foundEquivalent = True
                    continue

    @staticmethod
    def getEqualUpToVariables(
        eq1: SearchNode, eq2: SearchNode
    ) -> Tuple[SearchNode, SearchNode]:
        """
        Looks for a fitting substitution of variables that will lead to the same equation
        if found, returns 2 search nodes - for first and second equation respectively.
        Otherwise returns (None, None)
        """
        varArr1: List[Tree] = []
        varArr2: List[Tree] = []
        varArrSub1: List[Tree] = []
        varArrSub2: List[Tree] = []
        varArrSub3: List[Tree] = []

        eq1_res: SearchNode = None
        eq2_res: SearchNode = None

        eq1_copy: SearchNode = None
        eq2_copy: SearchNode = None

        for ref in eq1.elemRefs:
            if isinstance(ref, Tree) and ref.data == "var":
                if ref not in varArr1:
                    varArr1 = varArr1 + [ref]

        for ref in eq2.elemRefs:
            if isinstance(ref, Tree) and ref.data == "var":
                if ref not in varArr2:
                    varArr2 = varArr2 + [ref]

        # are of the same length?
        if len(varArr1) != len(varArr2) and len(varArr1) != 0:
            return (None, None)

        # try to find fitting substitution
        num: int = 0
        for i in range(len(varArr1)):
            sub = Tree("var", [Token("VARFUNNAME", "b_{" + str(num) + "}")])
            while sub in varArr1:
                num += 1
                sub = Tree("var", [Token("VARFUNNAME", "b_{" + str(num) + "}")])
            varArrSub1.append(sub)
            num += 1

        num: int = 0
        for i in range(len(varArr2)):
            sub = Tree("var", [Token("VARFUNNAME", "c_{" + str(num) + "}")])
            while sub in varArr2:
                num += 1
                sub = Tree("var", [Token("VARFUNNAME", "c_{" + str(num) + "}")])
            varArrSub2.append(sub)
            num += 1

        for i in range(len(varArr1)):
            varArrSub3.append(Tree("var", [Token("VARFUNNAME", "a_{" + str(i) + "}")]))

        eq1_res: SearchNode = SearchNode(eq1)
        eq2_res: SearchNode = SearchNode(eq2)

        # changing variables to a_{1} and b_{1}
        for i in range(len(varArr1)):
            eq1_res.replaceVariable(varArr1[i], varArrSub1[i])
            eq2_res.replaceVariable(varArr2[i], varArrSub2[i])

        varArr1 = varArrSub1
        varArr2 = varArrSub2

        dummyVar: Tree = Tree("var", [Token("VARFUNNAME", "d")])

        # number of variables we substitute
        while len(varArr1) != 0:
            found: bool = False
            sub: Tree = varArrSub3[0]
            subIn1: Tree = None
            subIn2: Tree = None
            eq1_copy = SearchNode(eq1_res)
            eq1_copy.replaceVariable(varArr1[0], sub)
            for i in range(1, len(varArr1)):
                eq1_copy.replaceVariable(varArr1[i], dummyVar)
            for elem in varArr2:
                eq2_copy = SearchNode(eq2_res)
                eq2_copy.replaceVariable(elem, sub)
                for j in range(len(varArr2)):
                    if elem != varArr2[j]:
                        eq2_copy.replaceVariable(varArr2[j], dummyVar)
                eq1_copy.normalize()
                eq2_copy.normalize()
                if eq2_copy.tree == eq1_copy.tree:
                    subIn1 = varArr1[0]
                    subIn2 = elem
                    found = True

                    varArr1.remove(subIn1)
                    varArr2.remove(subIn2)
                    varArrSub3.remove(sub)

                    break
            if found:
                eq1_res.replaceVariable(subIn1, sub)
                eq2_res.replaceVariable(subIn2, sub)
            else:
                return (None, None)

        eq1_res.normalize()
        eq2_res.normalize()
        if eq1_res.tree != eq2_res.tree:
            return (None, None)

        return (eq1_res, eq2_res)

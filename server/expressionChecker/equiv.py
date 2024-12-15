import lark
from lark import Tree, Token
from .normalize import NormalizeTree
from typing import List


class Equiv:
    "This class is used to produce equivalents of different lark.Trees with our grammar"

    @staticmethod
    def getEquiv(equation: lark.Tree) -> List[lark.Tree]:
        "Function to get equivalents"

        ret: List = []

        if not isinstance(equation, Tree):
            return ret

        ret = ret + Equiv.ruleExpandBrackets(equation)
        ret = ret + Equiv.ruleCombineSum(equation)
        ret = ret + Equiv.ruleCombineMul(equation)
        ret = ret + Equiv.ruleInvertFraq(equation)
        ret = ret + Equiv.ruleMutiplyAllNumbers(equation)
        ret = ret + Equiv.ruleCombinePowers(equation)
        ret = ret + Equiv.ruleSumAllNumbers(equation)
        ret = ret + Equiv.ruleRemoveZerosFromNum(equation)
        ret = ret + Equiv.ruleAddZero(equation)
        ret = ret + Equiv.ruleMultiplyByOne(equation)
        ret = ret + Equiv.ruleDevideNumbers(equation)
        # ret = ret + Equiv.ruleAddPowerOne(equation)
        ret = ret + Equiv.ruleRemovePowerOne(equation)

        return ret

    # @staticmethod
    # def ruleAddPowerOne(equation: Tree) -> List[Tree]:
    #     """
    #     Add a power of 1: x -> x^1
    #     """
    #     ret: List[Tree] = []
    #     if equation.data not in {"pow", "num"}:  # Avoid adding redundant power to numbers or existing powers
    #         power_elem = Tree("pow", [equation, Tree("num", [Token("NUMBER", "1")])])
    #         ret.append(power_elem)
    #     return ret

    @staticmethod
    def ruleRemovePowerOne(equation: Tree) -> List[Tree]:
        """
        Remove a power of 1: x^1 -> x
        """
        ret: List[Tree] = []
        if equation.data == "pow" and len(equation.children) == 2:
            base, exponent = equation.children
            if exponent.data == "num" and float(exponent.children[0].value) == 1:
                ret.append(base)
        return ret

    @staticmethod
    def ruleDevideNumbers(equation: Tree) -> List[Tree]:
        "(a*g*98)/(k*p*2) = (a*g*49)/(k*p)"
        ret: List[Tree] = []
        if equation.data == "fraq":
            numMultUp: int = 0
            numMultDown: int = 0
            mul: float = 1
            up: Tree = equation.children[0]
            down: Tree = equation.children[1]
            upArr: List[Tree] = []
            downArr: List[Tree] = []

            if up.data == "num":
                numMultUp += 1
                mul = mul * float(up.children[0].value)
            elif up.data == "mul":
                for elem in up.children:
                    if elem.data == "num":
                        numMultUp += 1
                        mul = mul * float(elem.children[0].value)
                    else:
                        upArr = upArr + [elem]
            else:
                upArr = [up]

            if down.data == "num":
                numMultDown += 1
                try:
                    mul = mul / float(down.children[0].value)
                except:
                    return []  # division by zero
            elif down.data == "mul":
                for elem in down.children:
                    if elem.data == "num":
                        numMultDown += 1
                        try:
                            mul = mul / float(elem.children[0].value)
                        except:
                            return []  # division by zero
                    else:
                        downArr = downArr + [elem]
            else:
                downArr = [down]

            if (numMultDown > 0) or (numMultUp > 1):
                upArr = upArr + [Tree("num", [Token("NUMBER", str(mul))])]
                if len(upArr) > 1:
                    upElem: Tree = Tree("mul", upArr)
                else:
                    upElem: Tree = upArr[0]

                if len(downArr) > 1:
                    downElem: Tree = Tree("mul", downArr)
                elif len(downArr) == 1:
                    downElem: Tree = downArr[0]
                else:
                    downElem: Tree = None

                if downElem is not None:
                    resElem: Tree = Tree("fraq", [upElem, downElem])
                else:
                    resElem: Tree = upElem

                ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleExpandBrackets(equation: Tree) -> List[Tree]:
        "((a+b+c)*d) = (a*d + b*d + c*d)"
        ret: List[Tree] = []
        if equation.data == "mul":

            ch: List = []
            ch = equation.children

            # Is there a sum in mul? can we expand brackets?
            sumElem: Tree = None
            others: List[Tree] = []

            for elem in ch:
                if sumElem is None:
                    if elem.data == "sum":
                        sumElem = elem
                    else:
                        others.append(elem)
                else:
                    others.append(elem)

            # There is a sum in mul - expanding brackets
            if sumElem is not None:

                resElem: Tree
                resChildren: list[Tree] = []
                for nom in sumElem.children:
                    resChildren.append(Tree("mul", others + [nom]))
                resElem = Tree("sum", resChildren)
                ret.append(resElem)
                # print(resElem.pretty())
                # print("----debug mul ----")

        return ret

    @staticmethod
    def ruleCombineSum(equation: Tree) -> List[Tree]:
        "((a + b) + (c + d)) = (a + b + c + d)"
        ret: List[Tree] = []
        if equation.data == "sum":
            arr: List[Tree] = []
            for ch in equation.children:
                if ch.data == "sum":
                    arr = arr + ch.children
                else:
                    arr.append(ch)
            if len(arr) > len(equation.children):
                resElem: Tree = Tree("sum", arr)
                ret.append(resElem)
            elif len(arr) == 1:
                ret.append(arr[0])

        return ret

    @staticmethod
    def ruleCombineMul(equation: Tree) -> List[Tree]:
        "((a * b) * (c * d)) = (a * b * c * d)"
        ret: List[Tree] = []
        if equation.data == "mul":
            arr: List[Tree] = []
            for ch in equation.children:
                if ch.data == "mul":
                    arr = arr + ch.children
                else:
                    arr.append(ch)
            if len(arr) > len(equation.children):
                resElem: Tree = Tree("mul", arr)
                ret.append(resElem)
            elif len(arr) == 1:
                ret.append(arr[0])

        return ret

    @staticmethod
    def ruleInvertFraq(equation: Tree) -> List[Tree]:
        "(a / b) = (a * (b ** -1))"
        ret: List[Tree] = []
        if equation.data == "fraq" and len(equation.children) == 2:
            arr: List[Tree] = []
            arr = arr + [equation.children[0]]

            powArr: List[Tree] = []
            powArr = powArr + [equation.children[1]]
            powArr = powArr + [Tree("num", [Token("NUMBER", "-1")])]

            arr = arr + [Tree("pow", powArr)]

            resElem: Tree = Tree("mul", arr)

            ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleMutiplyAllNumbers(equation: Tree) -> List[Tree]:
        "(a * 100 * -8 * k) = (-800 * a * k)"
        ret: List[Tree] = []
        if equation.data == "mul":
            arr = []
            nom: int = 1
            numMultipliers: int = 0
            for ch in equation.children:
                if ch.data == "num":
                    val: float = float(ch.children[0].value)
                    nom = nom * val
                    numMultipliers += 1
                else:
                    arr = arr + [ch]

            if nom == 0:
                if numMultipliers > 1 or len(arr) > 0:
                    resElem = Tree("num", [Token("NUMBER", "0")])
                    ret = ret + [resElem]
            elif numMultipliers > 1:

                if nom != 1:
                    arr.append(Tree("num", [Token("NUMBER", str(nom))]))
                elif nom == 1 and len(arr) == 0:
                    arr.append(Tree("num", [Token("NUMBER", str(nom))]))

                if len(arr) == 1:
                    resElem: Tree = arr[0]
                    ret = ret + [resElem]
                elif len(arr) > 1:
                    resElem: Tree = Tree("mul", arr)
                    ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleSumAllNumbers(equation: Tree) -> List[Tree]:
        "(a + 100 + -8 + k) = (92 + a + k)"
        ret: List[Tree] = []
        if equation.data == "sum":
            arr = []
            sum: int = 0
            numAdd: int = 0
            for ch in equation.children:
                if ch.data == "num":
                    val: float = float(ch.children[0].value)
                    sum = sum + val
                    numAdd += 1
                else:
                    arr = arr + [ch]

            if numAdd > 1:

                if sum != 0:
                    arr.append(Tree("num", [Token("NUMBER", str(sum))]))
                elif sum == 0 and len(arr) == 0:
                    arr.append(Tree("num", [Token("NUMBER", str(sum))]))

                if len(arr) == 1:
                    resElem: Tree = arr[0]
                    ret = ret + [resElem]
                elif len(arr) > 1:
                    resElem: Tree = Tree("sum", arr)
                    ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleAddZero(equation: Tree) -> List[Tree]:
        "(a + 0) = (a)"
        ret: List[Tree] = []
        if equation.data == "sum":
            arr = []
            sum: int = 0
            numZeros: int = 0
            for ch in equation.children:
                if ch.data == "num" and float(ch.children[0].value) == 0:
                    numZeros += 1
                else:
                    arr = arr + [ch]

            if numZeros > 0:

                if len(arr) == 0:
                    arr = arr + [Tree("num", [Token("NUMBER", "0")])]

                if len(arr) > 1:
                    resElem = Tree("sum", arr)
                    ret = ret + [resElem]
                elif len(arr) == 1:
                    resElem = arr[0]
                    ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleMultiplyByOne(equation: Tree) -> List[Tree]:
        "((a+b)*1) = (a+b)"
        ret: List[Tree] = []
        if equation.data == "mul":
            arr = []
            numOnes: int = 0
            for ch in equation.children:
                if (ch.data == "num") and (float(ch.children[0].value) == 1):
                    numOnes += 1
                else:
                    arr = arr + [ch]

            if numOnes > 0:
                if len(arr) == 0:
                    arr = arr + [Tree("num", [Token("NUMBER", "1")])]

                if len(arr) > 1:
                    resElem = Tree("mul", arr)
                    ret = ret + [resElem]
                elif len(arr) == 1:
                    resElem = arr[0]
                    ret = ret + [resElem]

        return ret

    @staticmethod
    def ruleCombinePowers(equation: Tree) -> List[Tree]:
        "((a**b) * (a**c) * 888 * (a**67)) = ((a**(b + c + 67)) * 888)"
        ret: List[Tree] = []
        if equation.data == "mul":
            powArr: List[Tree] = []
            nonPowArr: List[Tree] = []

            # divide factors into powers / non-powers
            for ch in equation.children:
                if ch.data == "pow":
                    powArr = powArr + [ch]
                else:
                    nonPowArr = nonPowArr + [ch]

            base: Tree = None

            if len(powArr) > 1:

                # try to find powers with the same base
                for i in range(len(powArr)):
                    if base is not None:
                        break
                    for j in range(i + 1, len(powArr), 1):
                        if base is not None:
                            break
                        if powArr[i].children[0] == powArr[j].children[0]:
                            base = powArr[i].children[0]

                # found powers with the same base - create a new equivalent
                if base is not None:
                    sumArr: List[Tree] = []
                    otherPowArr: List[Tree] = []
                    for ch in powArr:
                        if base == ch.children[0]:
                            sumArr = sumArr + [ch.children[1]]
                        else:
                            otherPowArr = otherPowArr + [ch]

                    if len(sumArr) > 1:
                        powElem: Tree = Tree("pow", [base, Tree("sum", sumArr)])

                        resArr: List[Tree] = nonPowArr + [powElem] + otherPowArr

                        if len(resArr) == 1:
                            retElem = resArr[0]
                            ret = ret + [retElem]
                        elif len(resArr) > 1:
                            retElem = Tree("mul", resArr)
                            ret = ret + [retElem]

        return ret

    @staticmethod
    def ruleRemoveZerosFromNum(equation: Tree) -> List[Tree]:
        "09867.56780000 = 9867.5678"
        ret: List[Tree] = []
        if equation.data == "num":
            tok: Token = equation.children[0]
            num_str: str = tok.value
            num = float(num_str)
            if num.is_integer():
                cleaned_str = str(int(num))
            else:
                cleaned_str = str(num)

            if cleaned_str != num_str:
                resElem = Tree("num", [Token("NUMBER", cleaned_str)])
                ret = ret + [resElem]
        return ret

import re
from sympy.parsing.latex import parse_latex
from sympy import Function, Rational, symbols, Add, Mul, Pow, Integral, log, Eq
from sympy import E, Pow


def transform_equals_to_minus(sympy_expr):
    """Transform '=' in a SymPy expression to '-'."""
    # If the expression is an equation like a = b, replace the Eq() with a subtraction
    if isinstance(sympy_expr, Eq):
        lhs = sympy_expr.lhs
        rhs = sympy_expr.rhs
        return lhs - rhs
    return sympy_expr


def sympy_to_custom(expr):
    """
    Recursively converts a SymPy expression into your custom grammar format.
    """
    if expr.is_Number:
        if isinstance(expr, Rational):
            # Represent rationals using fraq(num(p), num(q)) except when denominator is 1
            if expr.q == 1:
                return f"num({expr.p})"
            return f"fraq(num({expr.p}), num({expr.q}))"
        return f"num({expr})"
    elif expr.is_Symbol:
        return f"var({expr})"
    elif expr == E:  # Handle Euler's number
        return "num(E)"
    elif isinstance(expr, Add):
        args = ", ".join(sympy_to_custom(arg) for arg in expr.args)
        return f"sum({args})"
    elif isinstance(expr, Mul):
        # Handle fractions like a * b**-1
        numerators = []
        denominators = []
        for arg in expr.args:
            if (
                isinstance(arg, Pow) and arg.exp == -1
            ):  # Negative exponent -> denominator
                denominators.append(sympy_to_custom(arg.base))
            else:  # Otherwise, it's a numerator
                numerators.append(sympy_to_custom(arg))
        if denominators:  # If there are denominators, it's a fraction
            numer = (
                "mul(" + ", ".join(numerators) + ")"
                if len(numerators) > 1
                else numerators[0]
            )
            denom = (
                "mul(" + ", ".join(denominators) + ")"
                if len(denominators) > 1
                else denominators[0]
            )
            return f"fraq({numer}, {denom})"
        else:  # Otherwise, it's just a product
            args = ", ".join(sympy_to_custom(arg) for arg in expr.args)
            return f"mul({args})"
    elif isinstance(expr, Pow):
        base, exp = expr.args
        if exp == -1:
            return f"fraq(num(1), {sympy_to_custom(base)})"
        return f"pow({sympy_to_custom(base)}, {sympy_to_custom(exp)})"
    elif isinstance(expr, Integral):
        integrand, *bounds = expr.args
        if len(bounds) == 2:  # Definite integral
            return f"integral({sympy_to_custom(integrand)}, {sympy_to_custom(bounds[0])}, {sympy_to_custom(bounds[1])})"
        else:  # Indefinite integral
            return f"integral({sympy_to_custom(integrand)}, var(x), var(x))"  # Adjust for indefinite
    elif isinstance(expr, log):
        arg, base = expr.args
        return f"log({sympy_to_custom(arg)}, {sympy_to_custom(base)})"
    elif isinstance(expr, Function):
        # Handle unknown or user-defined functions
        func_name = expr.func.__name__
        args = ", ".join(sympy_to_custom(arg) for arg in expr.args)
        return f"udf({func_name}, {args})"
    elif expr.is_Rational:  # Handle simple fractions
        return f"fraq(num({expr.p}), num({expr.q}))"
    else:
        raise ValueError(f"Unsupported SymPy expression: {expr}")


def latex_to_custom(latex):
    cleaned_string = re.sub(r"\\mathrm{(.*?)}", r"\1", latex)
    cleaned_string = re.sub(
        r"{\\bf\s*([a-zA-Z])}", r"\1", cleaned_string
    )  # Handles {\bf ...}
    cleaned_string = re.sub(
        r"\\bf\s*([a-zA-Z])", r"\1", cleaned_string
    )  # Handles \bf ...

    sympy_expr = transform_equals_to_minus(parse_latex(cleaned_string))
    return sympy_to_custom(sympy_expr)


def custom_to_latex(expression):
    """Convert custom grammar-like expressions to LaTeX."""
    # Base cases for different elements
    if expression.startswith("var("):
        # Extract variable name inside var()
        return re.search(r"var\((.*?)\)", expression).group(1)
    if expression.startswith("num("):
        # Extract numeric value inside num()
        return re.search(r"num\((.*?)\)", expression).group(1)
    if expression.startswith("mul("):
        # Handle multiplication: mul(a, b) -> "a \cdot b"
        inner = re.search(r"mul\((.*)\)", expression).group(1)
        terms = split_arguments(inner)
        return " \\cdot ".join(custom_to_latex(term) for term in terms)
    if expression.startswith("sum("):
        # Handle summation: sum(a, b) -> "a + b"
        inner = re.search(r"sum\((.*)\)", expression).group(1)
        terms = split_arguments(inner)
        return " + ".join(custom_to_latex(term) for term in terms)
    if expression.startswith("sub("):
        # Handle subtraction: sub(a, b) -> "a - b"
        inner = re.search(r"sub\((.*)\)", expression).group(1)
        minuend, subtrahend = split_arguments(inner)
        return f"{custom_to_latex(minuend)} - {custom_to_latex(subtrahend)}"
    if expression.startswith("fraq("):
        # Handle fraction: fraq(a, b) -> "\frac{a}{b}"
        inner = re.search(r"fraq\((.*)\)", expression).group(1)
        numerator, denominator = split_arguments(inner)
        return (
            f"\\frac{{{custom_to_latex(numerator)}}}{{{custom_to_latex(denominator)}}}"
        )
    if expression.startswith("pow("):
        # Handle power: pow(a, b) -> "a^{b}"
        inner = re.search(r"pow\((.*)\)", expression).group(1)
        base, exponent = split_arguments(inner)
        return f"{custom_to_latex(base)}^{{{custom_to_latex(exponent)}}}"
    if expression.startswith("integral("):
        # Handle integral: integral(a, b, c) -> "\int_{b}^{c} a \,dx"
        inner = re.search(r"integral\((.*)\)", expression).group(1)
        integrand, lower, upper = split_arguments(inner)
        return f"\\int_{{{custom_to_latex(lower)}}}^{{{custom_to_latex(upper)}}} {custom_to_latex(integrand)} \\,dx"
    if expression.startswith("log("):
        # Handle logarithm: log(a, b) -> "\log_{b}(a)"
        inner = re.search(r"log\((.*)\)", expression).group(1)
        value, base = split_arguments(inner)
        return f"\\log_{{{custom_to_latex(base)}}}({custom_to_latex(value)})"
    # Default case (should not happen for valid input)
    return expression


def split_arguments(arguments):
    """Split arguments in a custom expression, respecting nested parentheses."""
    result = []
    balance = 0
    current = []
    for char in arguments:
        if char == "," and balance == 0:
            result.append("".join(current).strip())
            current = []
        else:
            if char == "(":
                balance += 1
            elif char == ")":
                balance -= 1
            current.append(char)
    if current:
        result.append("".join(current).strip())
    return result


# Example usage
if __name__ == "__main__":
    latex_input = "(5, a+b, c)"  # Replace with your LaTeX input
    # sympy_to_custom(parse_latex(latex_input))
    sympy_expr = latex_to_custom(latex_input)
    print(parse_latex(latex_input))
    print("SymPy Expression:", sympy_expr)
    print("Custom Grammar Format:", sympy_expr)
    print("Reversed latex:", custom_to_latex(sympy_expr))

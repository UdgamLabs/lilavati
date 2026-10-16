"""Run a program written by Lilavati, safely.

Lilavati answers by writing a small Python function (`solution()` or `simple_math_problem()`). Running model-written
code for strangers needs care, because a visitor can try to trick the model into writing something harmful. Three layers:

1. **Structure check (before running).** The program is parsed and allowed only if it uses plain arithmetic,
   variables, functions, loops, conditions, lists/dicts, f-strings, a short list of safe built-ins, and `math`.
   No other imports, no attribute names starting with "_", no open/exec/eval/getattr/globals, no classes, no `with`.
2. **A separate, limited process.** It runs in a fresh Python process with CPU-time, memory, file and process limits
   and a tiny set of built-ins. On macOS it also runs inside `sandbox-exec` (no network, no file writes).
3. **A wall-clock timeout** (default 3 s); huge-number tricks like 10**10**10 are stopped by the CPU limit.

run(code) returns the number the program returns, or None if it is rejected, crashes, times out or returns a non-number.
"""
import ast, json, math, os, subprocess, sys, tempfile

SAFE_CALLS = {"abs", "round", "min", "max", "sum", "int", "float", "len", "range", "pow", "divmod", "sorted", "list",
              "tuple", "dict", "set", "enumerate", "zip", "any", "all", "str", "bool", "reversed", "print"}
SAFE_METHODS = {"append", "extend", "pop", "insert", "remove", "sort", "count", "index", "keys", "values", "items",
                "get", "split", "join", "strip", "replace", "upper", "lower", "is_integer", "add", "update"}
MATH_NAMES = {n for n in dir(math) if not n.startswith("_")}
ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Assign, ast.AugAssign, ast.AnnAssign,
           ast.Expr, ast.Name, ast.Load, ast.Store, ast.Del, ast.Constant, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
           ast.IfExp, ast.If, ast.For, ast.While, ast.Break, ast.Continue, ast.Pass, ast.List, ast.Tuple, ast.Dict, ast.Set,
           ast.Subscript, ast.Slice, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
           ast.Call, ast.keyword, ast.Attribute, ast.Import, ast.ImportFrom, ast.alias, ast.JoinedStr, ast.FormattedValue,
           ast.Starred, ast.Assert, ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context)
MAX_CHARS, MAX_NODES = 6000, 3000


def check_program(code):
    """(True, "") if the program only uses the allowed building blocks, else (False, reason)."""
    if len(code) > MAX_CHARS:
        return False, "program too long"
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"syntax error: {e.msg}"
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_NODES:
        return False, "program too large"
    defined = {n.name for n in nodes if isinstance(n, ast.FunctionDef)}
    from_math = {a.asname or a.name for n in nodes if isinstance(n, ast.ImportFrom) for a in n.names}
    for n in nodes:
        if not isinstance(n, ALLOWED):
            return False, f"not allowed: {type(n).__name__}"
        if isinstance(n, ast.FunctionDef) and n.decorator_list:
            return False, "decorators not allowed"
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            if any(m != "math" for m in mods):
                return False, f"import not allowed: {', '.join(mods)}"
            if isinstance(n, ast.ImportFrom) and any(a.name not in MATH_NAMES for a in n.names):
                return False, "unknown name from math"
        if isinstance(n, ast.Name) and (n.id.startswith("__") or n.id in {"exec", "eval", "compile", "open", "input",
                                                                           "getattr", "setattr", "delattr", "globals",
                                                                           "locals", "vars", "dir", "type", "object",
                                                                           "breakpoint", "help", "memoryview", "bytearray",
                                                                           "bytes", "super", "classmethod", "staticmethod",
                                                                           "property", "exit", "quit", "id", "hash"}):
            return False, f"name not allowed: {n.id}"
        if isinstance(n, ast.Attribute):
            if n.attr.startswith("_"):
                return False, "private attribute"
            is_math = isinstance(n.value, ast.Name) and n.value.id == "math"
            if is_math and n.attr not in MATH_NAMES:
                return False, f"unknown math name: {n.attr}"
            if not is_math and n.attr not in SAFE_METHODS:
                return False, f"method not allowed: {n.attr}"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id not in SAFE_CALLS and n.func.id not in defined and n.func.id not in from_math:
            return False, f"call not allowed: {n.func.id}"
    if not defined:
        return False, "no function defined"
    return True, ""


RUNNER = r'''
import json, math, sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    for lim, val in (("RLIMIT_AS", 512 << 20), ("RLIMIT_FSIZE", 0), ("RLIMIT_NOFILE", 16), ("RLIMIT_NPROC", 0)):
        if hasattr(resource, lim):
            try:
                resource.setrlimit(getattr(resource, lim), (val, val))
            except (ValueError, OSError):
                pass
except ImportError:
    pass
code = sys.stdin.read()
import builtins
SAFE = {k: getattr(builtins, k) for k in ("abs", "round", "min", "max", "sum", "int", "float", "len", "range", "pow",
        "divmod", "sorted", "list", "tuple", "dict", "set", "enumerate", "zip", "any", "all", "str", "bool", "reversed",
        "print", "True", "False", "None", "ZeroDivisionError", "ValueError", "AssertionError")}
SAFE["__import__"] = lambda name, *a, **k: math if name == "math" else (_ for _ in ()).throw(ImportError(name))
env = {"__builtins__": SAFE, "math": math}
out = None
try:
    exec(compile(code, "<lilavati>", "exec"), env)
    fn = env.get("solution") or env.get("simple_math_problem") or next((v for k, v in env.items() if callable(v) and k != "math"), None)
    v = fn() if fn else None
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v)):
        out = float(v)
except BaseException:
    out = None
sys.__stdout__.write("\n" + json.dumps(out))
'''
SANDBOX = '(version 1)\n(allow default)\n(deny network*)\n(deny file-write*)\n(allow file-write* (literal "/dev/null"))\n'


def run(code, timeout=3.0):
    ok, _ = check_program(code)
    if not ok:
        return None
    argv = [sys.executable, "-I", "-S", "-c", RUNNER]
    if sys.platform == "darwin" and os.path.exists("/usr/bin/sandbox-exec"):
        argv = ["/usr/bin/sandbox-exec", "-p", SANDBOX] + argv
    with tempfile.TemporaryDirectory() as d:
        try:
            r = subprocess.run(argv, input=code, capture_output=True, text=True, timeout=timeout, cwd=d,
                               env={"PATH": "/usr/bin:/bin"})
        except subprocess.TimeoutExpired:
            return None
    try:
        return json.loads((r.stdout.strip().splitlines() or ["null"])[-1])
    except (json.JSONDecodeError, IndexError):
        return None

"""Command line: lilavati "A shop sells pens at 12 rupees each. ..." [--tries 8] [--show-program]"""
import argparse


def main():
    ap = argparse.ArgumentParser(prog="lilavati", description="Solve a maths word problem by writing and running Python.")
    ap.add_argument("question")
    ap.add_argument("--tries", type=int, default=8, help="programs to write (1 = one greedy try, no checker)")
    ap.add_argument("--model", default="udgamlabs/Lilavati")
    ap.add_argument("--checker", default="udgamlabs/Lilavati-Checker")
    ap.add_argument("--device", default=None)
    ap.add_argument("--show-program", action="store_true")
    a = ap.parse_args()
    from . import Lilavati
    lv = Lilavati(a.model, a.checker if a.tries > 1 else None, device=a.device)
    r = lv.solve(a.question, tries=a.tries)
    if r["answer"] is None:
        print("No answer: every program failed to run.")
    else:
        extra = f"  ({round(100 * r['agreement'])}% of tries agree" + (f", checker {round(100 * r['confidence'])}%" if r.get("confidence") is not None else "") + ")" if a.tries > 1 else ""
        print(f"{r['answer']}{extra}")
    if a.show_program:
        print("\n" + r["program"])


if __name__ == "__main__":
    main()

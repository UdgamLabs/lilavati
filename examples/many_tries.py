"""Show every try: the value each program returned and the checker's rating, then the voted answer.
python examples/many_tries.py "A batsman scored 45, 62, 18 and 75 runs in four matches. How many runs must he score in the fifth match to average 55?" """
import sys

from lilavati import Lilavati

q = sys.argv[1] if len(sys.argv) > 1 else ("A batsman scored 45, 62, 18 and 75 runs in four matches. "
                                           "How many runs must he score in the fifth match to average 55 runs per match?")
lv = Lilavati()
r = lv.solve(q, tries=8)
for i, (v, s) in enumerate(zip(r["values"], r["scores"]), start=1):
    print(f"try {i}: returned {'failed' if v is None else f'{v:g}':>10}   checker {100 * s:5.1f}%")
print(f"\nvoted answer: {r['answer']}  ({round(100 * r['agreement'])}% agree, checker support {round(100 * r['confidence'])}%)")

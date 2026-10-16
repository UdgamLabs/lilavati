"""Solve one word problem and print the answer with the program behind it.   python examples/quickstart.py"""
from lilavati import Lilavati

lv = Lilavati()
r = lv.solve("A chai stall sells 45 cups of tea in the morning and twice as many in the evening. "
             "Each cup costs 12 rupees. How many rupees does the stall earn in a day?")
print("answer:", r["answer"])                                   # 1620
print(f"{round(100 * r['agreement'])}% of tries agree, checker support {round(100 * r['confidence'])}%")
print(r["program"])

import numpy as np
import json
from utility_v2 import *

def clone_prop_c(source_items):
    clone_items = source_items[:]
    del clone_items[]

columns = get_decision_columns()
as_rules = dict(filter(lambda elem: elem[0].find('R') == 0, columns.items()))
print('result::=='+json.dumps(as_rules))
in_rules_c = map(lambda x: x,as_rules)

mock_rules = {
    'R1' : ['T','T','T','-'],
    'R2' : ['T','T','T','T'],
    'R3' : ['T','T','T','F'],
    'R4' : ['T','T','T','-'],
}
mock_conds = {
    'C1' : ['T','T','T','T'],
    'C2' : ['T','T','T','T'],
    'C3' : ['T','T','T','T'],
    'C4' : ['T','T','T','T'],
}




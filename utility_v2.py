import pandas as pd
import logging
import json
import sys

from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom


reload(sys)
sys.setdefaultencoding('utf-8')
today = date.today()
dailydate = today.strftime("%Y%m%d")
logging.basicConfig(filename='./log./transform_'+dailydate+'.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

df = pd.read_excel('./DTProgram.xlsx', sheet_name='Sheet1')

# C , A , R
# C = Condition
# R = Rule
# A = Action


def get_decision_range(_key):
    ranges = []
    for cell_col in df.columns:
        for cell_row in df.index:
            val = str(df[cell_col][cell_row])
            # case _KEY == C or A
            if _key == 'C' or _key == 'A':
                if _key in val and cell_col == 'ID':
                    ranges.append(val)
        # case _KEY == R
        if _key in cell_col:
            ranges.append(cell_col)
    return ranges


def cast_nanval(cell_value):
    return "" if pd.isna(cell_value) else cell_value


def get_decision_rows():
    row_dict = {}
    for cell_row in df.index:
        row_array = []
        cell_key = df['ID'][cell_row]
        for cell_col in df.columns:
            if cell_col != 'ID':
                cell_value = df[cell_col][cell_row]
                row_array.append(cast_nanval(cell_value))
            #print('cell_key ::=='+cell_key)
        if cell_key != 'ID':
            row_dict[cell_key] = row_array
    #logging.info('rows::=='+json.dumps(row_dict,indent=2, sort_keys=True))
    return row_dict


def get_decision_columns():
    column_dict = {}
    for cell_col in df.columns:
        column_array = []
        for cell_row in df.index:
            cell_value = df[cell_col][cell_row]
            if cell_col != 'ID':
                column_array.append(cast_nanval(cell_value))
        if cell_col != 'ID':
            column_dict[cell_col] = column_array
    #logging.info('columns::=='+json.dumps(column_dict,indent=2, sort_keys=True))
    return column_dict


def create_xmlstr():
    with open('document.json') as json_file:
        _document = json.load(json_file)

        _pnml = Element("pnml")
        _pnml.set("xmlns", "http://www.pnml.org/version-2009/grammar/pnml")
        for _key in _document:
            #print("_key ::=="+json.dumps(_key))
            _tag = _document[_key]
            drawing_element(_pnml, _key, _tag)

    return _pnml


def drawing_element(parent, obj_key, obj_data):
    _sub = SubElement(parent, obj_key)
    if "attributes" in obj_data:
        attributes = obj_data["attributes"]
        for x in attributes:
            _sub.set(x, attributes[x])
    if "text" in obj_data:
        text = obj_data["text"]
        _sub.text = text
    if "childs" in obj_data:
        childs = obj_data["childs"]
        for y in childs:
            _tag = childs[y]
            drawingElement(_sub, y, _tag)
    return _sub

def append_dict(child, tags):
    for tag in tags:
        #print("  tag ::=="+tag)
        _tag = {"attributes": {"id": "p-3BB8-AC2EE-2"}, "childs": {}}
        if "text" == tag:
            _tag["text"] = "xxxxxxx"
        child["childs"][tag] = _tag
        _child = child["childs"][tag]
        append_dict(_child, tags[tag])


def append_2json(parent, prop):
    child = {
        prop: {
            "attributes": {

            },
            "text": "",
        }
    }
    return child

def read_rawdata():
    df_cols = df.columns
    df_rows = df.index

    # "C": ["ID", "Variable/Description", "Operator", "Value", "R1", "R2", "R3", "R4", "R5"]
    store = {
        'R' : {
            'C' : {},
            'A' : {}
        } , 
        'C' : {} , 
        'A' : {}
    }       
    for col_idx in df_cols:
        #print('col::=='+str(col))
        # row [R]        
        if col_idx.find('R') == 0:
            modules = {
                'C' : {},
                'A' : {}
            }
            for c_idx in df_rows:
                row_val = df['ID'][c_idx]
                col_val = df[col_idx][c_idx]
                if row_val.find('C') == 0:
                    modules['C'][row_val] = col_val            
                elif row_val.find('A') == 0:
                    modules['A'][row_val] = col_val 
            store['R']['C'][col_idx] = modules['C']
            store['R']['A'][col_idx] = modules['A']

    
    for row_idx in df_rows:
        row_val = df['ID'][row_idx]            
        modules = {}
        #print('row_val::=='+str(row_val))
        for col_idx in df_cols:
            col_val = df[col_idx][row_idx]
            if col_idx.find('R') == 0:                                
                modules[col_idx] = col_val     
        if row_val.find('C') == 0:
            store['C'][row_val] = modules
        elif row_val.find('A') == 0:
            store['A'][row_val] = modules
        
    #print('store ::=='+json.dumps(store,indent=2, sort_keys=True))
    return store
# -----------------------------------------------------------------------------------

read_rawdata()

# --------------------------------------------------------------------------------------------
# create a new XML file with the results
'''pnml = create_xmlstr()
path_xml = "./tina-result.pnml"
xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(encoding="ISO-8859-1",indent="    ")
with open(path_xml, "w") as f:
    f.write(xmlstr)
    logging.info('write:: '+path_xml)
'''


# ----------------------------------backup code----------------------------------------------------------
'''print("tag0 ::=="+tag0)
            net['childs'][tag0] = {
                "attributes" : {"id" : "p-3BB8-AC2EE-2"},"childs" : {}
            }
            child0 = net['childs'][tag0]             
            for tag1 in tags[tag0]:
                print("tag1 ::=="+tag1)
                child0["childs"][tag1] = {
                    "attributes" : {"id" : "p-3BB8-AC2EE-2"},"childs" : {}
                }
                child1 = child0["childs"][tag1]
                for tag2 in tags[tag0][tag1]:
                    print("tag2 ::=="+tag2)
                    child1["childs"][tag2] = {
                        "attributes" : {"id" : "p-3BB8-AC2EE-2"},"childs" : {}
                    }
                    child2 = child1["childs"][tag2]
                    for tag3 in tags[tag0][tag1][tag2]:
                        print("tag3 ::=="+tag3)
                        child2["childs"][tag3] = {
                            "attributes" : {"id" : "p-3BB8-AC2EE-2"},"childs" : {}
                        }
            '''

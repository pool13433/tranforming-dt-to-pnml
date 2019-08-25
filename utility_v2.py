import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
import logging
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
logging.basicConfig(filename='./log./transform.log', level=logging.DEBUG,
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


def parse_2json():
    columns = get_decision_columns()
    rows = get_decision_rows()

    jason = {
        "net": {
            "attributes": {
                "id": "n-3BB8-AC2DF-0",
                "type": "http://www.laas.fr/tina/tpn"
            },
            "childs": {
                "name": {
                    "childs": {
                        "text": {
                            "text": "buffer1"
                        }
                    }
                },
                "page" : {
                    "attributes": {"id": "p-3BB8-AC2EE-2"}, 
                    "childs":  {
                        "places" : []
                    }
                }
            }
        }
    }

    tags = {
        "name": {
            "text": "",
            "graphics": {
                    "offset": ""
            },
        },
        "label": {
            "text": "",
            "graphics": {
                    "offset": ""
            }
        },
        "graphics": {
            "position": ""
        }
    }

    net = jason['net']
    places = net["childs"]["page"]["childs"]["places"]
    for col in rows:
        #print(" col ::=="+col)
        place = {"childs" : {}}
        for tag0 in tags:
            tags_next = tags[tag0]
            append_dict(place, tags_next)
        #print("place ::=="+json.dumps(place, indent=2, sort_keys=True))                
        places.append(place)
    logging.info('2json::=='+json.dumps(jason, indent=2, sort_keys=True))


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
# -----------------------------------------------------------------------------------


parse_2json()


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

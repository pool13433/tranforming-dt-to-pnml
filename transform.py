import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
import logging
import json
import sys
import collections
from utility_v2 import *

reload(sys)
sys.setdefaultencoding('utf-8')
logging.basicConfig(filename='./log./transform.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

df = pd.read_excel('./DTProgram.xlsx', sheet_name='Sheet1')


def draw_place(page, place_dict):
    name_text = place_dict['name']['text']
    name_offset = place_dict['name']['offset']
    name_id = place_dict['name']['id']    
    graphics_offset = place_dict['graphics']['offset']

    uuid = name_id+str(name_text)  # 'p-3BB8-AC2EE-2'  ,p-3BB8-AC2

    place = SubElement(page, 'place', {'id': uuid})
    # child0
    name = SubElement(place, 'name')
    text = SubElement(name, 'text')
    text.text = name_text
    graphics = SubElement(name, 'graphics')
    offset = SubElement(graphics, 'offset', name_offset)
    # child1
    if 'label' in place_dict:
        label_text = place_dict['label']['text']
        label_offset = place_dict['label']['offset']

        label = SubElement(place, 'label')
        text = SubElement(label, 'text')
        text.text = label_text
        graphics = SubElement(label, 'graphics')
        offset = SubElement(graphics, 'offset', label_offset)
    elif 'initialMarking' in place_dict:
        initialMarking_text = place_dict['initialMarking']['text']

        initialMarking = SubElement(place,'initialMarking')
        text = SubElement(initialMarking,'text')
        text.text = initialMarking_text

    # child2
    graphics = SubElement(place, 'graphics')
    position = SubElement(graphics, 'position', graphics_offset)

def draw_places(page):
    rows = get_decision_rows()
    place_offset = {
           'a' : {'x': '820', 'y': '245'},
           'c' : {'x': '240', 'y': '240'},
           'r' : {'x': '35', 'y': '125'}
    }    
    # Place Group A*,C*
    rows_sorted = collections.OrderedDict(rows.keys())
    for key in sorted(rows.keys()):
        values = rows[key]
        print('rows-key ::=='+key)
        place_text = values[0]
        place_offset = draw_place_ac(page,key,place_offset,place_text)

    # Place Group R*
    columns = get_decision_columns()
    place_index = 1
    for key in sorted(columns.keys()):
        values = columns[key]
        print('col-key::=='+str(key))
        place_offset ,place_index  = draw_place_d(page,key,place_offset,place_index)
        
def draw_place_d(page,key,place_offset,place_index):
    if  key.find('R') == 0:
        name_text = 'D'+str(place_index)
        draw_place(page,{
            'name': {'text': name_text, 'index' : place_index, 'id' : 'p-3BB8-AC31A', 'offset': {'x': '0', 'y': '-10'}},
            'initialMarking': {'text': '1'},
            'graphics': {'offset': place_offset['r']}
        })
        place_offset['r']['x'] = str(int(place_offset['r']['x']))
        place_offset['r']['y'] = str(int(place_offset['r']['y'])+100)
        place_index = place_index+1

    return place_offset , place_index
    

def draw_place_ac(page,key,place_offset,place_text):
    value_dict = {
        'name': {'text': key, 'id' : 'p-3BB8-AC2', 'offset': {'x': '0', 'y': '-10'}},
        'label': {'text': place_text, 'offset': {'x': '10', 'y': '-10'}},
        'graphics': {'offset': {}}
    }
    if 'C' in key:
        value_dict['graphics']['offset'] = place_offset['c']
        place_offset['c']['x'] = str(int(place_offset['c']['x']))
        place_offset['c']['y'] = str(int(place_offset['c']['y'])+90)
    elif 'A' in key:
        value_dict['graphics']['offset'] = place_offset['a']
        place_offset['a']['x'] = str(int(place_offset['a']['x']))
        place_offset['a']['y'] = str(int(place_offset['a']['y'])+90)

    draw_place(page, value_dict)
    return place_offset

def draw_transition(page, transition_dict):
    name_text = transition_dict['name']['text']
    name_unique = transition_dict['name']['unique']
    name_index = transition_dict['name']['index']
    name_offset = transition_dict['name']['offset']
    graphics_offset = transition_dict['graphics']['offset']
    uuid = 't-3BB8-AC30D-'+name_text+name_unique
    # child0
    transition = SubElement(page, 'transition',{'id' : uuid})
    name = SubElement(transition, 'name')
    text = SubElement(name, 'text')
    text.text = 'CT'+str(name_index)
    graphics = SubElement(name, 'graphics')
    SubElement(graphics, 'offset',name_offset)
    # child1
    graphics = SubElement(transition, 'graphics')
    position = SubElement(graphics, 'position',graphics_offset)

def draw_transitions(page):
    columns = get_decision_columns()
    transition_index = 1
    transition_offset = {'x': '460', 'y': '50'}
    for (key,values) in columns.iteritems():
        #print('key ::=='+key)
        #print('values ::=='+str(values))
        if  key.find('R') == 0:
            for index in values:
                #print('index ::=='+str(index))
                if 'X' in index:
                    draw_transition(page,{
                        'name' : {'text' : index,'unique' : key, 'index' : transition_index,'offset' : {'x' : '0','y' : '0'}},
                        'graphics' : {'offset' : transition_offset}
                    })
                    transition_offset['x'] = str(int(transition_offset['x']))
                    transition_offset['y'] = str(int(transition_offset['y'])+90)
                    transition_index = transition_index+1

def draw_decision():
    pnml = Element('pnml')
    pnml.set('xmlns', 'http://www.pnml.org/version-2009/grammar/pnml')

    net = SubElement(pnml, 'net', {
        'id': 'n-3BB8-AC2DF-0',
        'type': 'http://www.laas.fr/tina/tpn'
    })

    name = SubElement(net, 'name')
    SubElement(name, 'text').text = 'buffer1'

    page = SubElement(net, 'page', {'id': 'g-3BB8-AC2EB-1'})

    draw_places(page)
    draw_transitions(page)

    xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
        encoding="ISO-8859-1", indent="    ")
    with open('./tina-result.pnml', "w") as f:
        f.write(xmlstr)


def main():

    # columns = get_decision_columns()
    # rows = get_decision_rows()
    draw_decision()


# ------- execute main -----------
if __name__ == "__main__":
    main()
print("finish export xml")

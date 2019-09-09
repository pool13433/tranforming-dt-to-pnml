import pandas as pd
import logging
import json
import sys
import re 
import collections

from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
from collections import OrderedDict

from utility_v2 import *

reload(sys)
sys.setdefaultencoding('utf-8')
today = date.today()
dailydate = today.strftime("%Y%m%d")
logging.basicConfig(filename='./log/transform_'+dailydate+'.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

df = pd.read_excel('./DTProgram.xlsx', sheet_name='Sheet1')
pnml_options = {
        'y_space' : 90
}
arcs = {'A' : [],'C' : [],'CT' : [],'D' : [],'R' : [],'RT' : [],'DT' : []}
def grep_char(str):
    chars = re.findall('[a-zA-Z]+',str) 
    if len(chars) > 0:
        return chars[0],len(chars)
    return '',0

def push_arcs(arc_key,arc_dict):    
    #print('arc_key ::=='+json.dumps(arc_key))
    #print('arc_dict ::=='+json.dumps(arc_dict))    
    arc_group,arc_len = grep_char(arc_key)
    numbers = re.findall('\d+',arc_key.replace('.','')) 
    sub_numbers = re.findall('\d+',arc_key) 
    #print('numbers ::=='+json.dumps(numbers))        
    if arc_len > 0:        
        arc_index = numbers[0]
        #print('arc_index ::=='+arc_index)
        #print('arc_group ::=='+json.dumps(arc_group,indent=2, sort_keys=True))
        if arc_group in arcs:
            #print('arc_index ::=='+str(arc_index))
            #print('arc_key ::=='+str(arc_key)+'\n')
            if 'index' not in arc_dict:
                arc_dict['index'] = int(arc_index)
            arcs[arc_group].append(arc_dict)                
            

def draw_place(page, place_dict):
    _name = place_dict['name']
    name_text = _name['text']
    name_offset = _name['offset']
    name_id = _name['id']        
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

    #print('uuid ::=='+uuid+' name_text::=='+name_text+'\n')
    arc_data = {'id' : uuid}
    if 'index' in _name:
        arc_data['index'] = _name['index']   
    push_arcs(name_text,arc_data)

def draw_places(page,store):
    rows = get_decision_rows()
    place_offset = {
           'a' : {'x': '820', 'y': '140'},
           'c' : {'x': '240', 'y': '140'},
           'd' : {'x': '35', 'y': '125'},
           'r' :  {'x': '545', 'y': '50'},
    }    

    # Place Group "A*"
    place_index = 1
    for a_idx in store['A']:
        key = a_idx
        values = store['A'][a_idx]
        place_text = a_idx
        place_offset,place_index = draw_place_ac(page,key,place_offset,place_text,place_index)

    # Place Group "C*"
    place_index = 1
    for c_idx in store['C']:
        key = c_idx
        values = store['C'][c_idx]
        place_text = c_idx
        place_offset,place_index = draw_place_ac(page,key,place_offset,place_text,place_index)
        
    # Place Group D* , R*
    place_index = {
        'r' : 1,
        'd' : 1
    }
    store_rc = store['R']['C']
    for r_idx in store_rc:
        r_values = store_rc[r_idx]
        #print('r_values::=='+str(r_values))
        key = r_idx
        #child D
        place_offset ,place_index  = draw_place_d(page,key,place_offset,place_index)
        #print('r_idx::=='+str(r_idx))
        dashs = find_dash(r_values)
        #print('len_dashs::=='+str(dashs))
        if len(dashs) > 0:    
            for x in range(2*len(dashs)):
                place_offset,place_index = draw_place_r(page,key+'.'+str(x+1),place_offset,place_index)                
        else:
            place_offset,place_index = draw_place_r(page,key,place_offset,place_index)            
def find_dash(r_values):
    return map(lambda y: r_values[y],filter(lambda x: r_values[x] == '-',r_values))

def draw_place_d(page,key,place_offset,place_index):
    if  key.find('R') == 0:
        offset_d = place_offset['d'] 
        d_index = place_index['d']
        name_text = 'D'+str(d_index)
        name_id = 'D-'+concat_unique(offset_d)
        draw_place(page,{
            'name': {'text': name_text, 'index' : d_index, 'id' : name_id, 'offset': {'x': '0', 'y': '-10'}},
            'initialMarking': {'text': '1'},
            'graphics': {'offset': offset_d}
        })
        offset_d['x'] = str(int(offset_d['x']))
        offset_d['y'] = str(int(offset_d['y'])+pnml_options['y_space'])   
        
        place_index['d'] = place_index['d']+1

    return place_offset , place_index

def draw_place_r(page,key,place_offset,place_index):
    if  key.find('R') == 0:
        offset_r = place_offset['r'] 
        r_index = place_index['r']
        draw_place(page,{
            'name': {
                        'text': key, 'id' : 'R-'+concat_unique(offset_r),
                        'index' : r_index, 'offset': {'x': '0', 'y': '-10'}
                    },            
            'graphics': {'offset': offset_r}
        })
        offset_r['x'] = str(int(offset_r['x']))
        offset_r['y'] = str(int(offset_r['y'])+pnml_options['y_space'])
        place_index['r'] = place_index['r']+1
    
    return place_offset,place_index

def draw_place_ac(page,key,place_offset,place_text,place_index):
    value_dict = {
        'name': {'text': key, 'id' : 'ac-3BB8-AC2', 'offset': {'x': '0', 'y': '-10'}},
        'label': {'text': place_text, 'offset': {'x': '10', 'y': '-10'}},
        'graphics': {'offset': {}}
    }
    graphics = value_dict['graphics']
    if 'C' in key:
        offset_c = place_offset['c']
        graphics['offset'] = offset_c
        offset_c['x'] = str(int(offset_c['x']))
        offset_c['y'] = str(int(offset_c['y'])+pnml_options['y_space'])
       
    elif 'A' in key:
        offset_a = place_offset['a']
        graphics['offset'] = offset_a
        offset_a['x'] = str(int(offset_a['x']))
        offset_a['y'] = str(int(offset_a['y'])+pnml_options['y_space'])        

    draw_place(page, value_dict)
    return place_offset,place_index

def draw_transition(page, transition_dict):
    if 'name' in transition_dict:
        name_text = transition_dict['name']['text']
        name_id = transition_dict['name']['id']
        name_offset = transition_dict['name']['offset']

        # child0
        transition = SubElement(page, 'transition',{'id' : name_id})
        name = SubElement(transition, 'name')
        text = SubElement(name, 'text')
        text.text = name_text
        graphics = SubElement(name, 'graphics')
        SubElement(graphics, 'offset',name_offset)

        push_arcs(name_text,{
            'id' : name_id
        })

    if 'graphics' in transition_dict:
        graphics_offset = transition_dict['graphics']['offset']    
    
        # child1
        graphics = SubElement(transition, 'graphics')
        position = SubElement(graphics, 'position',graphics_offset)

def draw_transitions(page,store):
    columns = get_decision_columns()
    rows = get_decision_rows()
    tran_index = {'CT' : 1,'DT' : 1,'RT' : 1}
    tran_offset = {
        'CT' : {'x': '460', 'y': '50'},
        'DT' : {'x': '125', 'y': '125'},        
        'RT' : {'x': '635', 'y': '50'},    
    }
    store_rc = store['R']['C']
    for r_idx in store_rc:
        r_values = store_rc[r_idx]
        rc_idx = store_rc.keys().index(r_idx)
        print('rc_idx::=='+str(rc_idx))
        print('r_idx::=='+str(r_idx))
        print('r_values::=='+str(r_values))
        dashs = find_dash(r_values)
        trans_keys = {'CT' : 'CT'+str(rc_idx+1),'RT' : 'RT'+str(rc_idx+1)}
        if len(dashs) > 0:
            couter_float = 1
            for dash_idx in range(2*len(dashs)):
                # child0 [CT]
                ct_key = trans_keys['CT']+'.'+str(couter_float+1)
                #print('ct_key ::=='+ct_key)
                tran_offset,tran_index = draw_transition_ctrt(page,ct_key,tran_offset,tran_index)
                # child0 [RT]
                rt_key = trans_keys['RT']+'.'+str(couter_float+1)
                #print('rt_key ::=='+rt_key)
                tran_offset,tran_index = draw_transition_ctrt(page,rt_key,tran_offset,tran_index)
                couter_float = couter_float+1
        # child [CT]
        tran_offset,tran_index = draw_transition_ctrt(page,trans_keys['CT'],tran_offset,tran_index)
        # child [RT]
        tran_offset,tran_index = draw_transition_ctrt(page,trans_keys['RT'],tran_offset,tran_index)
    
        # child1 [DT]
        #dt_index = transition_index['dt']
        dt_key = 'DT'+str(tran_index['DT'])
        tran_offset,tran_index = draw_transition_ctrt(page,dt_key,tran_offset,tran_index)            

def draw_transition_ctrt(page,key,trans_offset,trans_idx):
    key_char,key_len = grep_char(key)
    #print('key ::=='+str(key))
    #print('key_char ::=='+str(key_char))
    #print('trans_offset ::=='+json.dumps(trans_offset))
    #print('trans_idx ::=='+json.dumps(trans_idx))
    #return
    if key_len > 0:
        idx = trans_idx[key_char]
        #print('trans_idx::=='+str(idx))
        offset = trans_offset[key_char]
        trans_id = key_char+concat_unique(offset)+'-'+str(idx)+str(key_char)
        trans_text = key_char+str(idx)
        draw_transition(page,{
            'name' : {'text' : trans_text,'id' : trans_id, 'offset' : {'x' : '0','y' : '0'}},
            'graphics' : {'offset' : offset}
        })
        offset['x'] = str(int(offset['x']))
        offset['y'] = str(int(offset['y'])+pnml_options['y_space'])
        trans_idx[key_char] = trans_idx[key_char]+1
    return trans_offset,trans_idx

def draw_arc(page,arc):
    if 'target' in arc:
        _arc = SubElement(page,'arc',{
            'id' : arc['id'],
            'source' : arc['source'],
            'target' : arc['target'],
        }) 
        if 'type' in arc:
            SubElement(_arc,'type',{
                'value' : arc['type']
            })

def draw_arcs(page):
    #print('arcs ::=='+json.dumps(arcs,indent=2, sort_keys=True))
    columns = get_decision_columns()
    rows = get_decision_rows()
    data_link = {
            'DT' : 'C' ,'C' : 'CT', 'CT' : 'R'
            ,'R' : 'RT',
            #, 'RT' : 'A'
            }           
    counter_arc = {
        'CT' : -1     
    }

    dict_row_c = sorted(filter(lambda key: key.find('C') ==0  ,rows))                
    #print('dict_c ::=='+json.dumps(dict_row_c)) 
    dict_col_r = sorted(filter(lambda key: key.find('R') ==0 , columns))
    #print('dict_r ::=='+json.dumps(dict_col_r))


    for group in arcs: # for loop "key" [D,DT,R,RT,C,...]
        #print('arc  => group ::=='+group)
        #chars = re.findall('[a-zA-Z]+',group) 
        arc  = arcs[group]
        #print('arc ::=='+json.dumps(arc,indent=2, sort_keys=True))
        #print(' ------------------------------ chars ::=='+json.dumps(group)+'---------------------------------------')
        for (r_index,_arc) in enumerate(arc): #for loop "value" [D,DT,R,RT,C,...]
            #print('index ::=='+json.dumps(index))
            #print('_arc ::=='+json.dumps(_arc,indent=2, sort_keys=True))
            ref_source = _arc['id']
            dict_arc = {'id' : group+'-'+str(ref_source),'source' : ref_source}  
            group_char,group_len = grep_char(group)      
            #print('group_char::=='+str(group_char))               
            if 'DT' == group_char:                             
                #print('\n-------------------------index '+str(r_index)+'------------------------------------')
                for c_idx in range(len(dict_row_c)):
                    c_key = dict_row_c[c_idx]
                    c_dict = rows.get(c_key)
                    #print('c_key::=='+json.dumps(c_key))
                    #print('c_dict::=='+json.dumps(c_dict))
                    #print('r_idx::=='+json.dumps(c_idx))
                    if group in data_link:
                        r_value = columns['R'+str(r_index+1)][c_idx]
                        #print('r_value::=='+str(r_value))
                        if 'T' == r_value:
                            dict_arc['id'] = group+str(r_index)+'-'+str(c_key)+'-'+str(c_idx)
                            ref_target = arcs[data_link[group]][c_idx]
                            dict_arc['target'] = ref_target['id']
                            draw_arc(page,dict_arc)
                        
            elif 'C' == group_char:  
                #print('\nC:==group ::=='+str(group))
                for r_idx in range(len(dict_col_r)):
                    #print('r_idx::=='+str(r_idx))
                    r_key = dict_col_r[r_idx]
                    r_dict = columns.get(r_key)
                    print('r_idx::=='+str(r_idx))
                    #print('r_key::=='+str(r_key))
                    #print('r_dict::=='+str(r_dict))
                    if group in data_link:
                        r_value = r_dict[r_index]
                        r_idx_dash = r_idx
                        #print('r_value::=='+str(r_value)) 
                                             
                        if '-' == r_value: # fine dash then extrace 2 line
                            index_dash = r_value.index('-')                            
                            if index_dash > -1:
                                extrace_dashs = ['T','F']
                                for dash_idx in range(len(extrace_dashs)): 
                                    r_idx_dash = r_idx+int(counter_arc['CT'])  
                                    print('r_idx_dash::=='+str(r_idx_dash))                                      
                                    r_value_dash = extrace_dashs[dash_idx]                                    
                                    dict_arc['id'] = group+str(r_index)+'-'+str(r_idx_dash)+'-'+str(r_idx_dash)
                                    ref_target = arcs[data_link[group]][r_idx_dash]
                                    print('ref_target::=='+json.dumps(ref_target))
                                    dict_arc['target'] = ref_target['id'] 
                                    if 'F' == r_value_dash:                                    
                                        dict_arc['type'] = 'inhibitor'
                                    draw_arc(page,dict_arc)
                                    counter_arc['CT'] = counter_arc['CT']+1
                                    print('counter_arc::=='+json.dumps(counter_arc))                                                          
                        else:
                            dict_arc['id'] = group+str(r_index)+'-'+str(r_idx_dash)+'-'+str(r_idx_dash)
                            ref_target = arcs[data_link[group]][r_idx_dash]
                            dict_arc['target'] = ref_target['id'] 
                            if 'F' == r_value:                                    
                                dict_arc['type'] = 'inhibitor'
                            draw_arc(page,dict_arc)

            elif 'RT' == group_char:  
                print('RT')
            else:
                if group in data_link:
                    ref_target = arcs[data_link[group]][r_index]
                    dict_arc['target'] = ref_target['id']

                draw_arc(page,dict_arc)
def find_value_t(page,rows,r_value,dict_arc,start_idx):
    c_index = 0    
    for row in sorted(rows.keys()):
        if row.find('C') == 0:
            print('row::=='+str(row))
            row_values = rows[row]
            #print('DT::==row_values:=='+json.dumps(row_values))
            c_value = row_values[start_idx['C']]                                
            #print('\ncol key::=='+str(col)+' r_start_idx::=='+str(start_idx['R'])+' r_value::=='+str(r_value))
            #print('row key::=='+str(row)+' c_start_idx::=='+str(start_idx['C'])+' c_value ::=='+str(c_value))
            if 'T' == c_value and r_value == c_value:
                #print('++++ draw arc ++++')      
                ref_target = arcs['C'][c_index]
                print('ref_target ::=='+json.dumps(ref_target))
                dict_arc['target'] = ref_target['id']
                draw_arc(page,dict_arc)

            c_index = c_index+1            
        c_index = 0
    start_idx['C'] = start_idx['C']+1  
    return start_idx



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
    draw_arcs(page)

    xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
        encoding="ISO-8859-1", indent="    ")
    with open('./tina-result.pnml', "w") as f:
        f.write(xmlstr)

def concat_unique(offet):
    return str(offet['x'])+'-'+str(offet['y'])

def filter_index(source_dict,_where):
    idxs = []
    print('source_dict::=='+json.dumps(source_dict.items(),indent=2, sort_keys=False))
    for real_value in OrderedDict(source_dict):
        print('key::=='+str(real_value))         
        #real_value = source_dict.get(key)
        '''real_idx = source_dict.keys().index(key)
        print('real_idx::=='+str(real_idx))
        print('real_value::=='+str(real_value))
        #print('key::=='+str(key))
        if key.find(_where) ==0:
            idxs.append(real_idx)'''
    return idxs

def draw_decision_rawdata():
    store = read_rawdata()

    pnml = Element('pnml')
    pnml.set('xmlns', 'http://www.pnml.org/version-2009/grammar/pnml')

    net = SubElement(pnml, 'net', {
        'id': 'n-3BB8-AC2DF-0',
        'type': 'http://www.laas.fr/tina/tpn'
    })

    name = SubElement(net, 'name')
    SubElement(name, 'text').text = 'buffer1'

    page = SubElement(net, 'page', {'id': 'g-3BB8-AC2EB-1'})

    draw_places(page,store)
    draw_transitions(page,store)
    #draw_arcs(page)

    xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
        encoding="ISO-8859-1", indent="    ")
    with open('./tina-result.pnml', "w") as f:
        f.write(xmlstr)

def main():
    #draw_decision()   
    draw_decision_rawdata()
# ------- execute main -----------
if __name__ == "__main__":
    main()
print("finish export xml")


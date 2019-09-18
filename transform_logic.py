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

class TransformationLogic():

    def __init__(self):
        self.df = pd.read_excel('./DTProgram.xlsx', sheet_name='Sheet1')
        self.pnml_options = {
                'y_space' : 90
        }
        self.arcs = {'A' : [],'C' : [],'CT' : [],'D' : [],'R' : [],'RT' : [],'DT' : []}

    def grep_char(self,str):
        chars = re.findall('[a-zA-Z]+',str) 
        if len(chars) > 0:
            return chars[0],len(chars)
        return '',0

    def push_arcs(self,arc_key,arc_dict):    
        #print('arc_key ::=='+json.dumps(arc_key))
        #print('arc_dict ::=='+json.dumps(arc_dict))    
        arc_group,arc_len = self.grep_char(arc_key)
        numbers = re.findall('\d+',arc_key.replace('.','')) 
        sub_numbers = re.findall('\d+',arc_key) 
        #print('numbers ::=='+json.dumps(numbers))        
        if arc_len > 0:        
            arc_index = numbers[0]
            #print('arc_index ::=='+arc_index)
            #print('arc_group ::=='+json.dumps(arc_group,indent=2, sort_keys=True))
            if arc_group in self.arcs:
                #print('arc_index ::=='+str(arc_index))
                #print('arc_key ::=='+str(arc_key)+'\n')
                if 'index' not in arc_dict:
                    arc_dict['index'] = int(arc_index)
                self.arcs[arc_group].append(arc_dict)                
                

    def draw_place(self,page, place_dict):
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
        if 'unique' in place_dict:
            arc_data['unique'] = place_dict['unique']
        self.push_arcs(name_text,arc_data)

    def draw_places(self,page,store):
        #rows = get_decision_rows()
        place_offset = {
            'a' : {'x': '820', 'y': '140'},
            'c' : {'x': '240', 'y': '140'},
            'd' : {'x': '35', 'y': '125'},
            'r' :  {'x': '545', 'y': '50'},
        }    

        # Place Group "A*"
        place_index = 1
        for a_idx in sorted(store['A']):
            key = a_idx
            values = store['A'][a_idx]
            print('values ::=='+json.dumps(values))
            c_desc = values['Variable/Description']
            place_text = a_idx
            place_offset,place_index = self.draw_place_ac(page,key,place_offset,c_desc,place_index)

        # Place Group "C*"
        place_index = 1
        for c_idx in sorted(store['C']):
            key = c_idx
            values = store['C'][c_idx]
            c_desc = values['Variable/Description']
            place_text = c_idx
            place_offset,place_index = self.draw_place_ac(page,key,place_offset,c_desc,place_index)
            
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
            place_offset ,place_index  = self.draw_place_d(page,key,place_offset,place_index)
            #print('r_idx::=='+str(r_idx))
            dashs = self.find_dash(r_values)
            #print('len_dashs::=='+str(dashs))
            if len(dashs) > 0:    
                for x in range(2*len(dashs)):
                    place_offset,place_index = self.draw_place_r(page,key+'.'+str(x+1),place_offset,place_index)                
            else:
                place_offset,place_index = self.draw_place_r(page,key,place_offset,place_index) 

    def find_dash(self,r_values):
        return map(lambda y: r_values[y],filter(lambda x: r_values[x] == '-',r_values))

    def draw_place_d(self,page,key,place_offset,place_index):
        if  key.find('R') == 0:
            offset_d = place_offset['d'] 
            d_index = place_index['d']
            name_text = 'D'+str(d_index)
            name_id = 'D-'+self.concat_unique(offset_d)
            self.draw_place(page,{
                'name': {'text': name_text, 'index' : d_index, 'id' : name_id, 'offset': {'x': '0', 'y': '-10'}},
                'initialMarking': {'text': '1'},
                'graphics': {'offset': offset_d}
            })
            offset_d['x'] = str(int(offset_d['x']))
            offset_d['y'] = str(int(offset_d['y'])+self.pnml_options['y_space'])   
            
            place_index['d'] = place_index['d']+1

        return place_offset , place_index

    def draw_place_r(self,page,key,place_offset,place_index):
        if  key.find('R') == 0:
            offset_r = place_offset['r'] 
            r_index = place_index['r']
            self.draw_place(page,{
                'name': {
                            'text': key, 'id' : 'R-'+self.concat_unique(offset_r),
                            'index' : r_index, 'offset': {'x': '0', 'y': '-10'}
                        },            
                'graphics': {'offset': offset_r}
            })
            offset_r['x'] = str(int(offset_r['x']))
            offset_r['y'] = str(int(offset_r['y'])+self.pnml_options['y_space'])
            place_index['r'] = place_index['r']+1
        
        return place_offset,place_index

    def draw_place_ac(self,page,key,place_offset,place_text,place_index):
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
            offset_c['y'] = str(int(offset_c['y'])+self.pnml_options['y_space'])
        
        elif 'A' in key:
            offset_a = place_offset['a']
            graphics['offset'] = offset_a
            offset_a['x'] = str(int(offset_a['x']))
            offset_a['y'] = str(int(offset_a['y'])+self.pnml_options['y_space'])        

        value_dict['unique'] = key
        self.draw_place(page, value_dict)
        return place_offset,place_index

    def draw_transition(self,page, transition_dict):
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

            arc_data = {'id' : name_id}
            if 'unique' in transition_dict:
                arc_data['unique'] = transition_dict['unique']
            self.push_arcs(name_text,arc_data)

        if 'graphics' in transition_dict:
            graphics_offset = transition_dict['graphics']['offset']    
        
            # child1
            graphics = SubElement(transition, 'graphics')
            position = SubElement(graphics, 'position',graphics_offset)

    def draw_transitions(self,page,store):
        #columns = get_decision_columns()
        #rows = get_decision_rows()
        tran_index = {'CT' : 1,'DT' : 1,'RT' : 1}
        tran_offset = {
            'CT' : {'x': '460', 'y': '50'},
            'DT' : {'x': '125', 'y': '125'},        
            'RT' : {'x': '635', 'y': '50'},    
        }
        store_rc = store['R']['C']
        #print('store_rc::=='+json.dumps(store_rc))
        for r_key in sorted(store_rc):
            r_values = store_rc[r_key]
            rc_idx = store_rc.keys().index(r_key)
            #print('rc_idx::=='+str(rc_idx))
            #print('r_key::=='+str(r_key))
            #print('r_values::=='+str(r_values))
            dashs = self.find_dash(r_values)
            trans_keys = {'CT' : 'CT'+str(rc_idx+1),'RT' : 'RT'+str(rc_idx+1)}
            ctrt_data = {'unique' : r_key}
            if len(dashs) > 0:
                couter_float = 1
                for dash_idx in range(2*len(dashs)):
                    # child0 [CT]                    
                    ctrt_data['dash_key'] = trans_keys['CT']+'.'+str(couter_float+1)
                    #print('ct_key ::=='+ct_key)
                    tran_offset,tran_index = self.draw_transition_ctrt(page,ctrt_data,tran_offset,tran_index)
                    # child0 [RT]
                    ctrt_data['dash_key'] = trans_keys['RT']+'.'+str(couter_float+1)
                    #print('rt_key ::=='+rt_key)
                    tran_offset,tran_index = self.draw_transition_ctrt(page,ctrt_data,tran_offset,tran_index)
                    couter_float = couter_float+1
            else:
                # child [CT]
                ctrt_data['dash_key'] = trans_keys['CT']
                tran_offset,tran_index = self.draw_transition_ctrt(page,ctrt_data,tran_offset,tran_index)
                # child [RT]
                ctrt_data['dash_key'] = trans_keys['RT']
                tran_offset,tran_index = self.draw_transition_ctrt(page,ctrt_data,tran_offset,tran_index)
        
            # child1 [DT]
            #dt_index = transition_index['dt']
            ctrt_data['dash_key'] = 'DT'+str(tran_index['DT'])            
            tran_offset,tran_index = self.draw_transition_ctrt(page,ctrt_data,tran_offset,tran_index)

    def draw_transition_ctrt(self,page,ctrt_data,trans_offset,trans_idx):
        key = ctrt_data['dash_key']
        key_char,key_len = self.grep_char(key)
        #print('key ::=='+str(key))
        #print('key_char ::=='+str(key_char))
        #print('trans_offset ::=='+json.dumps(trans_offset))
        #print('trans_idx ::=='+json.dumps(trans_idx))
        #return
        if key_len > 0:
            idx = trans_idx[key_char]
            #print('trans_idx::=='+str(idx))
            offset = trans_offset[key_char]
            trans_id = key_char+self.concat_unique(offset)+'-'+str(idx)+str(key_char)
            trans_text = key_char+str(idx)

            # raw arc_data push to arcs collection
            arc_data = {
                'name' : {'text' : trans_text,'id' : trans_id, 'offset' : {'x' : '0','y' : '0'}},
                'graphics' : {'offset' : offset},
                'unique' : key
            }
            if 'unique' in ctrt_data:
                arc_data['unique'] = ctrt_data['unique']                
            self.draw_transition(page,arc_data)

            offset['x'] = str(int(offset['x']))
            offset['y'] = str(int(offset['y'])+self.pnml_options['y_space'])
            trans_idx[key_char] = trans_idx[key_char]+1
        return trans_offset,trans_idx

    def draw_arc(self,page,arc):
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
        
    def draw_arcline(self,page,source_key,target_key):
        for source in self.arcs[source_key]:
            print('source::='+json.dumps(source))
            source_idx = source['index']
            source_id = source['id']
            target_array = self.arcs[target_key]
            target_dict = target_array[source_idx-1]
            target_id = target_dict['id']
            self.draw_arc(page,{
                'id' : source_key+'-'+target_key+source_id+'-'+target_id,
                'source' : source_id,
                'target' :target_id 
            })

    def draw_arclineDT_C(self,page,store):
        # DT => C
        source_key = 'DT'
        target_key = 'C'
        store_rc = store['R']['C']
        c_dicts = self.arcs[target_key]        
        print('\nstore_rc'+json.dumps(store_rc))
        print('\nc_dicts::=='+json.dumps(c_dicts))        
        for source in self.arcs[source_key]:
            #print('source::=='+json.dumps(source))
            dt_idx = source['index']
            dt_id = source['id']
            r_dict = store_rc['R'+str(dt_idx)]
            #print('r_dict::=='+json.dumps(r_dict))
            for c_key in r_dict:
                #c_value = c_dict[c_key]
                c_dict = self.find_unique(c_dicts,c_key)  
                if c_dict is not None:
                    print('c_dict::=='+json.dumps(c_dict))  
                    c_id = c_dict['id']
                    c_idx = c_dict['index']
                    c_unique = c_dict['unique']
                    #print('c_key::=='+json.dumps(c_key))            
                    #print('c_value::=='+json.dumps(c_value)) 
                    if 'T' == r_dict[c_unique]:
                        self.draw_arc(page,{
                            'id' : source_key+'-'+target_key+dt_id+'-'+c_id,
                            'source' : dt_id,
                            'target' :c_id 
                        })

    def draw_arclineRT_A(self,page,store):
        # RT => A
        source_key = 'RT'
        target_key = 'A'
        store_ra = store['R']['A']        
        rt_dicts = self.arcs[source_key]
        a_dicts = self.arcs[target_key]
        #print('\nstore_ra'+json.dumps(store_ra))
        #print('\na_dicts::=='+json.dumps(a_dicts)) 
        print('\nrt_dicts::=='+json.dumps(rt_dicts)) 
        #for r_key in sorted(store_ra):
        for r_dict in rt_dicts:
            r_key = r_dict['unique']
            rt_id = r_dict['id']
            #print('r_key::=='+str(r_key))
            c_values = store_ra[r_key]
            print('c_values::=='+json.dumps(c_values))
            for c_key in c_values:                
                #print('c_key::=='+json.dumps(c_key))
                a_dict = self.find_unique(a_dicts,c_key)
                if a_dict is not None:
                    a_id = a_dict['id']
                    a_key = a_dict['unique']
                    print('a_dict::=='+json.dumps(a_dict))  
                    if 'X' == c_values[a_key]:
                        self.draw_arc(page,{
                            'id' : source_key+'-'+target_key+rt_id+'-'+a_id,
                            'source' : rt_id,
                            'target' :a_id 
                        })


    def find_unique(self,c_dict,c_key):
        #return find(lambda _key: c_dict[_key] == c_key,c_dict)
        #print('c_dict::=='+json.dumps(c_dict))
        #print('c_key::=='+json.dumps(c_key))        
        c_unique = filter(lambda item: item['unique'] == c_key,c_dict)
        #print('c_unique::=='+json.dumps(c_unique))
        if len(c_unique) > 0:
            return c_unique[0]
        else:
            return None

    def draw_arcs(self,page,store):
        store_rc = store['R']['C']
        store_c = store['C']
        
        self.draw_arcline(page,'D','DT')        
        self.draw_arcline(page,'CT','R')        
        self.draw_arcline(page,'R','RT')
        self.draw_arclineDT_C(page,store)
        self.draw_arclineRT_A(page,store)

        
        '''columns = get_decision_columns()
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


        for group in self.arcs: # for loop "key" [D,DT,R,RT,C,...]
            #print('arc  => group ::=='+group)
            #chars = re.findall('[a-zA-Z]+',group) 
            arc  = self.arcs[group]
            #print('arc ::=='+json.dumps(arc,indent=2, sort_keys=True))
            #print(' ------------------------------ chars ::=='+json.dumps(group)+'---------------------------------------')
            for (r_index,_arc) in enumerate(arc): #for loop "value" [D,DT,R,RT,C,...]
                #print('index ::=='+json.dumps(index))
                #print('_arc ::=='+json.dumps(_arc,indent=2, sort_keys=True))
                ref_source = _arc['id']
                dict_arc = {'id' : group+'-'+str(ref_source),'source' : ref_source}  
                group_char,group_len = self.grep_char(group)      
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
                                ref_target = self.arcs[data_link[group]][c_idx]
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
                                        ref_target = self.arcs[data_link[group]][r_idx_dash]
                                        print('ref_target::=='+json.dumps(ref_target))
                                        dict_arc['target'] = ref_target['id'] 
                                        if 'F' == r_value_dash:                                    
                                            dict_arc['type'] = 'inhibitor'
                                        draw_arc(page,dict_arc)
                                        counter_arc['CT'] = counter_arc['CT']+1
                                        print('counter_arc::=='+json.dumps(counter_arc))                                                          
                            else:
                                dict_arc['id'] = group+str(r_index)+'-'+str(r_idx_dash)+'-'+str(r_idx_dash)
                                ref_target = self.arcs[data_link[group]][r_idx_dash]
                                dict_arc['target'] = ref_target['id'] 
                                if 'F' == r_value:                                    
                                    dict_arc['type'] = 'inhibitor'
                                draw_arc(page,dict_arc)

                elif 'RT' == group_char:  
                    print('RT')
                else:
                    if group in data_link:
                        ref_target = self.arcs[data_link[group]][r_index]
                        dict_arc['target'] = ref_target['id']

                    draw_arc(page,dict_arc)
            '''
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
                    ref_target = self.arcs['C'][c_index]
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
        self.draw_transitions(page)
        draw_arcs(page)

        xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
            encoding="ISO-8859-1", indent="    ")
        with open('./tina-result.pnml', "w") as f:
            f.write(xmlstr)

    def concat_unique(self,offet):
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

    def draw_decision_rawdata(self,excellpath,pnmlpath):
        utility = Utility(excellpath)
        store = utility.read_rawdata()

        pnml = Element('pnml')
        pnml.set('xmlns', 'http://www.pnml.org/version-2009/grammar/pnml')

        net = SubElement(pnml, 'net', {
            'id': 'n-3BB8-AC2DF-0',
            'type': 'http://www.laas.fr/tina/tpn'
        })

        name = SubElement(net, 'name')
        SubElement(name, 'text').text = 'buffer1'

        page = SubElement(net, 'page', {'id': 'g-3BB8-AC2EB-1'})

        self.draw_places(page,store)
        self.draw_transitions(page,store)
        self.draw_arcs(page,store)

        xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
            encoding="ISO-8859-1", indent="    ")
        with open(pnmlpath, "w") as f: #'./tina-result.pnml'
            f.write(xmlstr)


logic = TransformationLogic()
logic.draw_decision_rawdata("./DTProgram.xlsx","result_pnmp-arc.pnml")
import pandas as pd
import logging
import json
import sys
import numpy as numpy

from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
from jproperties import Properties
from config_manager import *

reload(sys)
sys.setdefaultencoding('utf-8')

# C , A , R
# C = Condition
# R = Rule
# A = Action

class Utility():

    def __init__(self, filepath):
        print('filepath::==', filepath)
        if filepath is not None:
            #self.has_firstsheet(filepath)
            try:
                self.df = pd.read_excel(filepath, sheet_name=0) # read sheet first tab
            except:
                raise Exception('Program Error')
        else:
            print('File Excell Not Found !!!')

    @classmethod
    def read_properties(cls,prop_name):
        p = Properties()
        with open(prop_name, "r+b") as f:
            p.load(f, "utf-8")            
        return p    

    def filter_rules(self,df_cols,df_rows,req_conf,store):
        _rule = req_conf['RULE']['ALIAS']
        _action = req_conf['ACTION']['ALIAS']
        _condition = req_conf['CONDITION']['ALIAS']
        for col_idx in df_cols:
            #print('col_idx::=='+str(col_idx))
            # row [R]
            if str(col_idx).startswith(_rule):
                modules = {'C': {},'A': {}}
                for c_idx in df_rows:
                    row_val = self.df['ID'][c_idx]
                    col_val = self.df[col_idx][c_idx]
                    if str(row_val).startswith(_condition):
                        modules['C'][row_val] = col_val
                    elif str(row_val).startswith(_action):
                        modules['A'][row_val] = col_val
                store['R']['C'][col_idx] = modules['C']
                store['R']['A'][col_idx] = modules['A']
    
    def filter_condact(self,df_cols,df_rows,req_conf,store):
        _rule = req_conf['RULE']['ALIAS']
        _action = req_conf['ACTION']['ALIAS']
        _condition = req_conf['CONDITION']['ALIAS']
        for row_idx in df_rows:
            row_val = self.df['ID'][row_idx]
            modules = {}
            # print('row_val::=='+str(row_val))
            for col_idx in df_cols:
                col_val = self.df[col_idx][row_idx]
                modules[col_idx] = col_val

            #print('modules::=='+json.dumps(modules))
            if str(row_val).startswith(_condition):
                store['C'][row_val] = modules
            elif str(row_val).startswith(_action):
                store['A'][row_val] = modules
        #print('store[\'C\']::=='+json.dumps(store['C']))

    def filter_extends(self,req_conf,store):

        _rule = req_conf['RULE']['ALIAS']

        store_rc = store['R']['C']
        for rdash_key in store_rc:
            extend_data = {'name' : rdash_key,'extends' : {}}
            #print('\nrdash_key::=='+json.dumps(rdash_key))
            vals = store_rc[rdash_key]
            # print('val::=='+json.dumps(vals))
            len_CRC_EXTEND = len(filter(lambda c_key: vals[c_key] == '-', vals))
            #print('len_CRC_EXTEND::=='+str(len_CRC_EXTEND))
            if len_CRC_EXTEND > 0:
                matrixs_reshap = self.matrix_logic_boolean(len_CRC_EXTEND,is_reshap=True)
                extends_data = {}
                len_dash_power = pow(2,len_CRC_EXTEND)                
                for v_idx in range(len_CRC_EXTEND):
                    rdash_extends_key = rdash_key+'.'+str(v_idx)
                    new_vals = {}
                    das_idx = 0
                    for das_key in vals:
                        das_val = vals[das_key]
                        #print('das_key::=='+str(das_key))
                        #print('das_val::=='+str(das_val))
                        if '-' == das_val:                           
                            new_vals[das_key] =  matrixs_reshap[das_idx][v_idx]
                            das_idx +=1
                        else:
                            new_vals[das_key] = das_val        
                    #print('new_vals::=='+json.dumps(new_vals))               
                    #print('rdash_extends_key::=='+json.dumps(rdash_extends_key))                                   
                    extends_data[rdash_extends_key] = new_vals
                extend_data['extends'] = extends_data
            else:
                extend_data['extends'] = {rdash_key : vals}
            store['CRC_EXTEND'].append(extend_data)
        #print('store[\'CRC_EXTEND\']::==' +json.dumps(store['CRC_EXTEND'], indent=1, sort_keys=True))

        store_c = store['C']        
        #print('store_c::=='+json.dumps(store_c))         
        cr_array = {}               
        matrY_idx = {}
        for c_idx in range(len(store_c)):                        
            c_key = list(sorted(store_c))[c_idx]
            c_values = store_c[c_key]               
            r_dicts = {k: v for k, v in c_values.items() if str(k).startswith(_rule)}
            #print('\nc_key::=='+str(c_key))
            #print('c_idx::=='+str(c_idx))
            #print('r_dicts::=='+json.dumps(r_dicts)) 
            #print('c_values::=='+json.dumps(c_values)) 
            cr_array[c_key] = {}             
            #print('matrY_idx::=='+json.dumps(matrY_idx))
            for r_key in r_dicts:                   
                #print('matrY_idx::=='+json.dumps(matrY_idx))
                c_array = []     
                child = []                                    
                r_value = c_values[r_key]                
                rc_values = store_rc[r_key]
                #print('    r_key ::=='+str(r_key))
                #print('    r_value::=='+json.dumps(r_value))
                #print('    rc_values::=='+json.dumps(rc_values))
                len_RCR_EXTEND = len(filter(lambda c_key: rc_values[c_key] == '-', rc_values))
                #print('    len_RCR_EXTEND::=='+json.dumps(len_RCR_EXTEND))
                matrixs = self.matrix_logic_boolean(len_RCR_EXTEND,is_reshap=False)
                #print('    matrixs::=='+json.dumps(matrixs,indent=1))
                len_dash_power = pow(2,len_RCR_EXTEND) 
                #print('    len_dash_power::=='+str(len_dash_power))
                _idx = self.get_extend_idx(matrY_idx,r_key)
                #print('_idx::=='+str(_idx))
                for dup_idx in range(len_dash_power):                        
                    rdash_extends_key = r_key+'.'+str(dup_idx)  
                    if '-' == r_value:                                                
                        matrY_vals = matrixs[_idx]
                        matrX_val = matrY_vals[dup_idx]                         
                    else:
                        matrX_val = r_value
                    child.append({rdash_extends_key : matrX_val})
                cr_array[c_key][r_key] = child  
                if '-' == r_value:
                    matrY_idx = self.add_extend_idx(matrY_idx,r_key)

        store['RCR_EXTEND'] = cr_array

    def filter_expression(self,df_cols,df_rows,req_conf,store):

        _rule = req_conf['RULE']['ALIAS']
        _action = req_conf['ACTION']['ALIAS']
        _condition = req_conf['CONDITION']['ALIAS']
        _columns = req_conf['COLUMNS_JOIN']['VALUES']

        #---------------------H_GROUP---------------------
        group_h = store['H_GROUP']
        for group_idx in _columns:
            #print('group_idx::=='+str(group_idx))
            sub_group = {_action : {},_condition : {}}
            for col_idx in df_cols:
                #print('col_idx::=='+str(col_idx))
                for row_idx in df_rows:
                    _id = self.df['ID'][row_idx]
                    #print('row_idx::=='+str(row_idx))
                    #print('_id::=='+str(_id))
                    if col_idx.startswith(group_idx):
                        col_val = self.df[group_idx][row_idx]
                        #print('col_val::=='+str(col_val))
                        if str(_id).startswith(_action):
                            sub_group[_action][_id] = col_val
                        elif str(_id).startswith(_condition):
                            sub_group[_condition][_id] = col_val
                        else:
                            print('other _id ::=='+str(_id))
            group_h[group_idx] = sub_group        
        #print('group::=='+json.dumps(group,indent=1))
        #---------------------H_GROUP---------------------

        #---------------------V_GROUP---------------------
        group_v = store['V_GROUP']
        for row_idx in df_rows:
            id_val = self.df['ID'][row_idx]
            #print('id_val::=='+str(id_val))
            sub_group = {}
            for group_idx in _columns:
                print("col_idx::=="+str(col_idx))
                for col_idx in df_cols:
                    if group_idx in self.df:
                        _value = self.df[group_idx][row_idx]
                        if str(id_val).startswith(_action):
                            sub_group[group_idx] = _value
                        elif str(id_val).startswith(_condition):
                            sub_group[group_idx] = _value
                        else:
                            print('not found group !!')
                    else:
                        print('column '+group_idx+' invalid !!')
            group_v[id_val] =  sub_group   
        #print('group_v::=='+json.dumps(group_v,indent=1))
        #---------------------V_GROUP---------------------

        join_v = store['V_JOINS']
        for v_idx in sorted(group_v):
            #print('v_idx::=='+str(v_idx))
            v_dict = group_v[v_idx]
            #print('v_dict::=='+json.dumps(v_dict))            
            join_str = self.reduce_joinstr(_columns=_columns,v_dict=v_dict)        
            print('join_str::=='+join_str)
            join_v[v_idx] = join_str
        
        #print('join_v::=='+json.dumps(join_v))

    def reduce_joinstr(self,_columns,v_dict):
            join_str = '';
            for col_idx in _columns:
                if col_idx in v_dict:
                    col_val = v_dict[col_idx]
                    #print('col_val::=='+str(col_val))
                    #print('col_val isnan::=='+str(pd.isnull(col_val)))
                    if not pd.isnull(col_val): #pd.np.nan is not col_val or
                        join_str +=' '+str(col_val)
            return join_str

    def read_rawdata(self,req_conf):
        #print('hasattr(self,\'df\')::=='+json.dumps(not hasattr(self,'df')))
        if not hasattr(self,'df'):     
            raise Exception('df not found please implement code again.') 

        _rule = req_conf['RULE']['ALIAS']
        _action = req_conf['ACTION']['ALIAS']
        _condition = req_conf['CONDITION']['ALIAS']

        #print('_rule::=='+json.dumps(_rule,indent=1))

        df_cols = self.df.columns
        df_rows = self.df.index
        # "C": ["ID", "Variable/Description", "Operator", "Value", "R1", "R2", "R3", "R4", "R5"]
        store = {
            'R': { 'C': {},'A': {}},
            'C': {},'A': {},
            'CRC_EXTEND': [],'RCR_EXTEND' :{},  

            'H_GROUP':{}, #horizontal
            'V_GROUP':{}, #vertical
            'V_JOINS': {}
        }

        self.filter_rules(df_cols=df_cols,df_rows=df_rows,req_conf=req_conf,store=store)

        self.filter_condact(df_cols=df_cols,df_rows=df_rows,req_conf=req_conf,store=store)

        self.filter_extends(req_conf=req_conf,store=store)

        self.filter_expression(df_cols=df_cols,df_rows=df_rows,req_conf=req_conf,store=store)
                
        #print('store[\'RCR_EXTEND\']::=='+json.dumps(store['RCR_EXTEND'],indent=1))
        #print('matrY_idx::=='+json.dumps(matrY_idx))
        #for f_idx in range(len(c_array)):
        #print('store_c::=='+json.dumps(store_c,indent=1))
        print('store::=='+json.dumps(store,indent=1))
        return store
    # -----------------------------------------------------------------------------------
    def matrix_logic_boolean(self,len_power,is_reshap=True):
        matrix_y = []                
        len_matrix = pow(2,len_power)
        len_middle = len_matrix
        for power_idx in range(len_power):
            matrix_x = []
            matrix_counter = 0
            len_middle = len_middle/2
            bool_val = 'T'                                  
            for matrix_idx in range(len_matrix):                          
                if matrix_counter >= len_middle:                    
                    bool_val = 'F' if bool_val == 'T' else 'T'   
                    matrix_counter = 0                   
                matrix_x.append(bool_val)           
                matrix_counter += 1                     
            matrix_y.append(matrix_x)
        #print('matrix_'+json.dumps(matrix_y,indent=1,sort_keys=True))
        if is_reshap:
            return self.transform_matrix_logic(matrix_y,len_matrix)
        else:
            return matrix_y

    def transform_matrix_logic(self,matrix,len_power):
        matrix_x = []
        for pow_idx in range(len_power):
            matrix_shap = []
            for mat_vals in matrix:
                mat_val = mat_vals[pow_idx]
                #print('mat_val::==',str(mat_val))
                matrix_shap.append(mat_val)
            matrix_x.append(matrix_shap)
        #print('matrix_x::=='+json.dumps(matrix_x,indent=1,sort_keys=True))
        return matrix_x

    def add_extend_idx(self,matrY_idx,r_key):
        if r_key in matrY_idx:
            matrY_idx[r_key] += 1
        else:
            if not matrY_idx:
                matrY_idx = {r_key : 1}
            else:
                matrY_idx[r_key] = 1
        return matrY_idx

    def get_extend_idx(self,matrY_idx,r_key):
        if r_key in matrY_idx:
            return matrY_idx[r_key]
        else:
            return 0
        return matrY_idx

def main():
    _path = 'D:/NickWork/tina-transform/'
    configManager = ConfigManager(root_path=_path);
    config = configManager.read_configs(json_filename='input.json')
    #print('config::=='+json.dumps(config,indent=1))
    utility = Utility(_path+'/inputs/TestData1.xlsx')
    raw_data = utility.read_rawdata(req_conf=config)
    print('confs ::=='+json.dumps(raw_data,indent=1))

    with open('./rawdata.json','w') as output:
        json.dump(raw_data,output)
    
if __name__ == '__main__':
    main()
import pandas as pd
import logging
import json
import sys
import numpy as numpy

from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
from jproperties import Properties


reload(sys)
sys.setdefaultencoding('utf-8')
'''today = date.today()
dailydate = today.strftime("%Y%m%d")
logging.basicConfig(filename='./logs/transform_'+dailydate+'.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')'''
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
    def has_firstsheet(self,filepath):
        pd_sheets = pd.ExcelFile(filepath)
        for sheet in pd_sheets.sheet_names:
            print('sheet::=='+sheet)

    @classmethod
    def read_properties(cls,prop_name):    
        p = Properties()
        with open(prop_name, "r+b") as f:
            p.load(f, "utf-8")            
        return p    

    def read_rawdata(self,require):
        #print('hasattr(self,\'df\')::=='+json.dumps(not hasattr(self,'df')))
        if not hasattr(self,'df'):     
            raise Exception('df not found please implement code again.') 

        _rule = require['RULE']['ALIAS']
        _action = require['ACTION']['ALIAS']
        _condition = require['CONDITION']['ALIAS'] 

        df_cols = self.df.columns
        df_rows = self.df.index
        # "C": ["ID", "Variable/Description", "Operator", "Value", "R1", "R2", "R3", "R4", "R5"]
        store = {
            'R': {
                'C': {},
                'A': {}
            },
            'C': {},
            'A': {},
            'CRC_EXTEND': [],
            'RCR_EXTEND' :{},            
        }
        for col_idx in df_cols:
            #print('col_idx::=='+str(col_idx))
            # row [R]
            if str(col_idx).startswith(_rule):
                modules = {
                    'C': {},
                    'A': {}
                }
                for c_idx in df_rows:
                    row_val = self.df['ID'][c_idx]
                    col_val = self.df[col_idx][c_idx]
                    if str(row_val).startswith(_condition):
                        modules['C'][row_val] = col_val
                    elif str(row_val).startswith(_action):
                        modules['A'][row_val] = col_val
                store['R']['C'][col_idx] = modules['C']
                store['R']['A'][col_idx] = modules['A']

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
            r_dicts = {k: v for k, v in c_values.items() if str(k).startswith('R')}
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
        #print('store[\'RCR_EXTEND\']::=='+json.dumps(store['RCR_EXTEND'],indent=1))
        #print('matrY_idx::=='+json.dumps(matrY_idx))
        #for f_idx in range(len(c_array)):
        #print('store_c::=='+json.dumps(store_c,indent=1))
        #print('cr_array::=='+json.dumps(cr_array,indent=1))
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
    utility = Utility('./inputs/DTProgram.xlsx')
    confs = Utility.read_rawdata()
    print('name::=='+confs.get('name'))
    '''for x in confs:
        print('x::=='+str(x)+' conf::=='+json.dumps(confs[x]))'''
    

    #store = utility.matrix_logic_boolean(3)
    #utility.transform_matrix_logic(store)
    # print('store::=='+json.dumps(store))

if __name__ == '__main__':
    main()
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
# C , A , R
# C = Condition
# R = Rule
# A = Action
class Utility():

    def __init__(self,filepath):     
        print('filepath::==',filepath)  
        if filepath is not None: 
            self.df = pd.read_excel(filepath, sheet_name='Sheet1') #'./DTProgram.xlsx'
        else:
            print('File Excell Not Found !!!')

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

    def append_dict(child, tags):
        for tag in tags:
            #print("  tag ::=="+tag)
            _tag = {"attributes": {"id": "p-3BB8-AC2EE-2"}, "childs": {}}
            if "text" == tag:
                _tag["text"] = "xxxxxxx"
            child["childs"][tag] = _tag
            _child = child["childs"][tag]
            append_dict(_child, tags[tag])



    def read_rawdata(self):
        df_cols = self.df.columns
        df_rows = self.df.index
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
                    row_val = self.df['ID'][c_idx]
                    col_val = self.df[col_idx][c_idx]
                    if row_val.find('C') == 0:
                        modules['C'][row_val] = col_val            
                    elif row_val.find('A') == 0:
                        modules['A'][row_val] = col_val 
                store['R']['C'][col_idx] = modules['C']
                store['R']['A'][col_idx] = modules['A']

        
        for row_idx in df_rows:
            row_val = self.df['ID'][row_idx]            
            modules = {}            
            #print('row_val::=='+str(row_val))
            for col_idx in df_cols:
                col_val = self.df[col_idx][row_idx]
                modules[col_idx] = col_val 
                     
            print('modules::=='+json.dumps(modules))   
            if row_val.find('C') == 0:
                store['C'][row_val] = modules
            elif row_val.find('A') == 0:
                store['A'][row_val] = modules
            
        #print('store ::=='+json.dumps(store,indent=2, sort_keys=True))
        return store
    # -----------------------------------------------------------------------------------

'''utility = Utility('./DTProgram.xlsx')
store = utility.read_rawdata()
print('store::=='+json.dumps(store))'''
from xml.dom import minidom
import re
import xml.etree.ElementTree as ET
import json
import pandas as pd

class TransformWriter():

    def __init__(self):
        print('__init__')
        #self.pnmls = pnmls
        self.document = None

    def build_document(self,store):
        documents = []
        if 'RCR_EXTEND' not in store:
            raise Exception('"RCR_EXTEND" data not found in raw data.')
        if 'RULE' not in store:
            raise Exception('"RULE" data not found in raw data.')

        extends = store['RCR_EXTEND']
        rule_actions = store['RULE']['ACTION']

        doc_data = {}        
        for c_key in extends:
            print('|==>c_key::=='+c_key)
            for r_key in extends[c_key]:
                print('|==|==>r_key::=='+r_key)
                r_value = extends[c_key][r_key]
                rule_name = r_key
                actions = rule_actions[r_key]
                print('|==|==|==>r_value::=='+json.dumps(r_value))
                len_bools = len(r_value) # +'.'+str(bool_idx+1)
                for bool_idx in range(len_bools):
                    bool_dict = r_value[bool_idx]
                    print('|==|==|==|==>bool_idx::=='+json.dumps(bool_idx))
                    print('|==|==|==|==>bool_dict::=='+json.dumps(bool_dict))
                    bool_key = next(iter(bool_dict))
                    bool_val = bool_dict[bool_key]
                    print('|==|==|==|==>bool_key::=='+json.dumps(bool_key))
                    print('|==|==|==|==>bool_val::=='+json.dumps(bool_val))

                    integer,decimal = self.grep_numbers(bool_key)
                    print('|==|==|==|==>integer::=='+str(integer)+' decimal::=='+str(decimal))
                    
                    if len_bools > 1:
                        rule_name = r_key+'.'+str(bool_idx+1)
                    print('|==|==|==|==>rule_name::=='+str(rule_name))
                    bool_data = {c_key : bool_val}
                    if rule_name in doc_data:
                        if c_key in doc_data[rule_name]['0']:
                            doc_data[rule_name]['0'][c_key] = bool_val
                        else:
                            doc_data[rule_name]['0'] = dict(bool_data,
                                    **doc_data[rule_name]['0'])
                    else:
                        doc_data = dict({rule_name : {
                                '0' : bool_data,
                                '1' : '--LTL',
                                '2' : rule_name,
                                '3' : actions
                                }},**doc_data)
                    #doc_data[rule_name]
        print('doc_data::=='+json.dumps(doc_data,sort_keys=True))

        for line_key in sorted(doc_data):
            #print('line_key::=='+line_key)
            num1,num2 = self.grep_numbers(line_key)
            #print('num1::'+str(num1)+' num2::=='+str(num2))
            line_data = doc_data[line_key]
            #print('doc_data::=='+json.dumps(line_data))
            lines = []
            data_T = self.filter_sorted_keys(line_data['0'])
            if len(data_T) > 0:
                condition = "Specify Token in "+",".join(data_T)
            else:
                condition = "Not Specify Token "
            lines.append('--Verify '+line_key+' : '+condition)
            lines.append('--LTL')
            if num2 is not None:
                lines.append('<>{'+line_key+'};')
            else:    
                lines.append('<>'+line_key+';')
            data_X = self.filter_sorted_keys(line_data['3'])
            action = "/\\".join(data_X)
            if len(data_X) > 1:                
                lines.append('<>('+action+');')
            else:
                lines.append('<>'+action+';')

            line = "\n".join(lines)
            documents.append(line)
        
        self.document =  "\n\n".join(documents)
        print('self.document::=='+self.document)

    def filter_sorted_keys(self,data_dict):        
        excludes = filter(lambda x_key: self.includes(data_dict[x_key]),data_dict)
        return sorted(map(lambda x_key: x_key,excludes))

    def includes(self,data_val):
        return (str(data_val).upper() == 'X') or str(data_val).upper() == 'T'

    def write_document(self,text_filepath):
        if self.document is None:
            raise Exception('Please call method build_document before call this method.')        

        with open(text_filepath,'w') as pnml:
            pnml.write(self.document)
    
    def grep_numbers(self,source_str):
        numbers = re.findall(r'\d+', source_str)
        if len(numbers) > 1:
            return numbers[0],numbers[1]
        else:
            return numbers[0],None

    def grep_char(self, str):
		chars = re.findall('[a-zA-Z]+', str)
		if len(chars) > 0:
			return chars[0], len(chars)
		return '', 0

def main():
    '''writer = TransformWriter();
    writer.build_document({'RCR_EXTEND' : {}})
    writer.write_document('./outputs/RCR_EXTEND.txt')'''


if __name__ == "__main__":
    main()

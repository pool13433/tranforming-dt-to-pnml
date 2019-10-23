import json
import codecs
import pandas as pd
import os

from utility_v2 import *
from config_manager import *


class InputValidation():
    def __init__(self,root_path):
        self.validtors = []      
        self.root_path= root_path    
          
    def read_messages(self):        
        return ConfigManager(root_path=self.root_path).read_configs(json_filename='messages.json')

    def get_message(self,message_code):
        messages =  ConfigManager(root_path=self.root_path).read_configs(json_filename='messages.json')
        message = messages[message_code]
        #print('message::=='+json.dumps(message))
        if message != None:
            return message['MESSAGE']['EN']
        else:
            return ''

    def runValidateInput(self,xls_filename):
        configManager = ConfigManager(root_path=self.root_path)
        config = configManager.read_configs(json_filename='input.json');
        messages = configManager.read_configs(json_filename='messages.json');

        _rule = config['RULE']['ALIAS']
        _action = config['ACTION']['ALIAS']
        _condition = config['CONDITION']['ALIAS']

        utility = Utility(xls_filename)
        raw = utility.read_rawdata(require=config)

        # check C
        has_cond = self.checkLeastOneValue(raw=raw,messages=messages,key_name='C')
        # check A
        has_action = self.checkLeastOneValue(raw=raw,messages=messages,key_name='A')        
        # check R
        has_rule = self.checkLeastOneValue(raw=raw,messages=messages,key_name='R')        

        if has_cond and has_action and has_rule:
            vals_condition = config['CONDITION']['VALUES']
            vals_action = config['ACTION']['VALUES']
            self.checkValueContaine(raw=raw,messages=messages,key_name='C',values=vals_condition) #['T', 'F', '-']
            if "" in vals_action:                
                vals_action.append(pd.np.nan)
            self.checkValueContaine(raw=raw,messages=messages,key_name='A',values=vals_action) #['X', pd.np.nan]

            #check least one in rule cols
            self.checkLeastOneInRule(raw=raw,messages=messages,config=config,key_name='R')
        else:
            print('invalid input!!')
                
            
    def checkLeastOneInRule(self,raw,messages,config,key_name):
        _messageLeastOne = messages['LEAST_ONE']
        _messagLeastOneEN = _messageLeastOne['MESSAGE']['EN']
        vals_required = config['ACTION']['VALUES']
        if key_name in raw:
            _validates = []
            if 'A' in raw[key_name]:
                raw_a = raw[key_name]['A']
                len_a = len(raw_a)
                for r_key in raw_a:
                    print('c_idx::=='+str(r_key))
                    r_values = raw_a[r_key]
                    len_rule = len(r_values)
                    len_nan = len(filter(lambda x:(r_values[x] is pd.np.nan) , r_values))
                    print('len_rule::=='+str(len_rule)+' len_nan::=='+str(len_nan))
                    if len_rule == len_nan:
                        self.validtors.append({
                            'code': _messageLeastOne['CODE'],
                            'xls': {
                                'column': r_key,
                                'row': 'C?',
                            },
                            'value': {
                                'actual': '',
                                'expected': json.dumps(vals_required)
                            },
                            'source': r_key,
                            'message' : _messagLeastOneEN                               
                        })
                
    def checkLeastOneValue(self,raw,messages, key_name):        
                
        valid_message = None
        if key_name not in raw:         
            _messageNotPK = messages['NOT_PK'] 
            valid_message = _messageNotPK['MESSAGE']['EN'].replace('{0}',key_name)
            self.validtors.append({
                'code': _messageNotPK['CODE'],
                'field': key_name, 'message': valid_message
            })
            return False;
        else:
            c_len = len(raw[key_name])
            # print('c_len::=='+str(c_len))
            if c_len == 0:           
                _messageNotBlank = messages['NOT_BLANK']         
                _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace('{0}',key_name)                 
                self.validtors.append({
                    'code': _messageNotBlank['CODE'],
                    'field': key_name, 'message': _messageNotBlankEN
                })
                return False
            else:
                return True


    def checkValueContaine(self,raw, messages, key_name, values):              
        _messageNotBlank = messages['NOT_BLANK'] 
        #print('_messageNotBlank::=='+json.dumps(_messageNotBlank))
        _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace('{0}',key_name) 
        _messageOnly = messages['ONLY_VALUES']
        #print('_messageOnly::=='+json.dumps(_messageOnly))
        _messageOnlyEN = _messageOnly['MESSAGE']['EN'].replace('{0}',json.dumps(values)) 
        _validates = []
        if key_name not in raw:
            valid_message = key_name+' not has in raw collections'
            _validates.append({
                'code': _messageOnly['CODE'],
                'source': key_name,
                'message': _messageOnlyEN
            })
        else:
            _values = raw[key_name]
            for _key0 in _values:
                #print('_key::=='+json.dumps(_key0, indent=1,sort_keys=True))
                _vals = _values[_key0]
                #print('_val::=='+json.dumps(_vals))
                for _key1 in _vals:
                    #print('_key1::='+json.dumps(_key1))
                    _val1 = _vals[_key1]
                    #print('_val1::='+json.dumps(_val1))
                    if str(_key1).startswith('R'):
                        is_exist = _val1 in values
                        if not is_exist:
                            _validates.append({
                                'code': _messageNotBlank['CODE'],
                                'xls': {
                                    'column': _key1,
                                    'row': _key0,
                                },
                                'value': {
                                    'actual': _val1,
                                    'expected': str(values)
                                },
                                'source': key_name,
                                #'message': 'Value InValid '+str(values),
                                'message' : _messageOnlyEN                               
                            })

        if len(_validates) == 0:
            return True
        else:
            self.validtors.extend(_validates)
            return False

    def _decode_dict(self, data):
        rv = {}
        encoding = 'UTF-8'  # 'TIS-620'
        for key, value in data.iteritems():
            #the_encoding = chardet.detect(value)['encoding']
            # print('the_encoding::=='+str(the_encoding))
            if isinstance(key, unicode):
                key = key.encode(encoding)
            if isinstance(value, unicode):
                value = value.encode(encoding)
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, dict):
                value = self._decode_dict(value)
            rv[key] = value
        return rv

    def getValidtors(self):
        return self.validtors


def main():
    validate = InputValidation(root_path="D:/NickWork/tina-transform")
    validate.runValidateInput(xls_filename="D:/NickWork/tina-transform/inputs/DTProgram.xlsx")
    validators = validate.getValidtors()
    print('validators ::=='+json.dumps(validators, indent=1))    


if __name__ == "__main__":
    print('validate')
    main()

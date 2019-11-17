import json
import codecs
import pandas as pd
import os

from data_converter import *
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

        utility = DataConverter(xls_filename)
        raw = utility.read_rawdata(req_conf=config)
        meta = utility.read_metadata()

        # first priority check columns required
        is_passed = self.checkColumnsRequired(meta=meta,messages=messages,
                            config=config)
        print('is_passed::=='+json.dumps(is_passed))
        if is_passed:
            # check C
            has_cond = self.checkLeastOneValue(raw=raw,messages=messages,
                                key_name='CONDITION',alias_name=_condition)
            # check A
            has_action = self.checkLeastOneValue(raw=raw,messages=messages,
                                key_name='ACTION',alias_name=_action)        
            # check R
            has_rule = self.checkLeastOneValue(raw=raw,messages=messages,
                                key_name='RULE',alias_name=_rule)        

            if has_cond and has_action and has_rule:
                vals_condition = config['CONDITION']['VALUES']
                vals_action = config['ACTION']['VALUES']
                self.checkValueContains(raw=raw,messages=messages,key_name='CONDITION',
                                        values=vals_condition,rule_alias=_rule) #['T', 'F', '-']
                if "" in vals_action:                
                    vals_action.append(pd.np.nan)
                self.checkValueContains(raw=raw,messages=messages,key_name='ACTION',
                                        values=vals_action,rule_alias=_rule) #['X', pd.np.nan]

                #check least one in rule cols
                self.checkLeastOneInRule(raw=raw,messages=messages,config=config,key_name='RULE')


                #check xor group not have one value
                #self.checkXorGroupNotHaveOneValue(raw=raw,messages=messages,config=config);
            else:
                print('invalid input!!')
    
    def checkColumnsRequired(self,meta,messages,config):
        columns = meta['columns']
        #columns.remove('Operator1')
        print('columns::=='+json.dumps(columns))
        required = config['COLUMNS_REQUIRED']['VALUES']        
        #required.append('required')
        print('required::=='+json.dumps(required))
        is_same = all(elem in columns for elem in required)
        #is_same = all(elem in required for elem in columns)
        print('is_same ::=='+json.dumps(is_same))
        if not is_same:
            _messageRequired = messages['REQUIRE_COLUMNS']
            _messageRequiredEN = _messageRequired['MESSAGE']['EN']
            self.validtors.append({
                'code': _messageRequired['CODE'],
                'field': json.dumps(required), 
                'message': _messageRequiredEN
            }) 
        return is_same
            

    def checkXorGroupNotHaveOneValue(self,raw,messages,config):
        _messageThanOne = messages['XOR_THAN1']
        _messageThanOneEN = _messageThanOne['MESSAGE']['EN']
        xors = raw['XOR_EXTEND']
        for xor_key in xors:
            #print('xor_key::=='+str(xor_key))
            xor_values = xors[xor_key]
            #print('xor_values::=='+str(xor_values))
            if len(xor_values) == 1:
               self.validtors.append({
                    'code': _messageThanOne['CODE'],
                    'field': 'XOR', 'message': _messageThanOneEN
                })         
            
    def checkLeastOneInRule(self,raw,messages,config,key_name):
        _messageLeastOne = messages['LEAST_ONE']
        _messagLeastOneEN = _messageLeastOne['MESSAGE']['EN']
        vals_required = config['ACTION']['VALUES']
        if key_name in raw:
            _validates = []
            if 'ACTION' in raw[key_name]:
                raw_a = raw[key_name]['ACTION']
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
                
    def checkLeastOneValue(self,raw,messages, key_name,alias_name):        
                
        valid_message = None
        if key_name not in raw:         
            _messageNotPK = messages['NOT_PK'] 
            valid_message = _messageNotPK['MESSAGE']['EN'].replace('{0}',alias_name)
            self.validtors.append({
                'code': _messageNotPK['CODE'],
                'field': alias_name, 'message': valid_message
            })
            return False;
        else:
            c_len = len(raw[key_name])
            # print('c_len::=='+str(c_len))
            if c_len == 0:           
                _messageNotBlank = messages['NOT_BLANK']         
                _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace('{0}',alias_name)                 
                self.validtors.append({
                    'code': _messageNotBlank['CODE'],
                    'field': alias_name, 'message': _messageNotBlankEN
                })
                return False
            else:
                return True


    def checkValueContains(self,raw, messages, key_name, values,rule_alias):              
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
                    if str(_key1).startswith(rule_alias):
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
    validate.runValidateInput(xls_filename="D:/NickWork/tina-transform/inputs/TestData1.xlsx")
    validators = validate.getValidtors()
    print('validators ::=='+json.dumps(validators, indent=1))    


if __name__ == "__main__":
    print('validate')
    main()

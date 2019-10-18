import json
import codecs
import pandas as pd

from utility_v2 import *


class InputValidation():
    def __init__(self, soureFilePath):
        self.validtors = []
        self.validSourceFile = soureFilePath
        self.validMessages = self.read_messages()
        print('self.validMessages::=='+json.dumps(self.validMessages))

        #self.runValidateInput()
        

    def read_messages(self):
        with open('./config/messages.json') as json_file:
            data = json.load(json_file)        
            return data
        return None

    def get_message(self,message_code):
        message = self.validMessages[message_code]
        print('message::=='+json.dumps(message))
        if message != None:
            return message['MESSAGE']['EN']
        else:
            return ''

    def runValidateInput(self):
        # check C
        self.checkLeastOneValue('C')
        # check A
        self.checkLeastOneValue('A')
        # check B
        #self.checkLeastOneValue('B')
        # check R
        self.checkLeastOneValue('R')

        self.checkValueContaine('C', ['T', 'F', '-'])
        self.checkValueContaine('A', ['X', pd.np.nan])

    def checkLeastOneValue(self, key_name):
        utility = Utility(self.validSourceFile)
        raw = utility.read_rawdata()  
        messages =  self.validMessages        
        _messageNotBlank = messages['NOT_BLANK'] 
        _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace('{0}',key_name) 
        valid_message = None
        if key_name not in raw:
            _messagePK = messages['NOT_PK']['MESSAGE']            
            valid_message = _messagePK['EN'].replace('{0}',key_name)
        else:
            c_len = len(raw[key_name])
            # print('c_len::=='+str(c_len))
            if c_len == 0:           
                valid_message = _messageNotBlankEN

        if valid_message is None:
            return True
        else:
            _message = messages['NOT_BLANK']
            self.validtors.append({
                'code': _messageNotBlank['CODE'],
                'field': key_name, 'message': _messageNotBlankEN
            })
            return False

    def checkValueContaine(self, key_name, values):
        utility = Utility(self.validSourceFile)
        raw = utility.read_rawdata()
        messages =  self.validMessages        
        _messageNotBlank = messages['NOT_BLANK'] 
        _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace('{0}',key_name) 
        _messageOnly = messages['ONLY_VALUES']
        _messageOnlyEN = _messageOnly['MESSAGE']['EN'].replace('{0}',json.dumps(values)) 
        _validates = []
        if key_name not in raw:
            valid_message = key_name+' not has in raw collections'
            _validates.append({
                'code': _messageOnly['CODE'],
                'source': key_name,
                'message': _messageOnly['MESSAGE']['EN'].replace('{0}',values)
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
            self.validtors += _validates
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
    validate = InputValidation("./DTProgram.xlsx")
    '''validators = validate.getValidtors()
    print('validators ::=='+json.dumps(validators, indent=1))'''
    message = validate.get_message('PROCESS_ERROR')
    print('message::=='+json.dumps(message))


if __name__ == "__main__":
    print('validate')
    main()

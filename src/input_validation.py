import json
import codecs
import pandas as pd
import os

from data_converter import *
from config_manager import *


class InputValidation():
    def __init__(self, root_path):
        self.validtors = []
        self.root_path = root_path

    def read_messages(self):
        return ConfigManager(root_path=self.root_path).read_configs(json_filename='messages.json')

    def get_message(self, message_code):
        messages = ConfigManager(root_path=self.root_path).read_configs(
            json_filename='messages.json')
        message = messages[message_code]
        # print('message::=='+json.dumps(message))
        if message != None:
            return message['MESSAGE']['EN']
        else:
            return ''

    def runValidateInput(self, xls_filename):
        configManager = ConfigManager(root_path=self.root_path)
        config = configManager.read_configs(json_filename='input.json')
        messages = configManager.read_configs(json_filename='messages.json')

        _rule = config['RULE']['ALIAS']
        _action = config['ACTION']['ALIAS']
        _condition = config['CONDITION']['ALIAS']

        utility = DataConverter(xls_filename)
        meta = utility.read_metadata()
        
        # first priority check columns required
        is_passed = self.checkColumnsRequired(meta=meta, messages=messages,
                                              config=config)
        # print('is_passed::=='+json.dumps(is_passed))
        if is_passed:
            raw = utility.read_rawdata(req_conf=config)
            # check C
            has_cond = self.checkLeastOneValue(raw=raw, messages=messages,
                                               key_name='CONDITION', alias_name=_condition)
            # check A
            has_action = self.checkLeastOneValue(raw=raw, messages=messages,
                                                 key_name='ACTION', alias_name=_action)
            # check R
            has_rule = self.checkLeastOneValue(raw=raw, messages=messages,
                                               key_name='RULE', alias_name=_rule)

            if has_cond and has_action and has_rule:
                vals_condition = config['CONDITION']['VALUES']
                vals_action = config['ACTION']['VALUES']

                # check C [T,F,t,f,-]
                self.checkValueContains(raw=raw, messages=messages, key_name='CONDITION',
                                        values=vals_condition, rule_alias=_rule)  # ['T', 'F', '-']
                # check A [X,x,nan]
                self.checkValueContains(raw=raw, messages=messages, key_name='ACTION',
                                        values=vals_action, rule_alias=_rule)  # ['X', pd.np.nan]

                # check least one in rule cols
                self.checkLeastOneInRule(
                    raw=raw, messages=messages, config=config, key_name='RULE')

                # check xor Can only have one value
                self.checkXorCanOnlyHaveOneValue(
                    raw=raw, messages=messages, config=config)

                self.checkConditionConstant(
                    raw=raw, messages=messages, config=config)

                # check xor group not have one value
                # self.checkXorGroupNotHaveOneValue(raw=raw,messages=messages,config=config);
            else:
                print('invalid input!!')
    
    def checkConditionConstant(self, raw, messages, config):
        #print('checkConditionConstant')
        groups = raw['V_GROUP']
        prefix_cond = config["CONDITION"]['ALIAS']
        cols_ltl = config['COLUMNS_LTL']['VALUES']
        #print('cols_ltl ::=='+json.dumps(cols_ltl))

        cond_pk = cols_ltl["VAR1"]
        conditions = {}
        for cond_key in groups:
            #print('cond_key::=='+cond_key)
            # case C (condition)
            cond_vals = groups[cond_key]
            if str(cond_key).startswith(prefix_cond):
                var1 = self.ifnull_than(cond_vals[cond_pk])
                oper1 = self.ifnull_than(cond_vals[cols_ltl["OPER1"]])
                value1 = self.ifnull_than(cond_vals[cols_ltl["VALUE1"]])
                gate = self.ifnull_than(cond_vals[cols_ltl["GATE"]])
                var2 = self.ifnull_than(cond_vals[cols_ltl["VAR2"]])
                oper2 = self.ifnull_than(cond_vals[cols_ltl["OPER2"]])
                value2 = self.ifnull_than(cond_vals[cols_ltl["VALUE2"]])

                #print('var1::=='+str(var1))
                #print('oper1::=='+str(oper1))
                #print('value1::=='+str(value1))
                #print('gate::=='+str(gate))
                #print('var2::=='+str(var2))
                #print('oper2::=='+str(oper2))
                #print('value2::=='+str(value2))

                data_dict = {
                    'LEFT' : {'VAR' : var1,'OPER' : oper1,'VALUE' : value1},
                    'GATE' : gate,
                }
                if "" != var2:
                    data_dict['RIGHT'] = {'VAR' : var2,'OPER' : oper2,'VALUE' : value2} 

                con1_key = var1+oper1+value1
                con2_key = var2+oper2+value2

                if var1 in conditions:
                    if cond_key in conditions[var1]:
                        conditions[var1][cond_key] = data_dict
                    else:
                        conditions[var1] = dict({cond_key : data_dict},**conditions[var1])
                else:
                    conditions = dict({
                        var1 : { cond_key:data_dict}
                    },**conditions)

        _messageValidate = messages['CONDITION_VALIDATE']        
        _messageValidateEN = _messageValidate['MESSAGE']['EN']

        _messageValidateAnd = messages['CONDITION_VALIDATE_AND']
        _messageValidateAndEN = _messageValidateAnd['MESSAGE']['EN']

        _messageAllowIf = messages['OPER_ALLOWED_IF']
        _messageAllowIfEN = _messageAllowIf['MESSAGE']['EN']

        _messageAllowElse = messages['OPER_ALLOWED_ELSE']
        _messageAllowElseEN = _messageAllowElse['MESSAGE']['EN']
        
        
        for dup_key in conditions:
            #print('\n|==dup_key::=='+str(dup_key))
            id_dict = conditions[dup_key]
            #print(' ==|==id_dict::=='+json.dumps(id_dict))
            for cond_key in sorted(id_dict):
                _messageValidateENReplace = _messageValidateEN.replace('{0}', cond_key)                
                cond_dict = id_dict[cond_key]
                #print('==|==|==cond_key::=='+json.dumps(cond_key))
                #print('==|==|==cond_dict::=='+json.dumps(cond_dict))
                cond_left = cond_dict['LEFT']
                cond_gate = cond_dict['GATE']
                #print('\ncond_key::=='+json.dumps(cond_key))
                if 'RIGHT' in cond_dict:     
                    cond_right = cond_dict['RIGHT']  
                    is_numberic = self.is_numberic_handler(source_cond=cond_dict,
                                                            handler="IS_NUMBERIC")                    
                    print('\n|-->condition::=='+json.dumps(cond_dict))
                    print('|--|-->is_numberic::=='+str(is_numberic))
                    if is_numberic:                         
                        if ('AND' == str(cond_gate).upper()):
                            opers_allow = config['OPER_ALLOW']['VALUES']
                            opers_if = opers_allow['IF']
                            opers_else = opers_allow['ELSE']                       
                            #Please specify only '=', '>' or '<' in Operator1.
                            if cond_left['OPER'] not in opers_if:                        
                                self.validtors.append({
                                    'code': _messageAllowIf['CODE'],
                                    'row': self.ignore_ascii(cond_key),
                                    'message': _messageAllowIfEN
                                }) 
                            else:          
                                # Please specify only {0} in Operator2 or Value2 greater than or equal to Value1
                                is_operallowed = self.is_oper_allowed(source_cond=cond_dict,
                                                                        opers=opers_else)                                
                                is_greater_equal = self.is_numberic_handler(source_cond=cond_dict,
                                                                                handler="GREATER_EQUAL")

                                if (is_operallowed is False ) or (is_greater_equal is False): 
                                    _messageOpers = ' or '.join(opers_else[cond_left['OPER']])                       
                                    self.validtors.append({
                                        'code': _messageAllowElse['CODE'],
                                        'row': self.ignore_ascii(cond_key),
                                        'value' : {       
                                            'actual': {
                                                'left' : self.ignore_ascii(cond_left['OPER']),
                                                'right' : self.ignore_ascii(cond_right['OPER']),
                                            },
                                            'expected': {
                                                'right' :  _messageOpers
                                            }
                                        },
                                        'message': _messageAllowElseEN.replace('{0}', _messageOpers)
                                    })  
                    else:
                        # Please specify only {0} in Operator2 or Value2 greater than or equal to Value1
                        is_same,same_key = self.is_same_condition1_and_2(
                                cond_groups=id_dict,
                                source_cond=cond_dict,soure_key=cond_key)  
                        #print('is_same::=='+str(is_same))
                        #print('same_key::=='+str(same_key))
                        if is_same == True and (same_key is not None):
                            _messageValidateAndENReplace = _messageValidateAndEN.replace('{0}', cond_key)
                            self.validtors.append({
                                'code': _messageValidateAnd['CODE'],
                                'row': self.ignore_ascii(cond_key),
                                'message': _messageValidateAndENReplace.replace('{1}', same_key)
                            })     
                else:               
                    is_same,same_key = self.is_same_condition1(
                                cond_groups=id_dict,
                                source_cond=cond_dict,soure_key=cond_key)
                    #print('is_same::=='+str(is_same))
                    if is_same == True:
                        self.validtors.append({
                            'code': _messageValidate['CODE'],
                            'row': self.ignore_ascii(cond_key),
                            'message': _messageValidateENReplace
                        })                        

        #print('conditions::=='+json.dumps(conditions))
                
    def is_same_condition1(self,cond_groups,source_cond,soure_key):        
        
        source_left = source_cond['LEFT']
        source_gate = source_cond['GATE']
        for cond_key in cond_groups:
            #print('cond_key::=='+str(cond_key))
            cond_dict = cond_groups[cond_key]
            #print('cond_dict::=='+json.dumps(cond_dict))
            cond_left = cond_dict['LEFT']
            cond_gate = cond_dict['GATE']
            if 'RIGHT' in cond_dict:
                cond_right = cond_dict['RIGHT']
            same_oper = cond_left['OPER'] == source_left['OPER']
            same_value = cond_left['VALUE'] == source_left['VALUE']
            if soure_key != cond_key and (same_oper and same_value):
                return True , cond_key
                        
        return False , None    

    def is_numberic_handler(self,source_cond,handler):
        #print('source_cond::=='+json.dumps(source_cond))
        source_left = source_cond['LEFT']
        source_gate = source_cond['GATE']
        source_right = source_cond['RIGHT']
        if 'IS_NUMBERIC' == handler:
            if str(source_right['VALUE']).isdigit() and str(source_right['VALUE']).isdigit():
                return True
            else:
                return False
        elif 'GREATER_EQUAL' == handler:
            if source_right['VALUE'] >= source_left['VALUE']:
                return True
            else:
                return False
        else:
            return False            

    def ignore_ascii(self,str):
        if str is None:
            return ""
        else:
            return str.encode('ascii', 'ignore')

    def is_oper_allowed(self,source_cond,opers):        
        source_left = source_cond['LEFT']
        source_gate = source_cond['GATE']
        source_right = source_cond['RIGHT']
        oper = opers[source_left['OPER']]
        #print('oper::=='+str(oper))
        if source_right['OPER'] in oper:
            return True
        else:
            return False

    def is_same_condition1_and_2(self,cond_groups,source_cond,soure_key):        
        opers = ['=','<>']
        source_left = source_cond['LEFT']
        source_gate = source_cond['GATE']
        source_right = source_cond['RIGHT']
        same_oper = source_right['OPER'] == source_left['OPER']
        same_oper_right = source_right['OPER'] in opers
        same_oper_left = source_left['OPER'] in opers

        same_value = source_right['VALUE'] == source_left['VALUE']
        same_var = source_right['VAR'] == source_left['VAR']

        #print('opers ::=='+str((source_right['OPER'] in opers)))
        #print('same_var::=='+str(same_var))
        #print('same_oper::=='+str(same_oper))
        #print('same_value::=='+str(same_value))
        #print('cond_groups::=='+json.dumps(cond_groups))
        #print('len(cond_groups)::=='+str(len(cond_groups)))
        if len(cond_groups) > 1:
            is_same_group,same_group_key = self.is_same_condition1(
                                cond_groups=cond_groups,
                                source_cond=source_cond,soure_key=soure_key)
        else:
            is_same_group,same_group_key = True , soure_key

        #print('same_group_key::=='+str(same_group_key))
        if 'AND' == str(source_gate).upper():      
            is_same_gate = (same_var and (same_oper_right or same_oper_left) and same_value)
            #print('is_same_gate::=='+str(is_same_gate))
            if is_same_gate or is_same_group:                
                return True , same_group_key
            else:
                return False , None
        else:
            return False , None


    def ifnull_than(self,val):                          
        return "" if pd.isnull(val) else val
    def map_config(self,config):
        values = config['VALUES']
        return map(lambda x: values[x],values)

    def checkXorCanOnlyHaveOneValue(self, raw, messages, config):
        _messageThanOne = messages['XOR_UNIQUE']
        _messageThanOneEN = _messageThanOne['MESSAGE']['EN']

        groups = raw['VAR1_GROUP']
        for group_key in groups:
            #print('group_key::=='+str(group_key))
            group_vals = groups[group_key]
            #print('group_vals::=='+json.dumps(group_vals))
            # find first item in dict
            len_group = len(group_vals[group_vals.keys()[0]])
            #print('len_group::=='+str(len_group))
            if len_group > 1:
                counter = {}
                for primary_key in group_vals:
                    if len(group_vals) > 0:
                        bool_vals = map(lambda boo: str(boo).upper(),group_vals[primary_key])
                        count_T = bool_vals.count('T')
                        count_F = bool_vals.count('F')
                        #print('primary_key::=='+primary_key+' count_T ::=='+str(count_T)+'  count_F::=='+str(count_F))
                        # case T > 1
                        if count_T != 1:
                            self.validtors.append({
                                'code': _messageThanOne['CODE'],
                                'xls': {
                                    'rule': primary_key,
                                    'varable': group_key,
                                },
                                'source': group_key,
                                'message': _messageThanOneEN
                            })

    def checkColumnsRequired(self, meta, messages, config):
        columns = meta['columns']
        # columns.remove('Operator1')
        # print('columns::=='+json.dumps(columns))
        required = self.map_config(config['COLUMNS_REQUIRED']) + self.map_config(config['COLUMNS_LTL'])        
        #print('required::=='+json.dumps(required))
        # required.append('required')
        # print('required::=='+json.dumps(required))
        is_same = all(elem in columns for elem in required)
        #is_same = all(elem in required for elem in columns)
        #print('is_same ::=='+json.dumps(is_same))
        if not is_same:
            _messageRequired = messages['REQUIRE_COLUMNS']
            _messageRequiredEN = _messageRequired['MESSAGE']['EN']
            self.validtors.append({
                'code': _messageRequired['CODE'],
                'field': json.dumps(required),
                'message': _messageRequiredEN
            })
        return is_same

    def checkXorGroupNotHaveOneValue(self, raw, messages, config):
        _messageThanOne = messages['XOR_THAN1']
        _messageThanOneEN = _messageThanOne['MESSAGE']['EN']
        xors = raw['XOR_EXTEND']
        for xor_key in xors:
            # print('xor_key::=='+str(xor_key))
            xor_values = xors[xor_key]
            # print('xor_values::=='+str(xor_values))
            if len(xor_values) == 1:
                self.validtors.append({
                    'code': _messageThanOne['CODE'],
                    'field': 'XOR', 'message': _messageThanOneEN
                })

    def checkLeastOneInRule(self, raw, messages, config, key_name):
        _messageLeastOne = messages['LEAST_ONE']
        _messagLeastOneEN = _messageLeastOne['MESSAGE']['EN'].replace(
                '{0}', key_name)
        vals_required = config['ACTION']['VALUES']
        if key_name in raw:
            _validates = []
            if 'ACTION' in raw[key_name]:
                raw_a = raw[key_name]['ACTION']
                len_a = len(raw_a)
                for r_key in raw_a:
                    # print('c_idx::=='+str(r_key))
                    r_values = raw_a[r_key]
                    len_rule = len(r_values)
                    len_nan = len(
                        filter(lambda x: (r_values[x] is pd.np.nan), r_values))
                    #print('len_rule::=='+str(len_rule)+' len_nan::=='+str(len_nan))
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
                            'message': _messagLeastOneEN
                        })

    def checkLeastOneValue(self, raw, messages, key_name, alias_name):

        valid_message = None
        if key_name not in raw:
            _messageNotPK = messages['NOT_PK']
            valid_message = _messageNotPK['MESSAGE']['EN'].replace(
                '{0}', alias_name)
            self.validtors.append({
                'code': _messageNotPK['CODE'],
                'field': alias_name, 'message': valid_message
            })
            return False
        else:
            c_len = len(raw[key_name])
            # print('c_len::=='+str(c_len))
            if c_len == 0:
                _messageNotBlank = messages['NOT_BLANK']
                _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace(
                    '{0}', alias_name)
                self.validtors.append({
                    'code': _messageNotBlank['CODE'],
                    'field': alias_name, 'message': _messageNotBlankEN
                })
                return False
            else:
                return True

    def checkValueContains(self, raw, messages, key_name, values, rule_alias):
        _messageNotBlank = messages['NOT_BLANK']
        # print('_messageNotBlank::=='+json.dumps(_messageNotBlank))
        _messageNotBlankEN = _messageNotBlank['MESSAGE']['EN'].replace(
            '{0}', key_name)
        _messageOnly = messages['ONLY_VALUES']

        val_lowwer = map(lambda x: str(x).lower(), values)
        val_upper = map(lambda x: str(x).upper(), values)

        # concat lower + upper & clean duplicate vals key
        vals_concat = list(dict.fromkeys(val_lowwer+val_upper))
        # print('vals_sorted::=='+str(vals_concat))
        values_only = ", ".join(list(vals_concat))
        _messageOnlyEN = _messageOnly['MESSAGE']['EN'].replace(
            '{0}', values_only).replace('{1}', key_name)

        if 'ACTION' == key_name:
            if "" in values:
                val_lowwer.append(pd.np.nan)
                val_upper.append(pd.np.nan)

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
                # print('_val::=='+json.dumps(_vals))
                for _key1 in _vals:
                    # print('_key1::='+json.dumps(_key1))
                    _val1 = _vals[_key1]
                    # print('_val1::='+json.dumps(_val1))
                    if str(_key1).startswith(rule_alias):
                        #print('val_lowwer ::=='+json.dumps(val_lowwer))
                        #print('val_upper ::=='+json.dumps(val_upper))
                        is_exist = (_val1 in val_lowwer) or (
                            _val1 in val_upper)
                        if not is_exist:
                            _validates.append({
                                'code': _messageNotBlank['CODE'],
                                'xls': {
                                    'column': _key1,
                                    'row': _key0,
                                },
                                'value': {
                                    'actual': _val1,
                                    'expected': values_only
                                },
                                'source': key_name,
                                # 'message': 'Value InValid '+str(values),
                                'message': _messageOnlyEN
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
    validate.runValidateInput(
        xls_filename="D:/NickWork/tina-transform/inputs/TestData1 (1).xlsx")
    validators = validate.getValidtors()
    print('validators ::=='+json.dumps(validators, indent=1))


if __name__ == "__main__":
    print('validate')
    main()

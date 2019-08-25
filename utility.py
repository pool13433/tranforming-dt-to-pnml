import pandas as pd
import logging
import json

def parse_value(x):
    print('x ::=='+x)
    try:
        if pd.isnull(x):
            return '-'
        return str(x).join((agent_contact, agent_telno)).encode('utf-8').strip()
    except NameError:
        print('exception::=='+NameError)
    
def get_row_dict(df):
    rows = {}
    for ind_row in df.index:
        datas = {}
        row_key = '';
        for col_name in df.columns:
            data = df[col_name][ind_row]
            #print(data)
            if col_name == 'Stub':
                row_key = data
            else:
                datas[col_name] = ('' if pd.isnull(data) else data)
        rows[row_key] = datas
    logging.info('getRowList::=='+json.dumps(rows))
    return rows

def get_column_dict(df):
    columns = {}
    col_keyname = 'Variable/Description'
    for col_name in df.columns:
        datas = {}
        print('col_name ::=='+json.dumps(col_name))
        for ind_row in df.index:
            '''key_stub = df['Stub'][ind_row]
            if col_name != 'Stub':
                data = df[col_name][ind_row]
                datas[key_stub] = ('' if pd.isnull(data) else data)'''
            key_desc = df[col_keyname][ind_row]
            print('key_desc ::=='+json.dumps(key_desc))
            if col_name != col_keyname:
                data = df[col_name][ind_row]
                datas[key_desc] = ('' if pd.isnull(data) else data)
        if col_name != col_keyname:
            columns[col_name] = datas
    logging.info('getColumnList::=='+json.dumps(columns))
    return columns

def get_read_file(df):
    rows = get_row_dict(df)
    for x in rows:
        # print('row=>x::=='+x)
        for x_d in sorted(rows[x]):
            # print('row=>x_d::==' + str(x_d)+' rows[x]::=='+str(rows[x][x_d]))
            print('')

    columns = get_column_dict(df)
    for y in sorted(columns):
        #print('column=>y::==' + y)
        for y_d in sorted(columns[y]):
            #print('column=>y_d::==' + str(y_d) + ' columns[y]::==' + str(columns[y][y_d]))
            print('')

    return {
        'rows' : rows,
        'columns' : columns
    }
def sorted_dict(columnDict):
    column_list = []
    for x in sorted(columnDict):
        column_list.append(x)
    return column_list
def fine_drive2immediate(row_dict):
    resultDict = {}
    for rule in row_dict:
        index_C = rule.find('C')
        if index_C > -1:
            #print('rule::=='+rule+' row_dict ::=='+json.dumps(row_dict[rule]))
            resultDict[rule] = row_dict[rule]
    return resultDict

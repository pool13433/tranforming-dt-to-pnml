import json

class ConfigManager():

    def __init__(self,root_path):          
        self.root_path = root_path
    
    def read_configs(self,json_filename):
        with open(self.root_path+'/config/'+json_filename) as json_file:
            data = json.load(json_file)        
            return data
        return None
    def set_config(self,c_filename,c_key,c_value):
        data = self.read_configs()
        data[c_key] = c_value
        self.write_config(data)

    def replace_config(self,c_filename,c_dict):
        self.write_config(c_dict)

    def write_config(self,c_filename,c_data):
        jsonFile = open(self.config_name, "w+")
        jsonFile.write(json.dumps(c_data,indent=1))
        jsonFile.close()

def main():
    config = ConfigManager(root_path='D:/NickWork/tina-transform')
    result = config.read_configs(json_filename='messages.json')
    print('result::=='+json.dumps(result,indent=1))

    #config.set_config('ACTION','AA')

if __name__ == "__main__":
    main()

    #D:\NickWork\tina-transform\config\messages.json

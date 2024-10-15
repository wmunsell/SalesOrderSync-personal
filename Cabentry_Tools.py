import xmltodict, os, json

class Cabentry_Tools():
    def __init__(self):
        self.config = json.load(open('config.json'))
        self.xml_dir = self.config['xml_export_files']

    # check if new xml file exists within folder
    def check_for_new_xml(self):
        # get list of xml files
        xml_files = [f for f in os.listdir(self.xml_dir) if f.endswith('.xml')]
        # check if xml file exists
        if len(xml_files) > 0:
            # return first xml file
            return xml_files
        # return false if no xml file exists
        return False
    
    # format xml file to json to load into zoho
    def format_xml_to_json(self, xml_file):
        with open(xml_file, encoding='utf-8') as fd:
            # parse xml file
            doc = xmltodict.parse(fd.read())
            # remove w3 references from the json object
            doc['Order']['@xmlns:xsi'] = None
            doc['Order']['@xmlns:xsd'] = None
            doc['Order']['@xmlns'] = None
            # remove empty values from the json object
            for key in list(doc['Order'].keys()):
                if doc['Order'][key] == None:
                    del doc['Order'][key]
            # return json
            return doc['Order']

    # export json to file
    def export_json_to_file(self, json_data, file_name):
        # create file
        with open(file_name, 'w') as outfile:
            # write json to file
            json.dump(json_data, outfile, indent=4)
        # return file name
        return
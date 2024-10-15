import json
from datetime import datetime
from Zoho_Tools import Zoho_Tools
from difflib import SequenceMatcher

class Format_Sales_Order():
    def __init__(self, json_dict, customer_id, log):
        self.customer_id = customer_id
        self.json_dict = json_dict
        self.zt = Zoho_Tools(log)

    def get_base(self):
        base = self.json_dict
        key_list = ['RoomProfiles', 'CabinetProfiles', '@xmlns:xsi', '@xmlns:xsd', 'GUID']
        for key in key_list:
            if key in base:
                base.pop(key)
        # remove empty values from the json object
        for key in list(base.keys()):
            if base[key] == None:
                del base[key]
        return base
    
    def clean_keys(self, base):
        # remove all input keys from the json object
        key_list = ['SubmittedDate']
        for key in key_list:
            if key in base:
                base.pop(key)
        return base

    def get_room_info(self):
        # get the room info from the json object
        base = self.json_dict
        if base['RoomProfiles'] and base['RoomProfiles']['RoomProfile']:
            roomprofiles = base['RoomProfiles']['RoomProfile']
            return roomprofiles
        return None
    
    def get_sku_dict(self):
        with open('SKU_Dictionary.json') as f:
            data = json.load(f)
            return data
        
    def get_wood_species(self, cabinetprofiles):
        wood_species = []
        for cabinetprofile in cabinetprofiles:
            if cabinetprofile['TheRoom'] and cabinetprofile['TheRoom']['Wood']:
                wood_species.append(cabinetprofile['TheRoom']['Wood'])
        species_list = list(set(wood_species))
        if species_list and len(species_list) == 1:
            return species_list[0].split("(")[0].strip()
        elif species_list and len(species_list) > 1:
            return species_list[0].split("(")[0].strip()
        else:
            return None

    def get_wood_species_code(self, Wood_Species, sku_dict):
        Wood_Species_keys = list(sku_dict['Wood Species'].values())
        Wood_Species_matches = [Wood_Species_key for Wood_Species_key in Wood_Species_keys if Wood_Species_key in Wood_Species]
        if not Wood_Species_matches or len(Wood_Species_matches)<1:
            return None
        if Wood_Species_matches and len(Wood_Species_matches)<2:
            match_codes = list(sku_dict['Wood Species'].keys())[list(sku_dict['Wood Species'].values()).index(Wood_Species_matches[0])]
            Wood_Species = ''.join(match_codes)
        else:
            match_codes = list(set([list(sku_dict['Wood Species'].keys())[list(sku_dict['Wood Species'].values()).index(x)] for x in Wood_Species_matches]))
            Wood_Species = ''.join(match_codes)
        return Wood_Species

    def common_substring(self, strings):
        if not strings:
            return ""
        # Use the first string as a reference
        reference = strings[0]
        def get_common_substring(a, b):
            matcher = SequenceMatcher(None, a, b)
            match = matcher.find_longest_match(0, len(a), 0, len(b))
            return a[match.a: match.a + match.size]
        # Find common substring iteratively
        common_substr = reference
        for s in strings[1:]:
            common_substr = get_common_substring(common_substr, s)
        return common_substr

    def get_accessory_code(self, cabinetprofile):
        accessories = cabinetprofile['Accessories']['Accessory']
        if type(accessories) == list:
            accessory_skus = [x['SKU'] for x in accessories]
        else:
            accessory_skus = [accessories['SKU']]
        matches = []
        for accessory_sku in accessory_skus:
            if accessory_sku.startswith('ROT'):
                matches.append("ROT")
            elif accessory_sku.startswith('PPROT'):
                matches.append(accessory_sku)
        matches = list(set(matches))
        if matches:
            if len(matches)<2:
                return matches[0]
            else:
                return "-".join(matches)
        return None

    def get_exposed_side_code(self, cabinetprofile, sku_dict):
        exposed_side_count = 0
        LFE = cabinetprofile['LFE']
        RFE = cabinetprofile['RFE']
        codes = []
        if LFE != '( None )':
            LFE_Code = LFE.split("(")[1].replace(')', '').strip()
            codes.append(LFE_Code)
        if RFE != '( None )':
            RFE_Code = RFE.split("(")[1].replace(')', '').strip()
            codes.append(RFE_Code)
        exposed_side_count = int(len(codes))
        if exposed_side_count < 1:
            return None # no finished edges specified
        keys = []
        for code in codes:
            values = [index for index, value in sku_dict['Exposure'].items() if code in value]
            if not values:
                return "00" # no sales order codes were found within the sku dict
            keys.append([key for key in values if exposed_side_count == int(key[0])][0])
        keys = list(set(keys))  
        if len(keys) > 1:
            return None # two differed finished edges were found
        else:
            return keys[0]
    
    def get_construction_code(self, the_room, sku_dict):
        construction = the_room['Construction']
        construction_keys = list(sku_dict['Construction'].values())
        construction_matches = [construction_key for construction_key in construction_keys if construction_key in construction]
        if not construction_matches or len(construction_matches)<1:
            return None
        if construction_matches and len(construction_matches)<2:
            match_codes = list(sku_dict['Construction'].keys())[list(sku_dict['Construction'].values()).index(construction_matches[0])]
            construction_code = ''.join(match_codes)
        else:
            match_codes = list(set([list(sku_dict['Construction'].keys())[list(sku_dict['Construction'].values()).index(x)] for x in construction_matches]))
            construction_code = ''.join(match_codes)
        return construction_code
    
    def get_molding_code(self, the_cabinet, sku_dict):
        SKU = the_cabinet['SKU'] 
        if SKU in sku_dict['Molding_Types']:
            return '6000-'+SKU
        return None
    
    def get_custom_modification_skus(self, cabinetprofile):
        # check for custom modifications
        if cabinetprofile['CustomModifications']:
            if type(cabinetprofile['CustomModifications']['CustomModification']) == list:
                custom_mods = cabinetprofile['CustomModifications']['CustomModification']
                return [x['SKU'] for x in custom_mods]
            else:
                return [cabinetprofile['CustomModifications']['CustomModification']['SKU']]
                
    def get_interior_code(self, cabinetprofile, sku_dict):
        interior = cabinetprofile['TheRoom']['Interior']
        custom_mod_skus = self.get_custom_modification_skus(cabinetprofile)
        # check for custom modifications
        if custom_mod_skus:
            delux_interior = sku_dict['Interior']['DI']
            matches = list(set(custom_mod_skus) & set(list(delux_interior)))
            if matches:
                return 'DI'
        # if no custom modifications, check for standard interior
        else:
            interior = interior.split("(")[1].split(")")[0].strip()
            interior_match = [interior_key for interior_key, interior_values in sku_dict['Interior'].items() if interior in interior_values]
            if not interior_match or len(interior_match)<1:
                return None
            return interior_match[0]
        
    def get_item_id(self, sku):
        inventory = self.zt.get_inventory_item(sku)
        if inventory and inventory['items']:
            for item in inventory['items']:
                if item['sku'] == sku:
                    return item['item_id']
        else:
            return None
        
    def get_item_name(self, sku):
        inventory = self.zt.get_inventory_item(sku)
        if inventory and inventory['items']:
            for item in inventory['items']:
                if item['sku'] == sku:
                    return item['name']
        else:
            return None
        
    def get_toe_kick_code(self, sku_dict, Custom_Modification_Skus):
        if Custom_Modification_Skus:
            for SKU in Custom_Modification_Skus:
                if SKU in sku_dict['Toe Kick']:
                    return SKU
            return None
        else:
            return None

    def generate_sku(self, cabinetprofile):
        the_room = cabinetprofile['TheRoom']
        the_cabinet = cabinetprofile['TheCabinet']
        sku_dict = self.get_sku_dict()
        Construction =  self.get_construction_code(the_room, sku_dict)        
        SKU = the_cabinet['SKU']
        Accessories = None
        if cabinetprofile['Accessories'] and cabinetprofile['Accessories']['Accessory']:
            Accessories = self.get_accessory_code(cabinetprofile)
        Custom_Modification_Skus = self.get_custom_modification_skus(cabinetprofile)
        Toe_Kick = self.get_toe_kick_code(sku_dict, Custom_Modification_Skus)
        molding = self.get_molding_code(the_cabinet, sku_dict)
        Wood_Species = self.get_wood_species_code(the_room['Wood'], sku_dict)
        Exposure = self.get_exposed_side_code(cabinetprofile, sku_dict) 
        Interior = self.get_interior_code(cabinetprofile, sku_dict)
        if molding:
            molding_sku = [molding, Wood_Species]
            molding_sku = '-'.join([x for x in molding_sku if x is not None])
            return molding_sku
        full_sku = [Construction, SKU, Toe_Kick, molding, Wood_Species, Exposure, Interior, Accessories]
        full_sku = '-'.join([x for x in full_sku if x is not None])
        return full_sku.replace("-00", "")

    def format_header_section(self, cabinetprofiles):
        wood_species = self.get_wood_species(cabinetprofiles)
        finish = ""
        construction = ""
        base_door_style = ""
        purchase_order = ""
        header = {
            "customer_id": self.customer_id, 
            "salesorder_number": None, # self.zt.get_next_salesorder_number(),
            "reference_number": self.json_dict['JobName'],
            "sales_order_date": (datetime.strptime(self.json_dict['CreatedByDate'], "%Y-%m-%dT%H:%M:%S.%f")).strftime('%d %m %Y'), 
            "expected_shipment_date": None,
            "shipment_date": datetime.strptime(self.json_dict['AccountNumber'], "%m/%d/%Y").strftime("%Y-%m-%d"),
            "exchange_rate":1,
            "Payment_Terms": "Net 15",
            "delivery_method": None, 
            "wood_species": wood_species, 
            "finish": None, 
            "purchase_order": None,
            "custom_fields":[
                {
                    "value": wood_species,
                    "customfield_id":"3519566000000619051"
                },
                {
                    "value":finish,
                    "customfield_id":"3519566000000628085"
                },
                {
                    "value":construction,
                    "customfield_id":"3519566000000629095"
                },
                {
                    "value":base_door_style,
                    "customfield_id":"3519566000000817329"
                },
                {
                    "value":purchase_order,
                    "customfield_id":"3519566000000955305"
                }
            ]
        }
        return header 
    
    def refine_line_item(self, cabinetprofile):
        # get the line items from the json object  
        sku = self.generate_sku(cabinetprofile)
        discount = (float(self.json_dict['DealerDiscount'].replace('.0', '')))
        quantity = int(cabinetprofile["Quantity"])
        price = float(cabinetprofile["TotalPrice"].replace('$', '').replace(',', ''))
        if sku.startswith('6000'):
            liner_feet = quantity * 8
            price_per_liner_foot = price / 8
            adjusted_price = price_per_liner_foot * ((100 - discount)/100)
            total_price = adjusted_price * liner_feet
            quantity = liner_feet
        else:
            adjusted_price = price * ((100 - discount)/100)
            total_price = adjusted_price * quantity
        
        refined_line_item = {
            "description": sku,
            "item_id": self.get_item_id(sku),
            "name": self.get_item_name(sku),
            "quantity": quantity,
            "rate": round(adjusted_price, 4),
            "item_total": round(total_price, 2),
            "tax_id": 3519566000000113321,
            "tags":[
                {
                "tag_id":"3519566000000000333",
                "tag_option_id":"3519566000005113007"
                },
                {
                "tag_id":"3519566000000000337",
                "tag_option_id":"3519566000000955323"
                }
            ],
            "item_custom_fields":[
            ],
            "project_id": None,
            "header_name": None,
            "header_id": None,
            "unit":"ea"
            }
        return refined_line_item
    
    def pull_cabinets(self):
        # get the line items from the json object
        line_items = []
        cabinets = self.json_dict['CabinetProfiles']['CabinetProfile']
        for cabinet in cabinets:
            line_item = {}
            if cabinet['TheRoom'] and cabinet['TheRoom']['RoomName']:
                line_item['RoomName'] = cabinet['TheRoom']['RoomName']
            if cabinet['TheCabinet']:
                thecabinet = cabinet['TheCabinet']
                line_item.update(thecabinet)
            if cabinet['Accessories'] and cabinet['Accessories']['Accessory']:
                accessories = {"Accessories": cabinet['Accessories']['Accessory']}
                line_item.update(accessories)
            if cabinet['CustomModifications']:
                if type(cabinet['CustomModifications']['CustomModification']) == list:
                    custom_mods = {"CustomModifications": cabinet['CustomModifications']['CustomModification']}
                else:
                    custom_mods = {"CustomModifications": [cabinet['CustomModifications']['CustomModification']]}
                line_item.update(custom_mods)
            line_items.append(line_item)
        return line_items

    ### putting it all together ###
    def gen_sales_order_list(self):
        line_items = []
        cabinetprofiles = [cabinet_profile for cabinet_profile in self.json_dict['CabinetProfiles']['CabinetProfile'] if cabinet_profile['TheRoom']['RoomName'] != 'BLK']
        header = self.format_header_section(cabinetprofiles)
        for cabinetprofile in cabinetprofiles:
                try:
                    line_items = line_items + [self.refine_line_item(cabinetprofile)]
                except:
                    raise
        full_sales_order = {}
        full_sales_order.update(header)
        full_sales_order['line_items'] = line_items
        return full_sales_order



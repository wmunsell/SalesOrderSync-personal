import json
from datetime import datetime, timedelta
from Zoho_Tools import Zoho_Tools
from difflib import SequenceMatcher
from collections import Counter

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
        with open('SKU_Dictionary_New.json') as f:
            data = json.load(f)
            return data
        
    def get_wood_species(self, cabinetprofiles, sku_dict):
        wood_species_list = []
        for cabinetprofile in cabinetprofiles:
            if cabinetprofile['TheRoom'] and cabinetprofile['TheRoom']['Wood']:
                wood_species_list.append(cabinetprofile['TheRoom']['Wood'])
        if wood_species_list: # this will have to be updated to handle multiple wood species if found
            distinct_species_list = list(set(wood_species_list))
            Wood_Species_code = distinct_species_list[0].split("(")[1].split(")")[0].strip()
            Wood_Species_desc = [Wood_Species_value for Wood_Species_key, Wood_Species_value in sku_dict['Wood_Desc'].items() if Wood_Species_key == Wood_Species_code][0]
            return Wood_Species_desc
        else:
            return None

    def get_wood_species_code(self, Wood_Species, sku_dict):
        Wood_Species = Wood_Species.split("(")[1].split(")")[0].strip()
        Wood_Species_code = [Wood_Species_value for Wood_Species_key, Wood_Species_value in sku_dict['Wood'].items() if Wood_Species_key == Wood_Species][0]
        return Wood_Species_code

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
        return accessory_skus
    
    def get_accessories(self, cabinetprofile):
        accessories = cabinetprofile['Accessories']['Accessory']
        if type(accessories) == dict:
            return [accessories]
        else:
            return accessories

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
        
    def get_cabinet_end_code(self, cabinetprofile):
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
            return '00' # no finished edges specified
        return ''.join(codes)
    
    def get_construction_code(self, the_room, sku_dict):
        construction = the_room['Construction'].split("(")[1].split(")")[0].strip()
        construction_code = [construction_value for constrcution_key, construction_value in sku_dict['Construction'].items() if construction == constrcution_key]
        if not construction_code or len(construction_code)<1:
            return None
        return construction_code[0]
    
    def get_molding_code(self, the_cabinet, sku_dict):
        SKU = the_cabinet['SKU']
        Type = the_cabinet['Type'] 
        if Type == 'C-ML':
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
        else:
            return None
                
    def get_interior_code(self, cabinetprofile, sku_dict):
        interior = cabinetprofile['TheRoom']['Interior']
        interior = interior.split("(")[1].split(")")[0].strip()
        interior_match = [interior_value for interior_key, interior_value in sku_dict['Interior'].items() if interior_key == interior]
        if not interior_match or len(interior_match)<1:
            return None
        return interior_match[0]
        
    def sum_custom_mods(self, data):
        organized_dict = {}
        for key, values in data.items():
            if values is not None:
                for value_list in values:
                    if value_list is not None:
                        for value in value_list:
                            if value not in organized_dict:
                                organized_dict[value] = set()
                            organized_dict[value].add(key)
        
        # Convert sets to lists for the final output
        for key in organized_dict:
            organized_dict[key] = list(organized_dict[key])
        return organized_dict

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

    def get_type(self, cabinetprofile, sku_dict):
        type = cabinetprofile['Type']
        print("'"+type+"'")
        # check if the type is a key in the sku_dict
        if type in sku_dict['Type']:
            print('True')
            return True
        return False
    
    def format_dates(self, sales_order_date, expected_shipment_date):
        # check if the date is in the correct format ie 4/4/2024 not 04/04/24


        # Parse the sales order and expected shipment dates
        sales_order_date = datetime.strptime(sales_order_date, "%Y-%m-%dT%H:%M:%S.%f")
        expected_shipment_date = datetime.strptime(expected_shipment_date, "%m/%d/%Y")
        today = datetime.now()

        # Ensure expected shipment date is after both the sales order date and today
        if expected_shipment_date <= sales_order_date or expected_shipment_date <= today:
            expected_shipment_date = max(sales_order_date, today) + timedelta(days=1)

        # Format the dates back to the desired formats
        formatted_sales_order_date = sales_order_date.strftime('%d %m %Y')
        formatted_expected_shipment_date = expected_shipment_date.strftime("%Y-%m-%d")

        return formatted_sales_order_date, formatted_expected_shipment_date

    def generate_sku(self, cabinetprofile, sku_dict):
        the_room = cabinetprofile['TheRoom']
        the_cabinet = cabinetprofile['TheCabinet']
        Type = self.get_type(the_cabinet, sku_dict)

        Construction =  self.get_construction_code(the_room, sku_dict)    
        SKU = the_cabinet['SKU']

        Accessories = None
        if cabinetprofile['Accessories'] and cabinetprofile['Accessories']['Accessory']:
            Accessories = self.get_accessories(cabinetprofile)

        Custom_Modification_Skus = self.get_custom_modification_skus(cabinetprofile)
        molding = self.get_molding_code(the_cabinet, sku_dict)
        Wood_Species = self.get_wood_species_code(the_room['Wood'], sku_dict)
        Cabinet_end = self.get_cabinet_end_code(cabinetprofile) 
        Interior = self.get_interior_code(cabinetprofile, sku_dict)

        if molding:
            molding_sku = [molding, Wood_Species]
            molding_sku = '-'.join([x for x in molding_sku if x is not None])
            print(molding_sku)
            return molding_sku, Accessories, Custom_Modification_Skus
        
        if Type:
            # new SKU format 
            # [Construction - SKU - Wood_Species]
            full_sku = [Construction, SKU, Wood_Species]
            full_sku = '-'.join([x for x in full_sku if x is not None])
            print(full_sku)
            return full_sku, Accessories, Custom_Modification_Skus

        # original SKU format
        # [Construction, SKU, Toe_Kick, molding, Wood_Species, Exposure, Interior, Accessories]
        # new SKU format 
        # [Construction - SKU - Wood_Species - Cabinet_End - Interior]
        
        full_sku = [Construction, SKU, Wood_Species, Cabinet_end, Interior]
        full_sku = '-'.join([x for x in full_sku if x is not None])
        print(full_sku)
        return full_sku, Accessories, Custom_Modification_Skus

    def format_header_section(self, cabinetprofiles, sku_dict):
        wood_species = self.get_wood_species(cabinetprofiles, sku_dict)
        finish = ""
        construction = ""
        base_door_style = ""
        purchase_order = ""
        sales_order_date, expected_shipment_date = self.format_dates(self.json_dict['CreatedByDate'], self.json_dict['AccountNumber'])
        header = {
            "customer_id": self.customer_id, 
            "salesorder_number": None, # self.zt.get_next_salesorder_number(),
            "reference_number": self.json_dict['JobName'],
            "sales_order_date": sales_order_date,
            "expected_shipment_date": expected_shipment_date,
            "shipment_date": None,
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

    def get_accessory_price(self, accessories):
        accessory_price = 0.0
        for accessory in accessories:
            price = float(accessory["Upcharge"].replace('$', '').replace(',', ''))
            accessory_price += price
        return accessory_price
    
    def gen_accessory_line_items(self, accessories):
        accessory_line_items = []
        discount = float(self.json_dict['DealerDiscount'])

        for accessory in accessories:
            price = float(accessory["Upcharge"].replace('$', '').replace(',', ''))
            adjusted_price = price * ((100 - discount)/100)

            accessory_line_item = {}
            accessory_line_item['description'] = accessory["SKU"]
            accessory_line_item['item_id'] = self.get_item_id(accessory["SKU"])
            accessory_line_item['name'] = self.get_item_name(accessory["SKU"])
            
            accessory_line_item['quantity'] = accessory["Quantity"]
            accessory_line_item['rate'] = adjusted_price
            accessory_line_item['item_total'] = float(accessory["TotalUpcharge"].replace('$', '').replace(',', ''))
            accessory_line_item['tax_id'] = 3519566000000113321
            accessory_line_item['tags'] = [
                {
                "tag_id":"3519566000000000333",
                "tag_option_id":"3519566000005113007"
                },
                {
                "tag_id":"3519566000000000337",
                "tag_option_id":"3519566000000955323"
                }
            ]
            accessory_line_item['item_custom_fields'] = []
            accessory_line_item['project_id'] = None
            accessory_line_item['header_name'] = None
            accessory_line_item['header_id'] = None
            accessory_line_item['unit'] = 'ea'
            accessory_line_items.append(accessory_line_item)
        return accessory_line_items
    
    def refine_line_item(self, cabinetprofile, sku_dict):
        # get the line items from the json object  
        sku, accessories, custom_mods = self.generate_sku(cabinetprofile, sku_dict)
        # discount = (float(self.json_dict['DealerDiscount'].replace('.0', ''))) # this is the original discount algorithm
        discount = float(self.json_dict['DealerDiscount'])
        quantity = int(cabinetprofile["Quantity"])

        accessories_price = 0.0
        if accessories:
            accessories_price = self.get_accessory_price(accessories)

        price = float(cabinetprofile["TotalPrice"].replace('$', '').replace(',', '')) - accessories_price

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
        return refined_line_item, sku, custom_mods, accessories
    
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
        sku_dict = self.get_sku_dict()
        custom_mod_summary = {}
        line_items = []
        cabinetprofiles = [cabinet_profile for cabinet_profile in self.json_dict['CabinetProfiles']['CabinetProfile'] if cabinet_profile['TheRoom']['RoomName'] != 'BLK']
        header = self.format_header_section(cabinetprofiles, sku_dict)
        for cabinetprofile in cabinetprofiles:
                try:
                    line_item, sku, custom_mods, accessories = self.refine_line_item(cabinetprofile, sku_dict)
                    if sku in custom_mod_summary:
                        custom_mod_summary[sku].append(custom_mods)
                    else:
                        custom_mod_summary[sku] = [custom_mods]
                    line_items = line_items + [line_item]

                    if accessories:
                        accessory_line_items = self.gen_accessory_line_items(accessories)
                        line_items = line_items + accessory_line_items
                except:
                    raise
        full_sales_order = {}
        full_sales_order.update(header)
        full_sales_order['line_items'] = line_items
        accessory_summary = self.sum_custom_mods(custom_mod_summary)

        return full_sales_order, accessory_summary
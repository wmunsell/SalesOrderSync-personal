import json, http.client
from datetime import datetime

class Zoho_Tools():
    def __init__(self, log=None):
        self.config = json.load(open('config.json'))
        self.token = self.config['books_access_token']
        self.conn = http.client.HTTPSConnection("www.zohoapis.com")
        self.xml_dir = self.config['xml_export_files']
        self.organization_id = self.config['organization_id']
        self.client_id = self.config['client_id']
        self.client_secret = self.config['client_secret']
        self.log = log
    
    def list_sales_orders(self):
        # pull all sales orders from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/salesorders?organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('list_sales_orders ' + str(res.status))
        return json.loads(data.decode("utf-8"))['salesorders']
    
    def get_sales_order(self, sales_order_id):
        # pull a specific sales order from zoho
        headers = { 
            'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/salesorders/{sales_order_id}?organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('get_sales_order ' + str(res.status))
        return json.loads(data.decode("utf-8"))['salesorder']
    
    def get_sales_order_id(self, sales_order_number):
        # pull a specific sales order from zoho
        headers = { 
            'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/salesorders?organization_id={self.organization_id}&salesorder_number={sales_order_number}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('get_sales_order ' + str(res.status))
        return json.loads(data.decode("utf-8"))['salesorders'][0]['salesorder_id']   

    def create_sales_orders(self, payload, Test=False, Number=None):
        headers = { 
            'Authorization': f"Zoho-oauthtoken {self.token}",
            'Content-Type': 'application/json'
        }

        if Test:
            # create a test sales order in zoho
            payload['salesorder_number'] = Number
            self.conn.request("POST", f"/books/v3/salesorders?organization_id={self.organization_id}&ignore_auto_number_generation=true", json.dumps(payload), headers)
        else:
            # create a sales order in zoho
            self.conn.request("POST", f"/books/v3/salesorders?organization_id={self.organization_id}", json.dumps(payload), headers) # &ignore_auto_number_generation=true
        
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('create_sales_orders ' + str(res.status))
        return json.loads(data.decode("utf-8"))
    
    def list_contacts(self):
        # pull all contacts from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/contacts?organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('list_contacts ' + str(res.status))
        return json.loads(data.decode("utf-8"))['contacts']
    
    def check_for_contact_old(self, contact_name):
        # check if a contact exists in zoho
        contacts = self.list_contacts()
        for contact in contacts:
            if contact['contact_name'] == contact_name and contact['contact_type'] == 'customer':
                return int(contact['contact_id'])
        return False
    
    def check_for_contact(self, dealer_number):
        # pull all contacts from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/contacts?organization_id={self.organization_id}&cf_customer_number={dealer_number}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        contacts = json.loads(data.decode("utf-8"))['contacts']
        if contacts:
            if len(contacts)==1:
                return contacts[0]['contact_id']
            else:
                message = f"Multiple contacts were found with a cf_customer_number of {dealer_number}"
                self.log.error(message)
                return None
        else:
            message = f"No contacts were found with a cf_customer_number of {dealer_number}"
            self.log.error(message)
            return None
    
    # ////// this needs to be tested and updated (currently not in scope) ///////
    def create_contact(self, xml_json):
        # create a contact in zoho
        payload = {
            "contact_name" : xml_json['SoldTo']['Contact'],
            "customer_name" : xml_json['SoldTo']['Name'],
            "contact_type": "customer",
            "currency_id" : "3519566000000000097",
            "currency_code" : "USD",
            "custom_fields": [
                {
                    "SoldTo": xml_json['SoldTo'], 
                    "ShipTo": xml_json['ShipTo']
                }               
            ]
        }
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("POST", f"/books/v3/contacts?organization_id={self.organization_id}", payload, headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('create_contact ' + str(res.status))
        return json.loads(data.decode("utf-8"))
        
    def update_sales_orders(self, sales_order_id, sales_order):
        # update a sales order in zoho
        headers = { 
            'Authorization': f"Zoho-oauthtoken {self.token}",
            'content-type': "application/json" 
        }
        self.conn.request("PUT", f"/books/v3/salesorders/{sales_order_id}?organization_id={self.organization_id}", json.dumps(sales_order), headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('update_sales_orders ' + str(res.status))
        return json.loads(data.decode("utf-8"))
    
    def get_next_salesorder_number(self):
        # get list of all sales orders
        sales_orders = self.list_sales_orders()
        # get list of all sales order numbers
        salesorder_numbers = [x['salesorder_number'] for x in sales_orders]
        # get current year
        current_year = str(datetime.now().year)[-2:]
        # get current month
        current_month = str(datetime.now().month)
        # add a 0 in front of current month if less than 10
        if len(current_month) == 1:
            current_month = "0"+current_month
        # get list of all XX values for numbers that contain the current year and month
        refined_numbers = [int(x[:8].strip()[-2:]) for x in salesorder_numbers if x.startswith(current_year+"-"+current_month)]
        # get the highest number in the list
        highest_number = max(refined_numbers)
        next_number = str(highest_number+1)
        # add a 0 to the front of the number if less than 10
        if len(next_number) == 1:
            next_number = "0"+next_number
        next_salesorder_number = current_year+"-"+current_month+next_number
        return next_salesorder_number
    
    def ack_number_exists(self, ack_number):
        # get list of all sales orders
        sales_orders = self.list_sales_orders()
        salesorder_numbers = [x['salesorder_number'] for x in sales_orders]
        if ack_number in salesorder_numbers:
            return True
        return False
    
    def list_items(self):
        # pull all items from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/items?organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('list_items ' + str(res.status))
        return json.loads(data.decode("utf-8"))['items']
    
    def list_salesorder_templates(self):
        # pull all sales order templates from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/salesorders/templates?organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('list_salesorder_templates ' + str(res.status))
        return json.loads(data.decode("utf-8"))

    def get_inventory_item(self, sku):
        # pull all items from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/items?search_text={sku}&organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        self.log.info('get_inventory_item ' + str(res.status))
        return json.loads(data.decode("utf-8"))

    def get_accessory_names(self, skus):
        accessory_names = []
        # pull accessory names from zoho
        for sku in skus:
            headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
            self.conn.request("GET", f"/books/v3/items?sku={sku}&organization_id={self.organization_id}", headers=headers)
            res = self.conn.getresponse()
            data = res.read()
            data = json.loads(data.decode("utf-8"))
            if data and len(data['items']) > 0:
                for item in data['items']:
                    if item['category_name'] == 'Accessories':
                        accessory_names.append(item['name'])
            else:
                accessory_names.append(sku)
        self.log.info('get_accessory_name ' + str(res.status))
        return accessory_names

    def get_modificaiton_notes(self, sku):
        # pull accessory names from zoho
        headers = { 'Authorization': f"Zoho-oauthtoken {self.token}" }
        self.conn.request("GET", f"/books/v3/items?sku={sku}&organization_id={self.organization_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        print(json.dumps(data, indent=4))
        # if data and len(data['items']) > 0:
        #     for item in data['items']:
        #         if item['category_name'] == 'Accessories':
        #             accessory_names.append(item['name'])
        # else:
        #     accessory_names.append(sku)
        # self.log.info('get_accessory_name ' + str(res.status))
        # return accessory_names

#zt = Zoho_Tools()
#num = '123003'
#print(zt.check_for_contact(num))
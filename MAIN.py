import os

# import python support files
from Format_Sales_Order_NEW import Format_Sales_Order
from Authenticate import Authenticate
from Zoho_Tools import Zoho_Tools
from Cabentry_Tools import Cabentry_Tools
from Workflow_Tools import Workflow_Tools
import json, sys, logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


###################################################
###### TESTING VARIABLES ######

# Change Testing to False
# Change SalesOrderNumber to None

Testing = True
SalesOrderNumber = '99-9999'

###################################################

def error_handler(xml_file_path, error_directory, json_file_path=None):
    xml_file_name = os.path.basename(xml_file_path)
    os.rename(xml_file_path, f'{error_directory}/{xml_file_name}')  
    if json_file_path:
        os.remove(json_file_path)   
    return

def main():
    today = datetime.now()
    # renew token if expired
    auth = Authenticate()
    auth.check_date()
    # get config file
    config = json.load(open('config.json'))
    xml_dir = config['xml_export_files']
    xml_processed_dir = config['xml_processed_files']
    xml_error_files = config['xml_error_files']
    json_dir = config['json_export_files']
    json_processed_dir = config['json_processed_files']
    logfile = config['testing_log_file']     
    handler = RotatingFileHandler(
        logfile, 
        maxBytes=100*1024*1024, 
        backupCount=50,
        encoding='utf-8'
    )
    log = logging.getLogger()
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.info("--------------------------------------------------------------------------------------------------")
    log.info(today)
    # create instance of Zoho_Sync
    cabentry = Cabentry_Tools() 
    # create instance of Workflow_Tools
    workflow = Workflow_Tools()
    # create instance of Zoho_Tools
    zoho_tools = Zoho_Tools(log)
    # check for new xml file
    xml_files = cabentry.check_for_new_xml()
    # check if xml file exists
    if xml_files:
        for xml_file in xml_files:
            log.info(f"Processing {xml_file}")
            xml_file_name = xml_file.split('.')[0]
            # set the full path to the xml file
            xml_file_path = f"{xml_dir}/{xml_file}"
            # get json from xml file
            try:
                xml_json = cabentry.format_xml_to_json(xml_file_path)
                log.info("XML converted to JSON")
            except Exception as e:
                message = f"There was an error converting to json"
                log.error(e)
                error_handler(xml_file_path, xml_error_files)

            try: 
                cabentry.export_json_to_file(xml_json, f"{json_dir}/{xml_file_name}.json")
                log.info("Exported JSON to file")
            except Exception as e:
                message = f"There was an error exporting to json"
                log.error(e)
                error_handler(xml_file_path, xml_error_files)  

            json_file_path = f"{json_dir}/{xml_file_name}.json"

            # check for AcknowledgementNumber
            try:
                ack_number = workflow.get_ack_number(xml_json)
            except Exception as e:
                message = f"There was an error getting the ack number"
                log.error(e)    

            dealernumber = xml_json['DealerNumber']
            # check for contact
            try: 
                customer_id = zoho_tools.check_for_contact(dealernumber)
            except Exception as e:
                message = f"There was an error getting the customer id"
                log.error(e)      

            # if contact does not exist
            if not customer_id:
                # send email to notify that contact does not exist
                message = f'Unable to pull contact_id for contact with a cf_customer_number of {dealernumber}'
                workflow.email_failed_sales_order(xml_file, 999, message)  

            # create instance of sales order
            try:
                log.info("Formatting Sales Order")
                formatted_sales_order = Format_Sales_Order(xml_json, customer_id, log)
            except Exception as e:
                message = f"There was an error formatting the sales order"
                log.error(e)   

            # create list of sales orders
            log.info("Generating Sales Order list")
            sales_order, accessory_summary = formatted_sales_order.gen_sales_order_list()

            if accessory_summary:
                workflow.email_accessory_dict(sales_order, accessory_summary)

            with open("testing.json", 'w') as f:
                json.dump(sales_order, f, indent=4)

            # if ack_number and zoho_tools.ack_number_exists(ack_number):
            #     try:
            #         salesorder_id = zoho_tools.get_sales_order_id(ack_number)
            #         res = zoho_tools.update_sales_orders(salesorder_id, sales_order)
            #     except Exception as e:
            #         message = f"There was an error updating the salesorder"
            #         log.error(e)
            #         workflow.email_failed_sales_order(xml_file, 999, message, e)
            #         error_handler(xml_file_path, xml_error_files, json_file_path) 
            #  
            # else:
            #     try:
            #         res = zoho_tools.create_sales_orders(sales_order, Test=Testing, Number=SalesOrderNumber)
            #     except Exception as e:
            #         message = f"There was an error creating the sales order"
            #         log.error(e)
            #         workflow.email_failed_sales_order(xml_file, 999, message, e)
            #         error_handler(xml_file_path, xml_error_files, json_file_path) 
            
            # # if sales order failed to create
            # if res['code'] == 200 or res['code'] == 0:
            #     # move the processed files to the processed folder
            #     os.rename(xml_file_path, f'{xml_processed_dir}/{xml_file_name}.xml')   
            #     os.rename(json_file_path, f'{json_processed_dir}/{xml_file_name}.json') 
            #     log.info("Moved XML and JSON files to processed") 
            # else:
            #     code = res['code']
            #     message = res['message']
            #     # email failed sales order
            #     workflow.email_failed_sales_order(xml_file, code, message)
            #     log.error(message)
            #     error_handler(xml_file_path, xml_error_files, json_file_path) 


        log.info('All xml files processed')
    else:
        log.info('No new xml files found')


if __name__ == "__main__":   
    main()







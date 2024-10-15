from smtplib import SMTP
from email.mime.text import MIMEText
import json

class Workflow_Tools():
    def __init__(self):
        pass
    
    # email notification of failed sales order
    def email_failed_sales_order(self, file_name, code, message, error=None):
        # connect to server
        smtp_server = 'mail.indtelnet.com'
        Euser = 'coppes-dev@itnstart.com'
        Epass = """&d8d%L%L3M"""
        # configure email
        Efrom = 'no-reply@coppes.us'
        #Eto = ['wesley@coppes.us', 'davidm@coppes.us', 'will.munsell@outlook.com']
        Eto = 'will.munsell@outlook.com'
        message = """\
            File Name: """ + str(file_name) + """
            Code: """ + str(code) + """
            Message: """ + str(message) + """
            Error: """ + str(error)
        text_subtype = 'plain'
        msg = MIMEText(message, text_subtype)
        msg['Subject']= 'Failed Sales Order'
        msg['From']   = Efrom 
        # send email
        conn = SMTP(smtp_server)
        conn.set_debuglevel(False)
        conn.login(Euser, Epass)
        try:
            conn.sendmail(Efrom, Eto, msg.as_string())
        finally:
            conn.quit()

    def email_accessory_dict(self, salesorder, summary):
        # pull info from salesorder
        salesorder_number = salesorder['salesorder_number']
        salesorder_name = salesorder['reference_number']
        subject = 'Accessory Summary for ' + str(salesorder_name) + ' - ' + str(salesorder_number)
        # connect to server
        smtp_server = 'mail.indtelnet.com'
        Euser = 'coppes-dev@itnstart.com'
        Epass = """&d8d%L%L3M"""
        # configure email
        Efrom = 'no-reply@coppes.us'
        #Eto = ['wesley@coppes.us', 'davidm@coppes.us', 'will.munsell@outlook.com']
        Eto = 'will.munsell@outlook.com'
        message = str(json.dumps(summary, indent=4))
        
        text_subtype = 'plain'
        msg = MIMEText(message, text_subtype)
        msg['Subject']= subject
        msg['From']   = Efrom 
        # send email
        conn = SMTP(smtp_server)
        conn.set_debuglevel(False)
        conn.login(Euser, Epass)
        try:
            conn.sendmail(Efrom, Eto, msg.as_string())
        finally:
            conn.quit()

    def get_ack_number(self, xml_json):
        # check for AcknowledgementNumber
        if 'AcknowledgementNumber' in xml_json:
            return xml_json['AcknowledgementNumber']
        else:
            return False
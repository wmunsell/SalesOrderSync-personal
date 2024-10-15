# Cabentry
### Overview
    Project to transfer exported XML Sales Orders from Cabentry to Zoho. 

    The operation is inteded to be placed within the Windows Task Scheduler to run on a specific interval. The script then references a specific folder in which exported Sales Orders from Cabentry are saved. As the script runs on its scheduled bases, it checks the folder for any new exports and processes all .xml files found within the folder. If none are found, it simple exits. All xml files that are successfully processed are then moved to an archive folder. Any issues or failures encountered durring this process are emaild to the specified recipients. 

### 

# Files
### Authenicate.py
    used for updating the Zoho API Key. this file references the Config.json file which contains all required credentials for renewing the API Key. 

### Cabentry.py
    used for accessing and manipulating exported Sales Order XML files. 

### Format_Sales_Order.py
    once the export from Cabentry has been converted into a JSON object, its then passed to this file to parse through all of the data and generate a properly formatted sales order. 

### Workflow_Tools.py
    used for general purpose tools that do not have a specific reference to either Zoho or Cabentry

### Zoho_Tools.py
    used for all operations that ineteract with Zoho. 

### Main.py
    used for tying it all together. this file does not contain any functions and only references the other files. this file only contains the primary logic and operations. 

# Requirements
    Python
    requests
    xmltodict
    smtplib

# Installation links 
### Python Latest - [Download Link](https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe)
+ Once the installation is complete open a command prompt and run the following command
    - "pip install requests xmltodict smtplib"

# Scheduler instructions
    create a general task
    add two triggers, one for morning and one for afternoon
    for actions
        start a program 
            action = path to python exe (C:\Python310\python.exe)
            arguments = commented path to MAIN.py ("C:\Users\...\SalesOrderSync\MAIN.py")

    

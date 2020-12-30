from nornir import InitNornir 
from nornir_netmiko.tasks import netmiko_send_config , netmiko_send_command# importing the netmiko functions 
from nornir.core.exceptions import NornirExecutionError
from termcolor import colored
from nornir_utils.plugins.functions import print_result , print_title # importing the print_result function 
import os 
import subprocess
import sqlite3
import time
from netmiko import ConnectHandler
import yaml 


conn = sqlite3.connect('vlans.db',check_same_thread=False)
c =conn.cursor()
with open ("hosts.yaml", "r") as f: 
    Devices = yaml.load(f, Loader=yaml.FullLoader)

nornir = InitNornir(config_file="config.yaml", dry_run=True , core={"raise_on_error":True})
try:
    results = nornir.run(task=netmiko_send_command, name ="Vlan_Automation",command_string="show vlan brief", use_textfsm=True)
    
    #print_result(results)
except: 
    NornirExecutionError
vlan_ID = [] 
vlan_NAME = []
def Sync():   
    results = nornir.run(task=netmiko_send_command, name ="Vlan_Automation",command_string="show vlan brief", use_textfsm=True)  
    for key in results.keys():
        response = results[key].result
        
        nr_of_vlans = len(response) - 4 
        if nr_of_vlans == 1: 
            print('There is only the default vlan')
            
        else:


            for vlan in range (0,nr_of_vlans):
                vlan_id =  response[vlan]['vlan_id']
                vlan_name= response[vlan]['name']
                vlan_ID.append(vlan_id)
                vlan_NAME.append(vlan_name)
        
    #print(vlan_ID)
    #print(vlan_NAME)

    print(colored('Displaying the current vlans id existing on the switch..','yellow'))
    print(colored( vlan_ID,'blue'))
    print(colored('The Device is synchronizing with the database... please wait!','green'))
    def sync_sw_db():
        table  = ''' CREATE TABLE IF NOT EXISTS vlans(
            id integer primary key,
            name text , 
            decription text
            ); '''
        
        c.execute(table)

        c.execute("DElETE FROM vlans")
        for x , y in zip(vlan_ID , vlan_NAME):
            
            
            c.execute("INSERT OR REPLACE  INTO vlans(id, name , description) VALUES(?, ?, ?)",(x, y , 'no desc availabe for sw ios'))


        conn.commit()

    print(colored('DONE! , Sync is complete!','green'))
    sync_sw_db()
Sync()

print(colored('Do you want to configure a vlan on a switch ? Answer yes or no...','white'))
answer = input()
cisco_iosSW1 = {
'device_type': 'cisco_ios',
'host': Devices['Switch1']['hostname'],
'username': Devices['Switch1']['username'],
'password': Devices['Switch1']['password'],
'secret': Devices['Switch1']['password'],
'port':'22',
}
net_connect = ConnectHandler(**cisco_iosSW1)
net_connect.enable()
if answer == 'yes': 
    print('The switch have the following vlans already configured:')
    print(colored(vlan_ID,'blue'))
    print('Please configure one that is not on the list')
    print('Enter the vlan id: ')
    vlan_user_id = input()

    print('Enter the vlan name:')
    vlan_user_name = input()


    cmds = ['conf t', 'vlan ' + str(vlan_user_id) , 'name '  + vlan_user_name, 'end']
    output = net_connect.send_config_set(cmds)
    print(colored('Vlan sucesfully added!'+' Please wait while the database is synchornizng....','green'))
    vlan_ID.clear()
    vlan_NAME.clear()
    time.sleep(7)
    Sync()
    print(colored('Done synchronizing with the database','green'))



    
elif answer == 'no':
    print('Do you want to delete a vlan? yes or no' )
    answ = input()
    if answ == 'yes':
        print('The switch have the following vlans already configured:')
        print(colored(vlan_ID,'blue'))
        print('Please type the id of the vlan you want to delete')
        user_del = input()
        cmds1  =['conf t', 'no vlan ' + str(user_del), 'end']

        net_connect.send_config_set(cmds1)
        print(colored('Vlan '+str(user_del) + ' deleted','red') + ' Please wait while the database is synchornizng')
        vlan_ID.clear()
        vlan_NAME.clear()        
        time.sleep(7)
        
        Sync()

    else:
        print('Ok, bye')



def Database_vlan():

    print(colored('We are on the DATABASE now!!','red'))
    c.execute("SELECT id FROM vlans")
    rows =c.fetchall()
    
    print('Do you want to add a vlan to the database ?  yes or no ')
    rasp = input()
    if rasp == 'yes':
        print('Here are the vlans id curently present on the database , please add a new vlan id :')
        print(colored(rows,'blue'))
        new_id = input()
        print('Please add a name to your vlan (max 20 characters)')
        new_name = input()
       
           

        c.execute("INSERT OR REPLACE  INTO vlans(id, name , description) VALUES(?, ?, ?)",(new_id, new_name , 'no desc availabe for sw ios'))
        conn.commit()
        print(colored('New Vlan was added to the database','green'))
        print(colored('Synchronizing the databse with switch...','green'))

        cmds = [ 'vlan ' + str(new_id) , 'name '  + new_name , 'end']
        out = net_connect.send_config_set(cmds)
        print(colored('DONE! the vlan was added to the switch','green'))

      

    elif rasp == 'no':
        print('Do you want to delete a vlan from the database? yes or no ')
        delet = input()
        if delet == 'yes':
            print('Here are the vlans id currently present on the database , type the id of the one you want to delete')
            print(colored(rows,'blue'))
            del_id = input()
            c.execute(f"DELETE FROM vlans WHERE id ={del_id}")
            conn.commit()
            print(colored('Vlan ' + str(del_id) + ' was deleted from the database','red'))
            print('Synchronizing with the switch')
            cmdss = ['conf t' , 'no vlan '+ str(del_id), 'end' ]
            net_connect.send_config_set(cmdss)
            print(colored('Done , the switch is synchronized and the vlan was deleted','green'))

        
Database_vlan()
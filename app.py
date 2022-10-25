from netmiko import ConnectHandler
from datetime import datetime
import getpass
import os
import sys
from pprint import pprint
import subprocess
import platform
import pandas as pd

class CustomError(Exception):
    pass

def MainProgram(macs):
    # Asks user for credentials
    wlc, wlc_username, wlc_password = GetCred()

    net_device = {
        'device_type': 'cisco_ios',
        'ip': wlc,
        'username': wlc_username,
        'password': wlc_password,
    }

    try:
        net_connect = ConnectHandler(**net_device)
    except Exception as e:
        print(e)
        input("ENTER to exit...")
        sys.exit()

    # Runs show wireless client on WLC
    output, count, macs_in_error, ips_in_error = VerifyConnection(macs, net_connect)

    # Runs following code if macs are found in error state
    if output:

        # Saves output to a file
        with open("output.txt", 'a') as file1:
            print("Saving output to file")
            file1.write(f"------------------------{datetime.now()}---------------------------\n")
            file1.write(f"-------------------Found {str(count)} device(s) stuck in error state----------------------\n")
            for text in output:
                file1.write(text)
            file1.write("\n")
            file1.write("\n")
        
        # Informs the user on how many devices are in run state
        print(f"Found {str(count)} device(s) in run state, but not on the network.")

        # Asks the user if they want to run the troubleshooter on the devices in a run state, but not able to ping.
        pprint(output)
        user_input = input("Would you like run the troubleshooter for the devices in a run state? (y/N) ").upper()[:1] or "N"
        if user_input == "Y":
            for mac, ip in zip(macs_in_error, ips_in_error):
                Troubleshoot(mac, net_connect, ip)
        print("Time to Party!")
        input("ENTER to exit...")
    else:
        print("No devices in run state.")
        input("ENTER to exit...")
    
    # Disconnects from device
    net_connect.disconnect()

def GetCred():
    wlc = input("Enter IP of WLC: ")
    wlc_username = input("wlc Username: ")
    wlc_password = getpass.getpass()
    return wlc, wlc_username, wlc_password

def VerifyConnection(macs, net_connect, count=0):

    output = []
    macs_in_error = []
    ips_in_error = []

    def FindStatusOfClient(mac, net_connect, count=0):
        status = net_connect.send_command('show wireless client mac-address '\
            +mac+' detail') # command to verify mac is connected
        
        # If device is in a run state it will parse the output and find more info
        if status:
            status = status.strip("\n")
            connected_for = status[460:566]
            status = status[:460]
            ip = ''
            ip = status.split("\n")[2][22:]

            # Tries to ping the device and saves output
            if ip:
                state = ping(ip)
            else:
                state = False
            
            if not state:
                print("Found device in error state")
                ap_name = status.split("\n")[5][9:]

                # Connects to WLC to gather AP and switch information
                ap_stats = net_connect.send_command('show ap cdp neighbors | in ' + ap_name) # This is a little slow
                ap_stats = ap_stats.strip("\n")

                # Saves the variables to a list
                output.append(status)
                output.append(connected_for)
                output.append("\n")
                output.append(ap_stats)
                output.append("\n")
                output.append("________________________________________________________")
                output.append("\n")
                macs_in_error.append(mac)
                ips_in_error.append(ip)
                count += 1
        
        return output, count, macs_in_error, ips_in_error

    # If macs is presented as a list it will use a loop
    if type(macs) == list:
        total = len(macs)
        for i, mac in enumerate(macs):
            print(f"Scanning {i+1} out of {total+1}")
            output, count, macs_in_error, ips_in_error = FindStatusOfClient(mac, net_connect, count)

    # If only one mac address was given
    elif type(macs) == str:
        output, count, macs_in_error, ips_in_error = FindStatusOfClient(macs, net_connect, count)

    else:
        raise CustomError('VerifyConnection accepts list or str. Neither was given.')
        input("ENTER to exit...")
        net_connect.disconnect()
        sys.exit()
    
    return output, count, macs_in_error, ips_in_error

def Deauthenticate(macs_in_error, net_connect, ips_in_error=False):
    if type(macs_in_error) == list and type(ips_in_error) == list:
        for mac, ip in zip(macs_in_error, ips_in_error):
            net_connect.send_command(f"wireless client mac-address {mac} deauthenticate")
            ping(ip, 4)
    elif type(macs_in_error) == list:
        for mac in macs_in_error:
            net_connect.send_command(f"wireless client mac-address {mac} deauthenticate")
    elif type(macs_in_error) == str:
        net_connect.send_command(f"wireless client mac-address {macs_in_error} deauthenticate")
        if ips_in_error:
                ping(ips_in_error, 4)
    else:
        raise CustomError('Deauthenticate accepts list or str. Neither was given.')
        input("ENTER to exit...")
        net_connect.disconnect()
        sys.exit()

def ping(host_ping, count=1):
    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, str(count), host_ping]
    return subprocess.call(command) == 0

def Troubleshoot(mac_in_error, net_connect, ip_in_error):

    # Defines variables
    exit_tshoot = False
    show_tshoot = ''
    cmd_tshoot = 'cls' if platform.system().lower()=='windows' else 'clear'

    # Menu for Troubleshooter (loops until exit)
    while exit_tshoot == False:
        os.system(cmd_tshoot)
        print(show_tshoot)
        print(f"""
        
        -------------Troubleshoot-------------

            1.) Ping device {ip_in_error}
            2.) Deauthenticate {mac_in_error}
            3.) Verify Connection to WLC {mac_in_error}
            4.) Exit

        """)
        user_input = str(input("Enter a selection: "))
        if user_input == '1':
            number_of_pings = int(input("How many pings? ") or 4)
            ping(ip_in_error, number_of_pings)
        elif user_input == '2':
            Deauthenticate(mac_in_error, net_connect, False)
        elif user_input == '3':
            output_tshoot, null, null, ip_in_error = VerifyConnection(mac_in_error, net_connect)
            pprint(output_tshoot)
            input("ENTER to continue...")
        elif user_input == '4':
            exit_tshoot = True
        elif user_input == 'exit':
            exit_tshoot = True
        else:
            show_tshoot = 'ERROR: You did not enter a number!'

def ReadTabbedFile():
    # Verifying that an inventory file exists!
    exists1 = os.path.isfile('inventory_tabbed.txt')
    if not exists1:
        print('Inventory_tabbed.txt file not found!')
        input("ENTER to exit...")
        sys.exit()
    
    # Inputs each line with out a comment into an array called hosts
    macs = []
    mac_check = []
    df = pd.read_csv('inventory_tabbed.txt', delimiter='\t', names=['Text','Model','Device Name','Description','Device Type','Device Protocol','Status','IPv4 Address','Copy','Super Copy'])
    df = df.loc[(df['Status'] == 'Unregistered')]
    df = list(df['Device Name'])

    for line in df:
        line = line[3:]
        line = line[:4]+'.'+line[4:8]+'.'+line[8:]
        if line not in mac_check and len(line) == 14:
            macs.append(line.upper())
    return macs

def ReadReturnFile():
    # Verifying that an inventory file exists!
    exists1 = os.path.isfile('inventory_return.txt')
    if not exists1:
        print('Inventory_return.txt file not found!')
        input("ENTER to exit...")
        sys.exit()

    # Inputs each line with out a comment into an array called hosts
    macs = []
    with open('inventory_return.txt') as fh:
        for line in fh:
            if '#' not in line:
                line = line.strip('\n')
                line = line.replace(".", "")
                line = line.replace(":", "")
                line = line[:4]+'.'+line[4:8]+'.'+line[8:]
                macs.append(line.upper())
    return macs

if __name__ == '__main__':

    # Defines variables for Main Menu
    exit_menu = False
    show_menu = ""
    clear_terminal = 'cls' if platform.system().lower()=='windows' else 'clear'
    macs = []

    while exit_menu == False:
        
        ### Runs Main Program (after selecting an item) ###
        if macs:
            os.system(clear_terminal)
            MainProgram(macs)
            sys.exit()
        
        ### Main Menu ###
        os.system(clear_terminal)
        print(show_menu)
        show_menu = ""
        print("""
            
            -------------Verify Connection-------------

                1.) Inventory_tabbed.txt using pandas delimiter='\\t'
                2.) Inventory_return.txt using for loop (mac on each line)
                3.) Exit

            """)
        menu_selection = input("What list would you like to check? (1): ") or '1'

        # Varify connected devices in inventory_tabbed.txt
        if menu_selection == '1':
            macs = ReadTabbedFile()
        elif menu_selection == '2':
            macs = ReadReturnFile()
        elif menu_selection == '3':
            sys.exit()
        else:
            show_menu = "You did not enter a valid selection."

from netmiko import ConnectHandler
from datetime import datetime
import getpass
import os
import sys

def GetCred():
    wlc = input("Enter IP of WLC: ")
    wlc_username = input("wlc Username: ")
    wlc_password = getpass.getpass()
    return wlc, wlc_username, wlc_password

def VerifyConnection(wlc, wlc_username, wlc_password, macs):
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
        sys.exit()

    total = len(macs)
    results = []
    macs_in_error = []
    ips_in_error = []
    count = 0
    for i, mac in enumerate(macs):
        print("Scanning {} out of {}".format(i, total))
        status = net_connect.send_command('show wireless client mac-address '\
            +mac+' detail') # command to verify mac is connected
        status = status.strip("\n")
        status = status[:203]
        if status:
            print("Found device in run state")
            ap_name = status.split("\n")[4]
            ap_name = ap_name[9:]
            ap_stats = net_connect.send_command('show ap cdp neighbors | in ' + ap_name) # This is a little slow
            ap_stats = ap_stats.strip("\n")
            results.append(status)
            results.append("\n")
            results.append(ap_stats)
            results.append("\n")
            results.append("________________________________________________________")
            results.append("\n")
            macs_in_error.append(mac)
            ip = status.split("\n")[1]
            ip = ip[22:]
            ips_in_error.append(ip)
            count += 1
    
    # Disconnects from device
    net_connect.disconnect()

    return results, count, macs_in_error, ips_in_error

def deauthenticate(wlc, wlc_username, wlc_password, macs_in_error, ips_in_error):
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
        sys.exit()
    
    for mac, ip in zip(macs_in_error, ips_in_error):
        net_connect.send_command(f"wireless client mac-address {mac} deauthenticate")
        os.system(f"ping {ip}")
    
    # Disconnects from device
    net_connect.disconnect()

if __name__ == '__main__':
    # Verifying that an inventory file exists!
    exists1 = os.path.isfile('inventory.txt')
    if not exists1:
        print('Inventory file not found!')
        sys.exit()

    # Inputs each line with out a comment into an array called hosts
    macs = []
    with open('inventory.txt') as fh:
        for line in fh:
            if '#' not in line:
                line = line.strip('\n')
                line = line.replace(".", "")
                line = line.replace(":", "")
                line = line[:4]+'.'+line[4:8]+'.'+line[8:]
                macs.append(line.upper())
    if macs:
        # Asks user for credentials
        wlc, wlc_username, wlc_password = GetCred()

        # Runs show wireless client on WLC
        results, count, macs_in_error, ips_in_error = VerifyConnection(wlc, wlc_username, wlc_password, macs)

        # Runs following code if macs are found in error state
        if results:
            # Saves output to a file
            with open("output.txt", 'a') as file1:
                print("Saving output to file")
                file1.write(f"------------------------{datetime.now()}---------------------------\n")
                file1.write(f"-------------------Found {str(count)} device(s) in run state----------------------\n")
                for text in results:
                    file1.write(text)
                file1.write("\n")
                file1.write("\n")
            # Informs the user on how many devices are in run state
            print(f"Found {str(count)} device(s) in run state.")
            # Asks the user if they want to deauthenticate the devices in a run state
            user_input = input("Would you like to deauthenticate the devices in a run state? (y/N) ").upper() or "N"
            if user_input == "Y":
                deauthenticate(wlc, wlc_username, wlc_password, macs_in_error, ips_in_error)
            print("Time to Party!")
        else:
            print("No devices in run state.")
    else:
        print("No macs in inventory.txt")

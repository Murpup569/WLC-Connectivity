# WLC-Conectivity
Checks conectivity of devices to a Cisco 9800 WLC

This script requires an inventory.txt file with mac addresses in it.

# This was used to troubleshoot Cisco bug CSCvv99765.
1. Open CUCM
2. Go to Device > Phone
3. Select "Device Type" from drop down
4. In the drop down "Select item or enter search text" click "Cisco 8821"
5. Click "Find"
6. Change the Rows per Page to the max
7. Copy output into a plain text editor like notepad and then copy the text from notepad (this will remove any formatting from CUCM)
8. Paste into excel
9. With the added text still highlighted click add table (verify that "my table has headers" is uncheckmarked)
10. Filter the column "Status" to "Unregistered" only
11. In a blank cell to the right enter "=RIGHT(<the cell that has the device name is in>, 12)" (This will give you a list of mac addresses to use in my script!
12. Paste the macs into inventory.txt

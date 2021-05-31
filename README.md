# Vaccine_Notifier
A script to notify through mobile sms, whenever your defined conditions regarding vaccine slot availability on cowin app are met. This script only provides notification and the slot booking is not supported yet.

Pre-requisite:

Create a free account on https://www.twilio.com/ to get sms update regarding slot availability on your phone.

https://www.youtube.com/watch?v=ILMuc1KASbo You can follow this video to setup your twilio account.

Remember once the notification of slot_availability has been sent, the script will exit and in case you want it to keep on running, you will have to rerun it.

Steps to execute the script:

a. Install python 3.7 on your system.

b. Take copy of the repo and open the terminal.

c. Run command 'pip install -r requirements.txt'

d. Enter the values in user_input.cfg file as explained in user_input_description.txt

e. Open the vaccine_notification.py with any editor and add the folder path of <vaccine_notifier_script> under variable 'BASE_PATH'.

f. Run the script using command 'python <script_folder>/vaccine_notification.py'

g. A log file with name 'vaccine_notifier_<current_date>.log' will be created in the <script_folder> directory so that you can monitor status and track errors.

h. An excel file with name 'vaccine_data.xlsx' will also be created giving you details about slot availability in <script_folder>.

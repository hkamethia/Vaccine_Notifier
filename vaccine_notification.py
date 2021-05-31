import requests, sys, time
from datetime import datetime, timedelta
import pandas as pd
import utils
from twilio.rest import Client

BASE_PATH = 'C:/Users/welll/Documents/vaccine_notifier'

config_dict = utils.read_configs_file(BASE_PATH)
log_filename = f'{BASE_PATH}/vaccine_notifier_{datetime.now().strftime("%d-%m-%Y")}.log'
logger = utils.create_logger(log_filename)

excel_file_name = f'{BASE_PATH}/vaccine_data.xlsx'
url_availability_by_district_id = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id={}&date={}'
url_availability_by_pin = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={}&date={}'

headers = {
    'user-agent': config_dict['user_agent']
}

# these are the fields whose data we write to excel
required_fields = [
    'center_id',
    'name',
    'address',
    'district_name',
    'state_name',
    'fee_type',
    'fee',
    'date',
    'available_capacity',
    'available_capacity_dose1',
    'available_capacity_dose2',
    'min_age_limit',
    'vaccine',
    'from',
    'to',
    'slots'
]

# these are the fields whose data we are sending to user mobile no
alert_fields = [
    'name',
    'address',
    'vaccine',
    'available_capacity_dose1',
    'available_capacity_dose2',
    'min_age_limit'
]


def send_alert(body):
    """
    Send text alert to your mobile number
    :param body:
    :return:
    """
    try:
        logger.debug('Preparing to send available slots data to the user provided mobile no.')
        client = Client(config_dict['account_sid'], config_dict['token'])

        message = client.messages.create(
            body=body,
            from_=config_dict['sender_no'],
            to=config_dict['receiver_no']
        )

        if message.sid:
            logger.debug(f'Successfully sent the slots data:{body}\n to the user provided no. :: {config_dict["receiver_no"]}')
            logger.debug(f'Message id: {message.sid}')

    except Exception as e:
        logger.error(f'Failed to send the message::{body}\n to provided credentials:: {config_dict["receiver_no"]}')
        logger.error('ERROR:: ' + str(e))
        print('ERROR:: ' + str(e))


def get_vaccine_slots(vaccine_data, failed_retries):
    """
    Check whether the vaccine slots are available as per user input
    :param failed_retries:
    :param vaccine_data:
    :return:
    """

    try:

        df = pd.DataFrame(vaccine_data['sessions'])
        if df.empty:
            return False
        df = df[required_fields]
        df = df[df['vaccine'].isin(config_dict['vaccine'].split(','))]
        df = df[df['min_age_limit'].isin([int(x) for x in config_dict['min_age'].split(',')])]
        df = df[df['fee_type'].isin(config_dict['fee'].split(','))]

        if retries == 0:
            logger.debug(f'Checking the data for::\nVaccines :: {config_dict["vaccine"]}\n'
                         f'Minimum age limit :: {config_dict["min_age"]}\n'
                         f'Fee type :: {config_dict["fee"]}')

        if len(config_dict['dose'].split(',')) == 1:
            if config_dict['dose'] == '1':
                df = df[df['available_capacity_dose1'] > 0]
                logger.debug('Checking if doses for slot 1 are available')
            elif config_dict['dose'] == '2':
                df = df[df['available_capacity_dose2'] > 0]
                logger.debug('Checking if doses for slot 2 are available')
        else:
            df = df[df['available_capacity'] > 0]
            logger.debug('Since no specific slot was provided.\nChecking if doses for any slot are available')

        if not df.empty:
            logger.debug('Available slots found')
            body = df[alert_fields].to_json()
            df.to_excel(excel_file_name)
            logger.debug(f'Available slots data written to the excel {excel_file_name}')
            print(f'Slots are available. Check the excel {excel_file_name}')
            send_alert(body)
            return True
        return False

    except Exception as e:
        logger.error('ERROR:: ' + str(e) + '\n\n\n')
        print('ERROR:: ' + str(e))
        if failed_retries >= 0:
            failed_retries -= 1
            return False
        send_alert('Exited the process\nERROR::' + str(e))
        sys.exit(1)


if __name__ == "__main__":
    # get_state_ids()
    # get_districts()
    retries = 0
    failed_retries = 3

    try:
        config_dict['date'] = (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y') if config_dict['date'] == '' else config_dict['date']

        search_by = config_dict['search_by'].lower()
        if 'district_id' in search_by.split(','):
            url = url_availability_by_district_id.format(config_dict['district_id'], config_dict['date'])
            logger.debug(f'You selected option search slot by district_id:: {config_dict["district_id"]}')

        else:
            url = url_availability_by_pin.format(config_dict['pincode'], config_dict['date'])
            logger.debug(f'You selected option to search slot by pin:: {config_dict["pincode"]}')

        max_retries = sys.maxsize if config_dict['max_retries'] == '' else int(config_dict['max_retries'])
        sleep_time = 900 if config_dict['timeout'] == '' else int(config_dict['timeout'])*60

        while retries <= max_retries:
            logger.debug(f'Starting processing for retry no. :: {retries}')

            # fetching data from api
            with requests.session() as s:
                vaccine_data = s.get(url, headers=headers).json()

            # if slot not found, keep retrying until retries exhausted or slot is found
            if not get_vaccine_slots(vaccine_data=vaccine_data, failed_retries=failed_retries):

                if retries < max_retries:
                    logger.debug(f'Starting sleep after retry no. :: {retries}')
                    time.sleep(sleep_time)
                    logger.debug(f'Sleep completed after retry no. :: {retries}')

                logger.error(f'Slots were not found for retry no. :: {retries}')
                retries += 1

            else:
                break
        logger.debug('SUCCESSFUL :: Exiting the script as slots were found')

    except Exception as e:
        logger.error('ERROR::' + str(e) + '\n\n\n')
        print('ERROR::' + str(e))
        send_alert('ERROR::' + str(e))
        sys.exit(1)

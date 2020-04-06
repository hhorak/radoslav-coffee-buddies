#!/bin/env python3

# MIT License
#
# Copyright (c) 2020 Honza Horak <hhorak@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pprint import pprint
import random
import argparse
import os

# for messages
from json import dumps
from httplib2 import Http
import csv

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
ENV_OK = True

try:
    # The ID and range of a sample spreadsheet.
    FORM_SPREADSHEET_ID = os.environ['RADOSLAV_FORM_SPREADSHEET_ID']
    SAMPLE_RANGE_NAME = 'Form Responses 1!A2:F'
    MATCHES_RANGE_NAME = 'Matches!A2:B'

    # Taken from the chat (room -> Configure webhooks)
    CHAT_URL = os.environ['RADOSLAV_CHAT_URL']

    # From webapi as topic id
    CHAT_THREAD = os.environ['RADOSLAV_CHAT_THREAD']

except KeyError:
    print("ERROR: The following environment variables are not set: RADOSLAV_FORM_SPREADSHEET_ID, RADOSLAV_CHAT_URL, RADOSLAV_CHAT_THREAD")
    ENV_OK = False

ROW_TIMESTAMP=0
ROW_EMAIL=1
ROW_AGREEMENT=2
ROW_HOW_MANY=3
ROW_ALL_ASSIGNED=4
ROW_HOW_MANY_ASSIGNED=5

VERBOSE = False
DEBUG = False

def find_paris(names_to_match, historic_matches, chat_users, safe_messages=False):
    pairs = []
    nice_output = []
    pairs_found = False

    # now, create pairs from shuffled list and stop if the pair already met
    names_working = names_to_match.copy()
    while len(names_working) >= 2:
        buddy_a = names_working.pop()
        buddy_b = names_working.pop()
        if buddy_a == buddy_b:
            print("ERROR: Buddy {} paired with {} which would be boring. Try the random match again.".format(buddy_a, buddy_b))
            break
        if {buddy_a, buddy_b} in historic_matches:
            print("ERROR: Buddies {} and {} already met. Try the random match again.".format(buddy_a, buddy_b))
            if VERBOSE:
                print("Names to match:")
                pprint(names_to_match)
                print("History matches:")
                pprint(historic_matches)
            break
        pairs.append({buddy_a, buddy_b})
        if buddy_a in chat_users:
            buddy_a_repr = '<{}>'.format(chat_users[buddy_a]['id'])
        else:
            buddy_a_repr = '@{}'.format(buddy_a.replace('@redhat.com', ''))
        if buddy_b in chat_users:
            buddy_b_repr = '<{}>'.format(chat_users[buddy_b]['id'])
        else:
            buddy_b_repr = '@{}'.format(buddy_b.replace('@redhat.com', ''))

        # this is to not bother real people
        if safe_messages:
            print('Using hhorak instead {} and {}:'.format(buddy_a_repr, buddy_b_repr))
            buddy_a_repr = '<users/106875931551226392026> (originally {})'.format(buddy_a)
            buddy_b_repr = '<users/106875931551226392026> (originally {})'.format(buddy_b)

        nice_output.append('Coffee Buddies match found: {} and {}, please, contact each other and agree on time and format of the coffee chat. Have fun!'.format(buddy_a_repr, buddy_b_repr))
        pairs_found = True

    if pairs_found:
        print("Found pairs ({}):".format(len(pairs)))
        pprint(pairs)

    return (pairs, nice_output, pairs_found)


def get_chat_users():
    chat_users = {}
    with open('users-ids', 'r') as f:
        reader = csv.reader(f, dialect='excel', delimiter='\t')

        for row in reader:
            chat_users[row[0]] = {
                'nick': row[0].replace('@redhat.com', ''),
                'mail': row[0],
                'name': row[2],
                'id': row[1],
            }
    return chat_users


def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_historic_matches(sheet_values):
    # Read the matches assigned in history
    historic_matches = []

    result = sheet_values.get(spreadsheetId=FORM_SPREADSHEET_ID,
                                range=MATCHES_RANGE_NAME).execute()
    matches_values = result.get('values', [])
    if not matches_values:
        print('ERROR: No data found for matches in {}.'.format(MATCHES_RANGE_NAME))
    else:
        for row in matches_values:
            historic_matches.append({row[0], row[1]})
    return (matches_values, historic_matches)


def get_registration_form_data(sheet_values):
    result = sheet_values.get(spreadsheetId=FORM_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('ERROR: No data found in {}.'.format(SAMPLE_RANGE_NAME))
        exit(1)

    return values


def normalize_form_data(form_data):
    for row in form_data:
        if DEBUG:
            pprint(row)

        # normalize previously assigned number (add missing columns, parse them)
        try:
            previously_assigned = int(row[ROW_HOW_MANY_ASSIGNED])
        except IndexError:
            # add missing columns
            for i in range(ROW_HOW_MANY_ASSIGNED-len(row)+1):
                 row.append('')
            previously_assigned = 0
        except ValueError:
            previously_assigned = 0
        row[ROW_HOW_MANY_ASSIGNED] = previously_assigned

        # normalize how many assignees are wanted (parese, set to 1 if missing)
        try:
            if row[ROW_HOW_MANY] == '':
                how_many_wanted = 1
            else:
                how_many_wanted = int(row[ROW_HOW_MANY])
        except ValueError:
            print("ERROR: not possible to parse count of expected meetups for {}. Fix that manually in the sheet first.".format(row[ROW_EMAIL]))
            exit(1)
        row[ROW_HOW_MANY] = how_many_wanted

        # check if there are too many assigned
        if row[ROW_HOW_MANY_ASSIGNED] >= row[ROW_HOW_MANY]:
            row[ROW_ALL_ASSIGNED] = 'yes'
            if VERBOSE:
                print("Ignoring name {} (all assigned already, marking as such)".format(row[ROW_EMAIL]))


def create_pairs(form_data):
    names_to_match = []

    for row in form_data:
        if DEBUG:
            pprint(row)

        if row[ROW_EMAIL] in names_to_match:
            if VERBOSE:
                print("Ignoring name {} (aleady in the list)".format(row[ROW_EMAIL]))
            continue

        # check agreement
        if not row[ROW_AGREEMENT].lower().startswith('yes'):
            if VERBOSE:
                print("Ignoring name {} (no approval)".format(row[ROW_EMAIL]))
            continue

        # check assignment done
        if row[ROW_ALL_ASSIGNED].lower().startswith('yes'):
            if VERBOSE:
                print("Ignoring name {} (marked as all assigned)".format(row[ROW_EMAIL]))
            continue

        if VERBOSE:
            print("Adding name {} to the random match".format(row[ROW_EMAIL]))
        names_to_match.append(row[ROW_EMAIL])

    return names_to_match


def write_back(sheet_values, matches_values, form_data):
    # update back the matched names
    matches_update_request = sheet_values.update(spreadsheetId=FORM_SPREADSHEET_ID, range=MATCHES_RANGE_NAME, valueInputOption='USER_ENTERED', body={'range':MATCHES_RANGE_NAME, 'values':matches_values, 'majorDimension':'ROWS'})
    response = matches_update_request.execute()
    if DEBUG:
        pprint(response)
    print('Successfully updated {} cells in {}'.format(response['updatedCells'], response['updatedRange']))

    # update back the names and counts
    update_request = sheet_values.update(spreadsheetId=FORM_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, valueInputOption='USER_ENTERED', body={'range':SAMPLE_RANGE_NAME, 'values':form_data, 'majorDimension':'ROWS'})
    response = update_request.execute()
    if DEBUG:
        pprint(response)
    print('Successfully updated {} cells in {}'.format(response['updatedCells'], response['updatedRange']))


def send_messages(nice_output, skip_messages):
    print("This is to be printed to the chat:")
    print('\n'.join(nice_output))

    # basic setting for chat messages
    chat_message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    chat_message_http_obj = Http()

    for message in nice_output:
        bot_message = {'text' : message, 'thread': { 'name' : CHAT_THREAD }}

        if skip_messages:
            print('Messages sending skipped: {}'.format(message))
            continue

        chat_message_response = chat_message_http_obj.request(
            uri=CHAT_URL,
            method='POST',
            headers=chat_message_headers,
            body=dumps(bot_message),
        )

        if chat_message_response[0].status == 200:
            if DEBUG:
                pprint(chat_message_response)
            print('Message sent successfully to the chat: "{}"'.format(message))
        else:
            print('ERROR: Message not sent successfully:')
            pprint(chat_message_response)


# A tool that matches random people registred via a Google form
def main():
    """
    This tool works with data in the Google sheet (Google form output) and creates
    random matches of people who expressed wish to meet somebody else randomly.
    Checks that two people do not meet twice and works with the number of
    people to meet.

    Make sure the following environment variables are set:
      RADOSLAV_FORM_SPREADSHEET_ID: e.g. 1yZB7dSdhdVunvWzTMHv0kPIVnOmAzoyMfQw_Ct9MLn4 -- taken from the Google sheet URL
      RADOSLAV_CHAT_URL: e.g. 'https://chat.googleapis.com/v1/spaces/AAAAbsdfkj/messages?key=...=...' -- a string taken from the chat (room -> Configure webhooks)
      RADOSLAV_CHAT_THREAD: e.g. spaces/AAAAbsdfkj/threads/skdjflsdjflk -- can be figureout using html DOM explorer from the Google Hangout Chat code'
    """
    parser = argparse.ArgumentParser(description='A tool that matches random people registred via a Google form')
    parser.add_argument("--verbose", help="print more verbose output", action="store_true")
    parser.add_argument("--debug", help="print more debug output", action="store_true")
    parser.add_argument("--test-run", help="sets on --skip-write-back, --safe-messages, --safe-messages", action="store_true")
    parser.add_argument("--skip-write-back", help="do not write the data back to the sheet", action="store_true")
    parser.add_argument("--skip-messages", help="do not send any messages to the chat", action="store_true")
    parser.add_argument("--safe-messages", help="replace name in the messages with hhorak", action="store_true")
    parser.add_argument("--pairs-limit", help="limit number of pairs", type=int)

    if not ENV_OK:
        parser.print_help()
        print(main.__doc__)
        exit(1)

    args = parser.parse_args()

    if args.test_run:
        args.verbose = True
        args.skip_write_back = True
        args.skip_messages = True
        args.safe_messages = True

    if args.debug:
        args.verbose = True
        pprint(args)

    VERBOSE = args.verbose
    DEBUG = args.debug

    chat_users = get_chat_users()

    random.seed(a=None, version=2)

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    sheet_values = sheet.values()

    (matches_values, historic_matches) = get_historic_matches(sheet_values)

    form_data = get_registration_form_data(sheet_values)

    normalize_form_data(form_data)

    names_to_match = create_pairs(form_data)

    # make sure we have even number of names to create pairs
    if len(names_to_match) % 2 == 1:
        removed = names_to_match.pop()
        if VERBOSE:
            print("Removing odd name {}".format(removed))

    # we have a list of even size now, shuffle it
    random.shuffle(names_to_match)

    # now, remove some if limit is set
    if args.pairs_limit:
        while len(names_to_match) > 0 and len(names_to_match) > args.pairs_limit * 2:
            removed = names_to_match.pop()
            if VERBOSE:
                print("Removing name {} because it is over a limit".format(removed))

    if len(names_to_match) % 2 == 1:
        print("ERROR: this is unexpected, odd number of people here.")
        return

    # fail if we have no new names
    if len(names_to_match) == 0:
        print("Error: no names left. Wait for more registrations.")
        return

    if VERBOSE:
        print("Names to match:")
        pprint(names_to_match)

    # Try to do the random pairing
    (pairs, nice_output, pairs_found) = find_paris(names_to_match, historic_matches, chat_users, args.safe_messages)
    if pairs_found:
        for pair in pairs:
            matches_values.append([pair.pop(), pair.pop()])
    else:
        print("ERROR: No pairs found. Try the random match again.")
        return

    # increase number of assigned and mark names done if the number is enough
    for row in form_data:
        for pair in pairs:
            if row[ROW_EMAIL] in pair:
                if VERBOSE:
                    print("Updating assigned numbers:")
                    pprint(row)
                row[ROW_HOW_MANY_ASSIGNED] = row[ROW_HOW_MANY_ASSIGNED] + 1
                if row[ROW_HOW_MANY_ASSIGNED] >= row[ROW_HOW_MANY]:
                    row[ROW_ALL_ASSIGNED] = 'yes'

    if args.skip_write_back:
        print('Write-back skipped.')
    else:
        write_back(sheet_values, matches_values, form_data)

    send_messages(nice_output, args.skip_messages)

if __name__ == '__main__':
    main()
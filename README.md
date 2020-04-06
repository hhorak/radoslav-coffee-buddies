Radoslav Coffee Buddies
=======================

Coffee Buddies is an idea to connect two random people registred via Google form.
This small app helps connecting such registred people randomly and uses the spreadsheet
a the data storage.

It sends a message about randomly created pairs to the Google Hangout Chat.


```
usage: radoslav.py [-h] [--verbose] [--debug] [--test-run] [--skip-write-back]
                   [--skip-messages] [--safe-messages]
                   [--pairs-limit PAIRS_LIMIT]

A tool that matches random people registred via a Google form

optional arguments:
  -h, --help            show this help message and exit
  --verbose             print more verbose output
  --debug               print more debug output
  --test-run            sets on --skip-write-back, --safe-messages, --safe-
                        messages
  --skip-write-back     do not write the data back to the sheet
  --skip-messages       do not send any messages to the chat
  --safe-messages       replace name in the messages with hhorak
  --pairs-limit PAIRS_LIMIT
                        limit number of pairs

    This tool works with data in the Google sheet (Google form output) and creates
    random matches of people who expressed wish to meet somebody else randomly.
    Checks that two people do not meet twice and works with the number of
    people to meet.

    Make sure the following environment variables are set:
      RADOSLAV_FORM_SPREADSHEET_ID: e.g. 1yZB7dSdhdVunvWzTMHv0kPIVnOmAzoyMfQw_Ct9MLn4 -- taken from the Google sheet URL
      RADOSLAV_CHAT_URL: e.g. 'https://chat.googleapis.com/v1/spaces/AAAAbsdfkj/messages?key=...=...' -- a string taken from the chat (room -> Configure webhooks)
      RADOSLAV_CHAT_THREAD: e.g. spaces/AAAAbsdfkj/threads/skdjflsdjflk -- can be figureout using html DOM explorer from the Google Hangout Chat code'
```

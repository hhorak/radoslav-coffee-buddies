Radoslav Coffee Buddies
=======================

Coffee Buddies is an idea to connect two random people registred via Google form.
This small app helps connecting such registred people randomly and uses the spreadsheet
a the data storage.

It sends a message about randomly created pairs to the Google Hangout Chat.


```
usage: radoslav.py [-h] [--verbose] [--debug] [--test-run] [--skip-write-back]
                   [--skip-messages] [--safe-messages] [--skip-mails]
                   [--pairs-limit PAIRS_LIMIT]

A tool that matches random people registred via a Google form

optional arguments:
  -h, --help            show this help message and exit
  --verbose             print more verbose output
  --debug               print more debug output
  --test-run            sets on --skip-write-back, --safe-messages, --skip-
                        messages, --skip-mails
  --skip-write-back     do not write the data back to the sheet
  --skip-messages       do not send any messages to the chat
  --safe-messages       replace name in the messages with hhorak
  --skip-mails          do not send any mail notifications
  --pairs-limit PAIRS_LIMIT
                        limit number of pairs

    This tool works with data in the Google sheet (Google form output) and creates
    random matches of people who expressed wish to meet somebody else randomly.
    Checks that two people do not meet twice and works with the number of
    people to meet.

    Make sure the following environment variables are set:
    Compulsory:
      `RADOSLAV_FORM_SPREADSHEET_ID`: e.g. `1yZB7dSdhdVunvWzTMHv0kPIVnOmAzoyMfQw_Ct9MLn4` -- taken from the Google sheet URL
    Optionally, if the notification should go to the Google Chat:
      `RADOSLAV_CHAT_URL`: e.g. `https://chat.googleapis.com/v1/spaces/AAAAbsdfkj/messages?key=...=...` -- a string taken from the chat (room -> Configure webhooks)
      `RADOSLAV_CHAT_THREAD`: e.g. `spaces/AAAAbsdfkj/threads/skdjflsdjflk` -- can be figureout using html DOM explorer from the Google Hangout Chat code'
    Optionally, if the notification should be sent by mail:
      `RADOSLAV_SMTP_SERVER`: e.g. `smtp.corp.redhat.com`
      `RADOSLAV_MAIL_SENDER`: e.g. `hhorak+coffee@redhat.com`
      `RADOSLAV_SMTP_SERVER_PORT`: e.g. `25`
    Optionally, if you want to test the functionality, you can re-define recepient of the mail and Google Chat message by these variables:
      `RADOSLAV_CHAT_USER_TEST`: e.g. `106875931551282394923`
      `MAIL_SENDER_TEST`: e.g. `hhorak+coffee@redhat.com`
```

TwilioSMS
=========
Sends text message using [Twilio](https://www.twilio.com/docs/api/rest/sending-messages).

Properties
----------
- **creds**: API credentials.
- **from_**: Twilio number to send the message from.
- **message**: Text message to send.
- **recipients**: List of recipients to send text message to. Name and number.

Inputs
------
- **default**: Any list of signals. A text message is sent for each one.

Outputs
-------
None

Commands
--------
None

Dependencies
------------
-   [twilio](https://pypi.python.org/pypi/twilio)

TwilioVoice
===========
Makes voice calls using [Twilio](https://www.twilio.com/docs/api/rest/making-calls).

Properties
----------
- **creds**: API credentials.
- **endpoint**: Endpoint to configure voice server on.
- **from_**: Twilio number to make the voice call from.
- **host**: Host address to configure voice server on.
- **message**: Configurable voice message.
- **port**: Port to configure voice server on.
- **recipients**: List of recipients to call. Name and number.
- **url**: Twilio makes a POST request to this URL to get the TwiML for the phone call.

Inputs
------
- **default**: Any list of signals. A phone call is made for each one.

Outputs
-------
None

Commands
--------
None

Dependencies
------------
-   [twilio](https://pypi.python.org/pypi/twilio)

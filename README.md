Twilio
=======

Send text messages and make voice calls using [Twilio](https://www.twilio.com/docs/api/rest).

-   [TwilioSMS](https://github.com/nio-blocks/twilio_blocks#TwilioSMS)
-   [TwilioVoice](https://github.com/nio-blocks/twilio_blocks#TwilioVoice)

***

TwilioSMS
===========

Sends text message using [Twilio](https://www.twilio.com/docs/api/rest/sending-messages).

Properties
--------------

-   **from**: Twilio number to send the message from.
-   **message**: Text message to send.
-   **recipients**: List of recipients to send text message to. Name and number.
-   **creds**: API credentials.


Dependencies
----------------

-   [twilio](https://pypi.python.org/pypi/twilio)

Commands
----------------
None

Input
-------
Any list of signals. A text message is sent for each one.

Output
---------
None

***

TwilioVoice
===========

Makes voice calls using [Twilio](https://www.twilio.com/docs/api/rest/making-calls).

Properties
--------------

-   **from**: Twilio number to make the voice call from.
-   **url**: Twilio makes a POST request to this URL to get the TwiML for the phone call.
-   **recipients**: List of recipients to call. Name and number.
-   **creds**: API credentials.



Dependencies
----------------

-   [twilio](https://pypi.python.org/pypi/twilio)
-   [dicttoxml](https://pypi.python.org/pypi/dicttoxml/1.5.5)
-   nio web module

Commands
----------------
None

Input
-------
Any list of signals. A phone call is made for each one.

Output
---------
None

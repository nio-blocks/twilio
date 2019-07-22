from twilio.rest import TwilioRestClient
from threading import Thread
try:
    # location moved in 3.6.7
    from twilio.rest.exceptions import TwilioRestException
except:
    # keeps this for backwards compatability
    from twilio import TwilioRestException

from nio import TerminatorBlock
from nio.properties import (PropertyHolder, Property, ListProperty,
                            ObjectProperty, StringProperty, VersionProperty)


class Recipient(PropertyHolder):
    name = StringProperty(title='Name', default='')
    number = StringProperty(title='Number', default='5558675309')

    def __str__(self):
        return 'name: {}, number: {}'.format(self.name(), self.number())


class TwilioCreds(PropertyHolder):
    sid = StringProperty(title='SID', default='[[TWILIO_ACCOUNT_SID]]')
    token = StringProperty(title='Token', default='[[TWILIO_AUTH_TOKEN]]')


class TwilioSMS(TerminatorBlock):

    recipients = ListProperty(Recipient, title='Recipients', default=[])
    creds = ObjectProperty(TwilioCreds, title='Credentials')
    from_ = StringProperty(title='From', default='[[TWILIO_NUMBER]]')
    message = Property(title='Message', default='')
    version = VersionProperty("1.0.0")

    def __init__(self):
        super().__init__()
        self._client = None

    def configure(self, context):
        super().configure(context)
        self._client = TwilioRestClient(self.creds().sid(),
                                        self.creds().token())

    def process_signals(self, signals):
        for s in signals:
            self._send_sms(s)

    def _send_sms(self, signal):
        try:
            message = self.message(signal)

            for rcp in self.recipients(signal):
                args = (rcp.name(signal), rcp.number(signal), message)
                Thread(
                    target=self._broadcast_msg,
                    args=args).start()

        except Exception as e:
            self.logger.error(
                "Message evaluation failed: {0}: {1}".format(
                    type(e).__name__, str(e))
            )

    def _broadcast_msg(self, name, number, message, retry=False):
        body = "%s: %s" % (name, message)
        try:
            # Twilio sends back some useless XML. Don't care.
            response = self._client.messages.create(
                to=number,
                from_=self.from_(),
                body=body
            )
        except TwilioRestException as e:
            self.logger.error("Status %d" % e.status)
            if not retry:
                self.logger.debug("Retrying failed request")
                self._broadcast_msg(name, number, message, True)
            else:
                self.logger.error("Retry request failed")
        except Exception as e:
            self.logger.error("Error sending SMS to %s (%s): %s" %
                              (name, number, e))

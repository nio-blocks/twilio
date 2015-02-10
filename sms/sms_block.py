from twilio.rest import TwilioRestClient
try:
    # location moved in 3.6.7
    from twilio.rest.exceptions import TwilioRestException
except:
    # keeps this for backwards compatability
    from twilio import TwilioRestException
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.expression import ExpressionProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.string import StringProperty
from nio.modules.threading import Thread


class Recipient(PropertyHolder):
    name = StringProperty(title='Name', default='')
    number = StringProperty(title='Number', default='5558675309')


class TwilioCreds(PropertyHolder):
    sid = StringProperty(title='SID', default='[[TWILIO_ACCOUNT_SID]]')
    token = StringProperty(title='Token', default='[[TWILIO_AUTH_TOKEN]]')


@Discoverable(DiscoverableType.block)
class TwilioSMS(Block):

    recipients = ListProperty(Recipient, title='Recipients')
    creds = ObjectProperty(TwilioCreds, title='Credentials')
    from_ = StringProperty(title='From', default='[[TWILIO_NUMBER]]')

    message = ExpressionProperty(title='Message', default='')

    def __init__(self):
        super().__init__()
        self._client = None

    def configure(self, context):
        super().configure(context)
        self._client = TwilioRestClient(self.creds.sid,
                                        self.creds.token)

    def process_signals(self, signals):
        for s in signals:
            self._send_sms(s)

    def _send_sms(self, signal):
        try:
            message = self.message(signal)

            for rcp in self.recipients:
                Thread(target=self._broadcast_msg, args=(rcp, message)).start()

        except Exception as e:
            self._logger.error(
                "Message evaluation failed: {0}: {1}".format(
                    type(e).__name__, str(e))
            )

    def _broadcast_msg(self, recipient, message, retry=False):
        body = "%s: %s" % (recipient.name, message)
        try:
            # Twilio sends back some useless XML. Don't care.
            response = self._client.messages.create(
                to=recipient.number,
                from_=self.from_,
                body=body
            )
        except TwilioRestException as e:
            self._logger.error("Status %d" % e.status)
            if not retry:
                self._logger.debug("Retrying failed request")
                self._broadcast_msg(recipient, message, True)
            else:
                self._logger.error("Retry request failed")
        except Exception as e:
            self._logger.error("Error sending SMS to %s (%s): %s" % \
                               (recipient.name, recipient.number, e))

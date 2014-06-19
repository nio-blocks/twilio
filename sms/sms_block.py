from nio.util import eval_signal
from twilio.rest import TwilioRestClient
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.string import StringProperty


class Recipient(PropertyHolder):
    name = StringProperty(default='')
    number = StringProperty(default='5558675309')


class TwilioCreds(PropertyHolder):
    sid = StringProperty(default='')
    token = StringProperty(default='5558675309')
    
    
@Discoverable(DiscoverableType.block)
class Twilio(Block):
    
    recipients = ListProperty(Recipient)
    creds = ObjectProperty(TwilioCreds)
    from_ = StringProperty(default='')
    
    messages = ListProperty(str)

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
        for msg in self.messages:
            msg = eval_signal(signal, msg, self._logger)
            for rcp in self.recipients:
                self._broadcast_msg(rcp, msg)

    def _broadcast_msg(self, recipient, message):
        body = "%s: %s" % (recipient.name, message)
        try:
            response = self._client.messages.create(
                to=recipient.number,
                from_=self.from_,
                body=body
            )

            if response is None:
                raise Exception("Null response")
        except Exception as e:
            self._logger.error("Error sending SMS to %s (%s): %s" % \
                               (recipient.name, recipient.number, e))
            

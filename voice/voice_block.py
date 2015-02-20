from .mixins.web_server.web_server_block import WebServer
from twilio import twiml
from twilio.rest import TwilioRestClient
try:
    # location moved in 3.6.7
    from twilio.rest.exceptions import TwilioRestException
except:
    # keeps this for backwards compatability
    from twilio import TwilioRestException
from nio.common.signal.base import Signal
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.versioning.dependency import DependsOn
from nio.metadata.properties import ExpressionProperty, IntProperty, \
    ListProperty, ObjectProperty, StringProperty
from nio.modules.web import WebEngine
from nio.modules.web import RESTHandler
from nio.modules.threading import spawn
from nio.util.unique import Unique
from ..sms.sms_block import Recipient, TwilioCreds


class Speak(RESTHandler):

    def __init__(self, endpoint, blk):
        super().__init__('/'+endpoint)
        self.notify = blk.notify_signals
        self._logger = blk._logger
        self.messages = blk._messages

    def on_post(self, req, rsp):
        self._logger.debug('Speak is handling POST: {}, {}'.format(req, rsp))
        params = req.get_params()
        _id = params.get('msg_id', '')
        self._logger.debug('POST params: {}'.format(params))
        phrase = twiml.Response()
        phrase.say(self.messages.get(_id, ''))
        rsp.set_body(phrase)
        self.notify([Signal(params)])


@DependsOn("nio.modules.web", "1.0.0")
@Discoverable(DiscoverableType.block)
class TwilioVoice(Block, WebServer):

    recipients = ListProperty(Recipient, title='Recipients')
    creds = ObjectProperty(TwilioCreds, title='Credentials')
    from_ = StringProperty(default='[[TWILIO_NUMBER]]', title='From')
    url = StringProperty(default='', title='Callback URL')

    message = ExpressionProperty(
        default='An empty voice message',
        title='Message')
    port = IntProperty(title='Port', default=8184)
    host = StringProperty(title='Host', default='[[NIOHOST]]')
    endpoint = StringProperty(title='Endpoint', default='')

    def __init__(self):
        super().__init__()
        self._client = None
        self._messages = {}
        self._server = None

    def configure(self, context):
        super().configure(context)
        self._client = TwilioRestClient(self.creds.sid,
                                        self.creds.token)
        conf = {
            'host': self.host,
            'port': self.port
        }
        self.configure_server(conf, Speak(self.endpoint, self))

    def start(self):
        super().start()
        # Start Web Server
        self.start_server()

    def stop(self):
        super().stop()
        # Stop Web Server
        self.stop_server()

    def process_signals(self, signals):
        for s in signals:
            self._place_calls(s)

    def _place_calls(self, signal):
        try:
            msg = self.message(signal)
            msg_id = Unique.id()
            self._messages[msg_id] = msg
            for rcp in self.recipients:
                spawn(target=self._call, recipient=rcp, message_id=msg_id)
        except Exception as e:
            self._logger.error(
                "Message evaluation failed: {0}: {1}".format(
                    type(e).__name__, str(e))
            )

    def _call(self, recipient, message_id, retry=False):
        try:
            # Twilio sends back some useless XML. Don't care.
            to = recipient.number,
            from_ = self.from_,
            url = "%s?msg_id=%s" % (self.url, message_id)
            self._logger.debug("Making call to {}, from {}, with callback url"
                               " {}".format(to, from_ , url))
            self._client.calls.create(
                to=to,
                from_=from_,
                url=url
            )
        except TwilioRestException as e:
            self._logger.error("Status %d" % e.status)
            if not retry:
                self._logger.debug("Retrying failed request")
                self._call(recipient, message_id, True)
            else:
                self._logger.error("Retry request failed")
        except Exception as e:
            self._logger.error("Error sending voice {}: {}".format(
                recipient, e
            ))

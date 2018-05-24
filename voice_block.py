from twilio import twiml
from twilio.rest import TwilioRestClient
from uuid import uuid4
try:
    # location moved in 3.6.7
    from twilio.rest.exceptions import TwilioRestException
except:
    # keeps this for backwards compatability
    from twilio import TwilioRestException

from nio import Block, Signal
from nio.util.versioning.dependency import DependsOn
from nio.properties import Property, IntProperty, \
    ListProperty, ObjectProperty, StringProperty, VersionProperty
from nio.modules.web import RESTHandler, WebEngine
from nio.util.threading.spawn import spawn

from .sms_block import Recipient, TwilioCreds


class Speak(RESTHandler):

    def __init__(self, endpoint, blk):
        super().__init__('/'+endpoint)
        self.notify = blk.notify_signals
        self.logger = blk.logger
        self.messages = blk._messages

    def on_post(self, req, rsp):
        self.logger.debug('Speak is handling POST: {}, {}'.format(req, rsp))
        params = req.get_params()
        _id = params.get('msg_id', '')
        self.logger.debug('POST params: {}'.format(params))
        phrase = twiml.Response()
        phrase.say(self.messages.get(_id, ''))
        rsp.set_body(phrase)
        self.notify([Signal(params)])


class TwilioVoice(Block):

    recipients = ListProperty(Recipient, title='Recipients', default=[])
    creds = ObjectProperty(TwilioCreds, title='Credentials')
    from_ = StringProperty(default='[[TWILIO_NUMBER]]', title='From')
    url = StringProperty(default='', title='Callback URL')
    message = Property(
        default='An empty voice message',
        title='Message')
    port = IntProperty(title='Port', default=8184)
    host = StringProperty(title='Host', default='0.0.0.0')
    endpoint = StringProperty(title='Endpoint', default='')
    version = VersionProperty("1.0.0")

    def __init__(self):
        super().__init__()
        self._client = None
        self._messages = {}
        self._server = None
        self._threads = {}

    def configure(self, context):
        super().configure(context)
        self._client = TwilioRestClient(self.creds().sid(),
                                        self.creds().token())
        self.logger.debug('Configuring web server on {}:{}'.format(
            self.host(), self.port()))
        config = {}
        Speak.before_handler = self._no_auth
        self._server = WebEngine.add_server(self.port(), self.host(), config)
        self._server.add_handler(Speak(self.endpoint(), self))

    def start(self):
        super().start()
        self.logger.debug('Starting web server')
        self._server.start(None)

    def stop(self):
        for rcp in self._threads:
            self._threads[rcp].join()
        self.logger.debug('Stopping web server')
        self._server.stop()
        super().stop()

    def process_signals(self, signals):
        for s in signals:
            self._place_calls(s)

    def _place_calls(self, signal):
        try:
            msg = self.message(signal)
            msg_id = uuid4().hex
            self._messages[msg_id] = msg
            for rcp in self.recipients():
                self._threads[rcp] = spawn(target=self._call,
                                           recipient=rcp,
                                           message_id=msg_id)
        except Exception as e:
            self.logger.error(
                "Message evaluation failed: {0}: {1}".format(
                    type(e).__name__, str(e))
            )

    def _call(self, recipient, message_id, retry=False):
        try:
            # Twilio sends back some useless XML. Don't care.
            to = recipient.number(),
            from_ = self.from_(),
            url = "%s?msg_id=%s" % (self.url(), message_id)
            self.logger.debug("Making call to {}, from {}, with callback url"
                              " {}".format(to, from_, url))
            self._client.calls.create(
                to=to,
                from_=from_,
                url=url
            )
        except TwilioRestException as e:
            self.logger.error("Status %d" % e.status)
            if not retry:
                self.logger.debug("Retrying failed request")
                self._call(recipient, message_id, True)
            else:
                self.logger.error("Retry request failed")
        except Exception as e:
            self.logger.error("Error sending voice {}: {}".format(
                recipient, e
            ))

    def _no_auth(self, request, response):
        """ Override before_handler so that authentication is not required """
        return

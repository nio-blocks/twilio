from unittest.mock import patch, MagicMock
from ..voice_block import TwilioVoice, TwilioRestException
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.common.signal.base import Signal
from nio.modules.threading import Event
from time import sleep


class AVoiceBlock(TwilioVoice):

    def __init__(self, e):
        super().__init__()
        self._e = e

    def _call(self, recipient, message_id, retry=False):
        super()._call(recipient, message_id, retry)
        self._e.set()


class TestVoice(NIOBlockTestCase):

    def _create_server(self, cfg, e):
        blk = AVoiceBlock(e)
        blk.configure_server = MagicMock()
        blk.start_server = MagicMock()
        blk.stop_server = MagicMock()
        self.configure_block(blk, cfg)
        blk._client.calls.create = MagicMock()
        return blk

    def test_voice(self):
        e = Event()
        signals = [Signal()]
        cfg = { 'recipients': [ {'name': 'Snoopy', 'number': '5558675309'} ] }
        blk = self._create_server(cfg, e)
        blk.start()
        blk.process_signals(signals)
        e.wait(1)
        self.assertEqual(1, blk._client.calls.create.call_count)
        blk.stop()

    def test_voice_retry(self):
        e = Event()
        signals = [Signal()]
        cfg = { 'recipients': [ {'name': 'Snoopy', 'number': '5558675309'} ] }
        blk = self._create_server(cfg, e)
        blk._client.calls.create.side_effect = TwilioRestException(
            status=400,
            uri='bad'
        )
        blk.start()
        blk.process_signals(signals)
        e.wait(1)
        self.assertEqual(2, blk._client.calls.create.call_count)
        blk.stop()

from unittest.mock import MagicMock
from threading import Event

from nio.testing.block_test_case import NIOBlockTestCase
from nio.util.discovery import not_discoverable
from nio import Signal

from ..voice_block import TwilioVoice, TwilioRestException


@not_discoverable
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
        cfg = {'recipients': [{'name': 'Snoopy', 'number': '5558675309'}]}
        blk = self._create_server(cfg, e)
        blk.start()
        blk.process_signals(signals)
        e.wait(1)
        self.assertEqual(1, blk._client.calls.create.call_count)
        blk.stop()

    def test_voice_retry(self):
        e = Event()
        signals = [Signal()]
        cfg = {'recipients': [{'name': 'Snoopy', 'number': '5558675309'}]}
        blk = self._create_server(cfg, e)
        blk._client.calls.create.side_effect = TwilioRestException(
            status=400,
            uri='bad'
        )
        blk.logger.debug = MagicMock()
        blk.logger.error = MagicMock()
        blk.start()
        blk.process_signals(signals)
        e.wait(1)
        self.assertEqual(2, blk._client.calls.create.call_count)
        blk.logger.debug.mock_calls[1].assert_called_with(
            'Retrying failed request'
        )
        blk.logger.error.assert_called_with('Retry request failed')
        blk.stop()

    def test_voice_call_error(self):
        e = Event()
        signals = [Signal()]
        rcp_name = 'Snoopy'
        rcp_number = '5558675309'
        error_msg = 'uh oh'
        cfg = {'recipients': [{'name': rcp_name, 'number': rcp_number}]}
        blk = self._create_server(cfg, e)
        blk._client.calls.create.side_effect = Exception(error_msg)
        blk.logger.error = MagicMock()
        blk.start()
        blk.process_signals(signals)
        e.wait(1)
        self.assertEqual(1, blk._client.calls.create.call_count)
        blk.logger.error.assert_called_with(
            'Error sending voice name: {}, number: {}: {}'.format(
                rcp_name, rcp_number, error_msg)
        )
        blk.stop()

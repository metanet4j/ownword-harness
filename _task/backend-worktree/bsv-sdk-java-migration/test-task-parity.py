#!/usr/bin/env python3
"""核验固定 AuthFetch 支付失败日志的字段级比较边界。"""
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('task_parity', Path(__file__).with_name('task-parity.py'))
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)


def entry(timestamp, message='payment attempt 1 failed', stack=None):
    fields = {
        'attempt': {'type': 'number', 'value': '1'},
        'timestamp': {'type': 'string', 'value': timestamp},
        'message': {'type': 'string', 'value': message},
        'stack': {'type': 'string', 'value': stack or f'Error: {message}\n  at call'},
    }
    return {'actual': {'type': 'map', 'value': fields}}


class PaymentErrorEntryTest(unittest.TestCase):
    def test_dynamic_timestamp_and_stack_keep_stable_fields(self):
        first = entry('2026-09-26T13:57:45.381Z')
        second = entry('2026-09-26T14:05:03.002Z', stack='Error: payment attempt 1 failed\n  at Java')
        self.assertEqual(parity.payment_error_entry(first), parity.payment_error_entry(second))
        self.assertNotEqual(parity.payment_error_entry(first),
                            parity.payment_error_entry(entry('2026-09-26T14:05:03.002Z', 'different')))

    def test_malformed_dynamic_field_is_rejected(self):
        with self.assertRaises(ValueError):
            parity.payment_error_entry(entry('not-a-timestamp'))
        with self.assertRaises(ValueError):
            parity.payment_error_entry(entry('2026-09-26T13:57:45.381Z', stack='unrelated\n  at call'))


if __name__ == '__main__':
    unittest.main()

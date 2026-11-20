import unittest
from src.monitor import extract_lines, digest, additions, embed_for

class MonitorTests(unittest.TestCase):
    def test_extract_removes_nav(self):
        html = '<main id="main"><nav><p>Ignore navigation item forever</p></nav><h1>Azure Virtual Desktop update</h1>' + ''.join(f'<p>Detailed update number {i} with meaningful information.</p>' for i in range(7)) + '</main>'
        lines = extract_lines(html)
        self.assertEqual(len(lines), 8)
        self.assertFalse(any('navigation' in l for l in lines))

    def test_changes(self):
        old = ['first relevant paragraph', 'second relevant paragraph']
        new = ['first relevant paragraph', 'new Azure feature paragraph']
        plus, minus = additions(old, new)
        self.assertEqual(plus, ['new Azure feature paragraph'])
        self.assertEqual(minus, ['second relevant paragraph'])
        self.assertNotEqual(digest(old), digest(new))
        payload = embed_for({'name': 'Test docs', 'category': 'AVD', 'url': 'https://learn.microsoft.com/en-us/azure/virtual-desktop/whats-new'}, old, new)
        self.assertEqual(len(payload['fields']), 2)

if __name__ == '__main__':
    unittest.main()

import unittest
from src.monitor import extract_lines, digest, additions, embed_for, canonical_lines

class MonitorTests(unittest.TestCase):
    def test_extract_removes_nav(self):
        html = '<main id="main"><nav><p>Ignore navigation item forever</p></nav><h1>Azure Virtual Desktop update</h1>' + ''.join(f'<p>Detailed update number {i} with meaningful information.</p>' for i in range(7)) + '</main>'
        lines = extract_lines(html)
        self.assertEqual(len(lines), 8)
        self.assertFalse(any('navigation' in l for l in lines))

    def test_ignores_feedback_ui_and_whitespace(self):
        old = ["Azure Virtual Desktop provides session hosts.", "Was this page helpful?"]
        new = ["  Azure   Virtual Desktop provides session hosts. ", "Thank you for your feedback"]
        self.assertEqual(digest(old), digest(new))
        self.assertEqual(additions(old, new), ([], []))

    def test_preserves_actual_technical_changes(self):
        old = ["The platform supports session host configuration."]
        new = ["The platform supports session host configuration with new policy controls."]
        self.assertNotEqual(digest(old), digest(new))
        added, removed = additions(old, new)
        self.assertTrue(added)
        self.assertTrue(removed)

    def test_extract_removes_feedback_container(self):
        html = '<main id="main"><div class="page-feedback"><p>Was this page helpful?</p></div>' + ''.join(f'<p>Azure platform configuration detail number {i}.</p>' for i in range(6)) + '</main>'
        lines = extract_lines(html)
        self.assertEqual(len(lines), 6)
        self.assertFalse(any("helpful" in line.lower() for line in lines))

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

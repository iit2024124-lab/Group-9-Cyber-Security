import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import authenticate

class LoginTests(unittest.TestCase):
    def test_correct_alex(self):
        self.assertEqual(authenticate('alex', 'Maison!26')['user']['email'], 'alex@example.com')
    def test_correct_taylor(self):
        self.assertEqual(authenticate('taylor', 'CozyHome!26')['user']['name'], 'Taylor Reed')
    def test_wrong_password(self):
        self.assertFalse(authenticate('alex', 'alex123')['ok'])
    def test_unknown_user(self):
        self.assertFalse(authenticate('nobody', 'alex123')['ok'])
    def test_empty_credentials(self):
        self.assertFalse(authenticate('', '')['ok'])
    def test_malformed_quote(self):
        self.assertFalse(authenticate("'", 'x')['ok'])
    def test_exact_bypass(self):
        self.assertEqual(authenticate("alex' -- ", 'alex123')['ok'], False)
    def test_tautology_bypass(self):
        self.assertEqual(authenticate("' OR 1=1 -- ", 'alex123')['ok'], False)

if __name__ == '__main__':
    unittest.main()

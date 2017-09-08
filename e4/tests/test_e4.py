import os
import e4
import unittest
import tempfile

class E4TestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, e4.app.config['DATABASE'] = tempfile.mkstemp()
        e4.app.testing = True
        self.app = e4.app.test_client()
        with e4.app.app_context():
            e4.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(e4.app.config['DATABASE'])

    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
            ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('admin', 'NieniarcEgHiacHeulijkikej')
        assert b'You were logged in' in rv.data
        rv = self.logout()
        assert b'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert b'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert b'Invalid password' in rv.data

if __name__ == '__main__':
    unittest.main()
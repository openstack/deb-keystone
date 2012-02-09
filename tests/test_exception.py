# vim: tabstop=4 shiftwidth=4 softtabstop=4
import uuid
import json

from keystone.common import wsgi
from keystone import exception
from keystone import test


class ExceptionTestCase(test.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def assertValidJsonRendering(self, e):
        resp = wsgi.render_exception(e)
        self.assertEqual(resp.status_int, e.code)
        self.assertEqual(resp.status, '%s %s' % (e.code, e.title))

        j = json.loads(resp.body)
        self.assertIsNotNone(j.get('error'))
        self.assertIsNotNone(j['error'].get('code'))
        self.assertIsNotNone(j['error'].get('title'))
        self.assertIsNotNone(j['error'].get('message'))
        self.assertNotIn('\n', j['error']['message'])
        self.assertNotIn('  ', j['error']['message'])
        self.assertTrue(type(j['error']['code']) is int)

    def test_validation_error(self):
        target = uuid.uuid4().hex
        attribute = uuid.uuid4().hex
        e = exception.ValidationError(target=target, attribute=attribute)
        self.assertValidJsonRendering(e)
        self.assertIn(target, str(e))
        self.assertIn(attribute, str(e))

    def test_unauthorized(self):
        e = exception.Unauthorized()
        self.assertValidJsonRendering(e)

    def test_forbidden(self):
        action = uuid.uuid4().hex
        e = exception.Forbidden(action=action)
        self.assertValidJsonRendering(e)
        self.assertIn(action, str(e))

    def test_not_found(self):
        target = uuid.uuid4().hex
        e = exception.NotFound(target=target)
        self.assertValidJsonRendering(e)
        self.assertIn(target, str(e))

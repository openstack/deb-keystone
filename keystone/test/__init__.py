import os
import sys
import subprocess
import tempfile
import time
import unittest2 as unittest

from functional.common import HttpTestCase


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
TEST_CERT = os.path.join(BASE_DIR, 'examples/ssl/certs/middleware-key.pem')


def execute(cmd, raise_error=True):
    """
    Executes a command in a subprocess. Returns a tuple
    of (exitcode, out, err), where out is the string output
    from stdout and err is the string output from stderr when
    executing the command.

    :param cmd: Command string to execute
    :param raise_error: If returncode is not 0 (success), then
                        raise a RuntimeError? Default: True)
    """

    env = os.environ.copy()
    # Make sure that we use the programs in the
    # current source directory's bin/ directory.
    env['PATH'] = os.path.join(BASE_DIR, 'bin') + ':' + env['PATH']
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env)
    result = process.communicate()
    (out, err) = result
    exitcode = process.returncode
    if process.returncode != 0 and raise_error:
        msg = "Command %(cmd)s did not succeed. Returned an exit "\
              "code of %(exitcode)d."\
              "\n\nSTDOUT: %(out)s"\
              "\n\nSTDERR: %(err)s" % locals()
        raise RuntimeError(msg)
    return exitcode, out, err


class KeystoneTest(object):
    """Primary test class for invoking keystone tests. Controls
    initialization of environment with temporary configuration files,
    starts keystone admin and service API WSIG servers, and then uses
    :py:mod:`unittest2` to discover and iterate over existing tests.

    :py:class:`keystone.test.KeystoneTest` is expected to be
    subclassed and invoked in ``run_tests.py`` where subclasses define
    a config_name (that matches a template existing in
    ``keystone/test/etc``) and test_files (that are cleared at the
    end of test execution from the temporary space used to run these
    tests).
    """
    CONF_PARAMS = {'test_dir': TEST_DIR, 'base_dir': BASE_DIR}
    isSsl = False

    def clear_database(self):
        """Remove any test databases or files generated by previous tests."""
        for fname in self.test_files:
            fpath = os.path.join(TEST_DIR, fname)
            if os.path.exists(fpath):
                print "Removing test file %s" % fname
                os.unlink(fpath)

    def construct_temp_conf_file(self):
        """Populates a configuration template, and writes to a file pointer."""
        template_fpath = os.path.join(TEST_DIR, 'etc', self.config_name)
        conf_contents = open(template_fpath).read()
        conf_contents = conf_contents % self.CONF_PARAMS
        self.conf_fp = tempfile.NamedTemporaryFile()
        self.conf_fp.write(conf_contents)
        self.conf_fp.flush()

    def setUp(self):
        self.clear_database()
        self.construct_temp_conf_file()

        # Set client certificate for test client
        if (self.isSsl == True):
            os.environ['cert_file'] = TEST_CERT

        # run the keystone server
        print "Starting the keystone server..."
        self.server = subprocess.Popen(
            [os.path.join(BASE_DIR, 'bin/keystone'), '-c', self.conf_fp.name])

        # blatant hack.
        time.sleep(5)
        if self.server.poll() is not None:
            raise RuntimeError('Failed to start server')

    def tearDown(self):
        # kill the keystone server
        print "Stopping the keystone server..."
        self.server.kill()
        self.clear_database()

    def run(self):
        try:
            self.setUp()

            # discover and run tests
            print "Running tests..."
            if '--with-progress' in sys.argv:
                loader = unittest.TestLoader()
                suite = loader.discover(TEST_DIR, top_level_dir=BASE_DIR)
                result = unittest.TextTestRunner(verbosity=1).run(suite)
                if not result.wasSuccessful():
                    raise RuntimeError("%s unresolved issues." %
                        (len(result.errors) + len(result.failures),))
            elif '--with-coverage' in sys.argv:
                print "running coverage"
                execute('coverage run %s discover -t %s -s %s' %
                        ('/usr/bin/unit2', BASE_DIR, TEST_DIR))
            else:
                execute('unit2 discover -f -t %s -s %s' % (BASE_DIR, TEST_DIR))
        finally:
            self.tearDown()

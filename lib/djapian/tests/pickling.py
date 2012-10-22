import cPickle as pickle

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry

class PicklingTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(PicklingTest, self).setUp()

        self.result = Entry.indexer.search("text").prefetch()
        self.data = pickle.dumps({'result': self.result}, pickle.HIGHEST_PROTOCOL)

    def test_result_hits(self):
        self.assertEqual(
            [r.__dict__ for r in self.result],
            [r.__dict__ for r in pickle.loads(self.data)['result']]
        )

    def test_result_instances(self):
        self.assertEqual(
            list([r.instance for r in self.result]),
            list([r.instance for r in pickle.loads(self.data)['result']])
        )

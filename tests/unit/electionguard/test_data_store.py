from tests.base_test_case import BaseTestCase

from electionguard.data_store import DataStore, ReadOnlyDataStore


class TestReadOnlyDataStore(BaseTestCase):
    """Read-only data store tests"""

    def setUp(self):
        super().setUp()
        self.store: DataStore[str, int] = DataStore()
        self.store.set("a", 1)
        self.subject = ReadOnlyDataStore(self.store)

    def test_behaves_as_mapping(self):
        self.assertEqual(dict(self.subject), {"a": 1})
        self.assertEqual(list(self.subject.keys()), ["a"])
        self.assertEqual(list(self.subject.items()), [("a", 1)])
        self.assertIn("a", self.subject)
        self.assertNotIn("missing", self.subject)

    def test_missing_key(self):
        self.assertIsNone(self.subject.get("missing"))
        with self.assertRaises(KeyError):
            _ = self.subject["missing"]

    def test_equality(self):
        self.assertEqual(self.subject, ReadOnlyDataStore(self.store))

        other: DataStore[str, int] = DataStore()
        other.set("a", 2)
        self.assertNotEqual(self.subject, ReadOnlyDataStore(other))

    def test_reflects_underlying_store(self):
        self.store.set("b", 2)
        self.assertEqual(self.subject["b"], 2)
        self.assertEqual(len(self.subject), 2)

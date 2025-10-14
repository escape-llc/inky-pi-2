import unittest
from ..model.hash_manager import HashManager, HASH_KEY

class TestHashManager(unittest.TestCase):
	def setUp(self):
		self.hm = HashManager()
	def test_hash_and_check(self):
		doc1 = { "name": "Test Document", "value": 42 }
		doc2 = { "name": "Test Document", "value": 43 }
		id = "doc1"
		path = "/path/to/doc1"

		# Hash the first document
		updated, hash1 = self.hm.hash_document(id, path, doc1)
		self.assertTrue(updated, "Hash should be updated for new document")
		self.assertIsNotNone(hash1, "Hash should not be None")

		# Check the same document with correct hash
		doc1_with_hash = doc1.copy()
		doc1_with_hash[HASH_KEY] = hash1
		match, stored_hash = self.hm.check_document_hash(id, path, doc1_with_hash)
		self.assertTrue(match, "Hashes should match")
		self.assertEqual(stored_hash, hash1, "Stored hash should match original hash")

		# Check the same document with incorrect hash
		doc1_with_wrong_hash = doc1.copy()
		doc1_with_wrong_hash[HASH_KEY] = "wronghash"
		match, stored_hash = self.hm.check_document_hash(id, path, doc1_with_wrong_hash)
		self.assertFalse(match, "Hashes should not match")
		self.assertEqual(stored_hash, hash1, "Stored hash should still be original hash")

		# Hash a different document
		updated, hash2 = self.hm.hash_document(id, path, doc2)
		self.assertTrue(updated, "Hash should be updated for changed document")
		self.assertIsNotNone(hash2, "New hash should not be None")
		self.assertNotEqual(hash1, hash2, "New hash should differ from old hash")

		# Check the new document with correct hash
		doc2_with_hash = doc2.copy()
		doc2_with_hash[HASH_KEY] = hash2
		match, stored_hash = self.hm.check_document_hash(id, path, doc2_with_hash)
		self.assertTrue(match, "Hashes should match for new document")
		self.assertEqual(stored_hash, hash2, "Stored hash should match new hash")
	pass

if __name__ == "__main__":
    unittest.main()
from unittest import TestCase

from electionguard.words import get_word, get_index_from_word


class TestWord(TestCase):
    def test_get_word(self):
        # Arrange
        INDEX_MIN = 0
        INDEX_RANDOM_1 = 100
        INDEX_RANDOM_2 = 1000
        INDEX_MAX = 4095

        # Act
        word_min = get_word(INDEX_MIN)
        word_random_1 = get_word(INDEX_RANDOM_1)
        word_random_2 = get_word(INDEX_RANDOM_2)
        word_max = get_word(INDEX_MAX)
        reverse_find_of_index_random_1 = get_index_from_word(word_random_1)

        # Assert
        self.assertEqual(word_min, "aardvark")
        self.assertEqual(word_random_1, "alfalfa")
        self.assertEqual(word_random_2, "column")
        self.assertEqual(word_max, "prospect")
        self.assertEqual(INDEX_RANDOM_1, reverse_find_of_index_random_1)

    def test_get_word_when_out_of_range(self):
        # Arrange
        INDEX_BELOW_MIN = -1
        INDEX_ABOVE_MAX = 4096

        # Act
        word_past_min = get_word(INDEX_BELOW_MIN)
        word_past_max = get_word(INDEX_ABOVE_MAX)

        # Assert
        self.assertIsNone(word_past_min)
        self.assertIsNone(word_past_max)

    def test_get_index_of_word_not_in_list(self):
        # Arrange
        FAILING_WORD = "thiswordshouldfail"

        # Act
        failed_index = get_index_from_word(FAILING_WORD)

        # Assert
        self.assertIsNone(failed_index)

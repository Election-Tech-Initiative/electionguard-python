from unittest import TestCase

from electionguard.schema import get_election_description_schema, validate_json_schema
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()


class TestSchema(TestCase):
    """Test cases for schema"""

    def test_election_description_schema(self):
        """Test schema validation for election description"""

        # Arrange
        simple_election = (
            election_factory.get_simple_election_from_file().to_json_object()
        )
        hamilton_election = (
            election_factory.get_hamilton_election_from_file().to_json_object()
        )

        # Act
        election_description_schema = get_election_description_schema()
        simple_election_validates = validate_json_schema(
            simple_election, election_description_schema
        )
        hamilton_election_validates = validate_json_schema(
            hamilton_election, election_description_schema
        )

        # Assert
        self.assertIsNotNone(election_description_schema)
        self.assertTrue(simple_election_validates)
        self.assertTrue(hamilton_election_validates)

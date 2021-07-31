from unittest import TestCase

from electionguard.schema import get_election_description_schema, validate_json_schema
import electionguardtools.factories.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()


class TestSchema(TestCase):
    """Test cases for schema"""

    def test_election_description_schema(self):
        """Test schema validation for election description"""

        # Arrange
        simple_manifest = (
            election_factory.get_simple_manifest_from_file().to_json_object()
        )
        hamilton_manifest = (
            election_factory.get_hamilton_manifest_from_file().to_json_object()
        )

        # Act
        election_description_schema = get_election_description_schema()
        simple_manifest_validates = validate_json_schema(
            simple_manifest, election_description_schema
        )
        hamilton_manifest_validates = validate_json_schema(
            hamilton_manifest, election_description_schema
        )

        # Assert
        self.assertIsNotNone(election_description_schema)
        self.assertTrue(simple_manifest_validates)
        self.assertTrue(hamilton_manifest_validates)

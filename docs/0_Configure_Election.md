# Election Configuration

An election in ElectionGuard is defined as a set of metadata and cryptographic artifacts necessary to encrypt, conduct, tally, decrypt, and verify an election.  The Data format used for election metadata is based on the [NIST Election Common Standard Data Specification](https://www.nist.gov/itl/voting/interoperability) but includes some modifications to support the end-to-end cryptography of ElectionGuard.

Election metadata is described in a specific format parseable into an `ElectionDescription` and it's validity is checked to ensure that it is of an appropriate structure to conduct an End-to-End Verified ElectionGuard Election.  ElectionGuard only verifies the components of the election metadata that are necessary to encrypt and decrypt the election.  Some components of the election metadata are not checked for structural validity, but are used when generating a hash representation of the `Election Description`.

From an `ElectionDescription` we derive an `InternalElectionDescription` that includes a subset of the elements from the `ElectionDescription` required to verify ballots are correct.  Additionally a `CiphertextElectionContext` is created during the [Key Ceremony](/1_Key_Ceremony.md) that includes the cryptographic artifacts necessary for encrypting ballots.

## Glossary

- **Election Manifest** The election metadata in json format that is parsed into an Election Description
- **Election Description** The election metadata that describes the structure and type of the election, including geopolitical units, contests, candidates, and ballot styles, etc.
- **Internal Election Description** The subset of the `ElectionDescription` required by ElectionGuard to validate ballots are correctly associated with an election.  This component mutates the state of the Election Description.
- **Ciphertext Election Context** The cryptographic context of an election that is configured during the `Key Ceremony`
- **Description Hash** a Hash representation of the original ElectionDescription.

## Process

1. Define an election according to the `ElectionDescription` requirements.  
2. Use the [NIST Common Standard Data Specification](https://www.nist.gov/itl/voting/interoperability) as a guide, but note the differences in [election.py](https://github.com/microsoft/electionguard-python/tree/main/src/electionguard.election.py) and the provided [sample manifest](https://github.com/microsoft/electionguard-python/tree/main/data/election_manifest_simple.json).
3. Parse the `ElectionDescription` into the application.
4. Define the encryption parameters necessary for conducting an election (see `Key Ceremony`).
5. Create the Pubic Key either from a single secret, or from the Key Ceremony.
6. Build the `InternalElectionDescription` and `CiphertextElectionContext` from the `ElectionDescription` and `ElGamalKeyPair.public_key`.

## Usage Example

```python

import os
from electionguard.election import ElectionDescription, InternalElectionDescription, CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret

# Open an election manifest file
with open(os.path.join(some_path, "election-manifest.json"), "r") as manifest:
        string_representation = manifest.read()
        election_description = ElectionDescription.from_json(string_representation)

# Create an election builder instance, and configure it for a single public-private keypair.
# in a real election, you would configure this for a group of guardians.  See Key Ceremony for more information.
builder = ElectionBuilder(
    number_of_guardians=1,     # since we will generate a single public-private keypair, we set this to 1
    quorum=1,                  # since we will generate a single public-private keypair, we set this to 1
    description=election_description
)

# Generate an ElGamal Keypair from a secret.  In a real election you would use the Key Ceremony instead.
some_secret_value: int = 12345
keypair: ElGamalKeyPair = elgamal_keypair_from_secret(some_secret_value)

builder.set_public_key(keypair.public_key)

# get an `InternalElectionDescription` and `CiphertextElectionContext`
# that are used for the remainder of the election.
(internal_metadata, context) = builder.build()

```
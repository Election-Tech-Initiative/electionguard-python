# Publish and Verify

## Publish

Publishing the election artifacts helps ensure third parties can verify the election. Refer to the specification on the specific details. Below is a breakdown of the objects within the repository. These are files that should be published at the close of the election so others can verify the election.

**Election Artifacts**

```py
manifest: Manifest                        # Manifest
constants: ElectionConstants              # Constants
context: CiphertextElectionContext        # Encryption context
devices: List[EncryptionDevice]           # Encryption devices
guardian_records: List[GuardianRecord]    # Record of public guardian information
submitted_ballots: List[SubmittedBallot]  # Encrypted submitted ballots
challenge_ballots: List[PlaintextTally]   # Decrypted challenge ballots
ciphertext_tally: CiphertextTally         # Encrypted tally
plaintext_tally: PlaintextTally           # Decrypted tally
```

These classes have been defined as `dataclass` to ensure that `asdict` can be used. This ensures ease of serialization to dictionaries within python, but allows customization for those wishing to use custom serialization. `electionguard_tools` includes `export.py` which can be used as an example.

## Verify

The election artifacts provide a means to begin validation. Start with deserializing the election artifacts to their original classes.

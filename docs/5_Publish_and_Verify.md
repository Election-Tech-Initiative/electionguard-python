# Publish and Verify

## Publish

Publishing the election artifacts helps ensure third parties can verify the election. Refer the specification on the specific details. Below is a breakdown of the objects within the repository. These are files that should be published at the close of the election so others can verify the election.

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

## Verify

The election artifacts provide a means to begin validation. Start with deserializing the election artifacts to their original classes.

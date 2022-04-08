# Key Ceremony

The ElectionGuard Key Ceremony is the process used by Election Officials to share encryption keys for an election.  Before an election, a fixed number of Guardians are selection to hold the private keys needed to decrypt the election results.  A Quorum count of Guardians can also be specified to compensate for guardians who may be missing at the time of Decryption.  For instance, 5 Guardians may be selected to hold the keys, but only 3 of them are required to decrypt the election results.

Guardians are typically Election Officials, Trustees Canvass Board Members, Government Officials or other trusted authorities who are responsible and accountable for conducting the election.

## Summary

The Key Ceremony is broken into several high-level steps.  Each Guardian must _announce_ their _attendance_ in the key ceremony by publishing a _public key_ from a _key pair_ they generate. Each guardian then shares a provable _key share_ which is mathematically verified using Non-Interactive Zero Knowledge Proofs. After verification of these key shares, an _election key_ is created to encrypt ballots in the election.

### Attendance
Guardians exchange all public keys and ensure each fellow guardian has received their public key ensuring at all guardians are in attendance.

### Key Sharing
Guardians generate a key share for each guardian and shares with that designated guardian. Then each designated guardian sends a verification back to the sender. The sender then publishes to the group when all verifications are received. 

### Election Key
The final step is to publish the election key after all keys and key shares have been distributed. 

## Glossary

- **Guardian** A guardian of the election who holds the ability to partially decrypt the election results
- **Key Ceremony Mediator** A mediator to mediate communication (if needed) of information such as keys between the guardians
- **Guardian Key Pair:** Pair of keys (public & secret) used to encrypt/decrypt election
- **Guardian Key Share:** A point on a secret polynomial and commitments to verify this point for a designated guardian.
- **Election Polynomial:** The election polynomial is the mathematical expression that each Guardian defines to solve for his or her private key. A different point associated with the polynomial is distributed to each of the other guardians so that the guardians can come together to derive the polynomial function and solve for the private key.
- **Election Key:** Combined public key from public keys of each guardian
- **Quorum:** Quantity of guardians (k) that is required to decrypt the election and is less than the total number of guardians available (n)

## Process

This is a detailed description of the entire Key Ceremony Process

1. The ceremony details are decided upon. These include a `number_of_guardians` and `quorum` of guardians required for decryption.
2. Each guardian creates a unique `id` and `sequence_order`.
3. Each guardian must generate their `guardian key pair` _(ElGamal key pair)_. This will generate a corresponding Schnorr `proof` and `polynomial` used for generating `key share` for sharing.
4. Each guardian must give the other guardians their `public key` directly or through a mediator.
5. Each guardian must check if all `public keys` are received.
6. Each guardian must generate `key share` for each other guardian. The guardian will use their `polynomial` and the designated guardian's `sequence_order` to create the value. 
7. Each guardian must send each encrypted `key share` to the designated guardian directly or through a `mediator`.
8. Each guardian checks if all encrypted `key share` have been received by their recipient guardian directly or through a mediator.
9. Each recipient guardian decrypts each received encrypted `key share`
10. Each recipient guardian verifies each `key share` and sends confirmation of verification
    - If the proof verifies, continue
    - If the proof fails
      1. Sender guardian publishes the `key share` value sent to recipient as a `key share challenge` to all the other guardians
      2. Alternate guardian (outside sender or original recipient) attempts to verify key share
         - If the proof verifies, continue
         - If the proof fails again, the accused (sender guardian) should be evicted and process should be restarted with new guardian.
11. On receipt of all verifications of `key share` by all guardians, generate and publish `election key` from guardian public keys.

## Files

- [`key_ceremony.py`](https://github.com/microsoft/electionguard-python/tree/main/src/electionguard/key_ceremony.py)
- [`guardian.py`](https://github.com/microsoft/electionguard-python/tree/main/src/electionguard/guardian.py)
- [`key_ceremony_mediator.py`](https://github.com/microsoft/electionguard-python/tree/main/src/electionguard/key_ceremony_mediator.py)

## Usage Example

This example demonstrates a convenience method to generate guardians for an election

```python

NUMBER_OF_GUARDIANS: int
QUORUM: int

details: CeremonyDetails
guardians: List[Guardian]

# Setup Guardians
for i in range(NUMBER_OF_GUARDIANS):
  guardians.append(
    Guardian(f"some_guardian_id_{str(i)}", i, NUMBER_OF_GUARDIANS, QUORUM)
  )

mediator = KeyCeremonyMediator(details)

# Attendance (Public Key Share)
for guardian in guardians:
  mediator.announce(guardian)

# Orchestation (Private Key Share)
orchestrated = mediator.orchestrate()

# Verify (Prove the guardians acted in good faith)
verified = mediator.verify()

# Publish the Joint Public Key
joint_public_key = mediator.publish_election_key()

```

## Implementation Considerations

ElectionGuard can be run without the key ceremony.  The key ceremony is the recommended process to generate keys for live end-to-end verifiable elections, however this process may not be necessary for other use cases such as privacy preserving risk limiting audits.

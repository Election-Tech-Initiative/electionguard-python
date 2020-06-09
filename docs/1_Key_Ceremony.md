# Key Ceremony

## Summary

### Attendance
Guardians exchange all public keys and ensure each fellow gaurdian has received an election and auxiliary public key ensuring at all guardians are in attendance.

### Key Sharing
Guardians generate a partial key backup for each guardian and share with that designated key with that guardian. Then each designated guardian sends a verification back to the sender. The sender then publishes to the group when all verifications are received. 

### Joint Key
The final step is to publish the joint election key after all keys and backups have been shared. 

## Glossary

- **Guardian** A guardian of the election who holds the ability to decrypt the election results
- **Key Ceremony Mediator** A mediator to mediate communication (if needed) of information such as keys between the guardians
- **Election Key Pair:** Pair of keys (public & secret) used to encrypt/decrypt election
- **Auxiliary Key Pair:** Pair of keys (public & secret) used to encrypt/decrypt information sent between guardians
- **Election Partial Key Backup:** A point on a secret polynomial and commitments to verify this point for a designated guardian.
- **Election Polynomial:** The election polynomial is the mathematical expression that each Guardian defines to solve for his or her private key. A different point associated with the polynomial is shared with each of the other guardians so that the guardians can come together to derive the polynomial function and solve for the private key.
- **Joint Key:** Combined public key from election public keys of each guardian
- **Quorum:** Quantity of guardians (k) that is required to decrypt the election and is less than the total number of guardians available (n)

## Process

1. The ceremony details are decided upon. These include a `number_of_guardians` and `quorum` of guardians required for decryption.
2. Each guardian creates a unique `id` and `sequence_order`.
3. Each guardian must generate their `auxiliary key pair`.
4. Each guardian must give the other guardians their `auxiliary public key` directly or through a mediator.
5. Each guardian must check if all `auxiliary public keys` are received.
6. Each guardian must generate their `election key pair` _(ElGamal key pair)_. This will generate a corresponding Schnorr `proof` and `polynomial` used for generating `election partial key backups` for sharing.
7. Each guardian must give the other guardians their `election public key` directly or through a mediator.
8. Each guardian must check if all `election public keys` are received.
9. Each guardian must generate `election partial key backup` for each other guardian. The guardian will use their `polynomial` and the designated guardian's `sequence_order` to create the value. The backup will be encrypted with the designated guardian's `auxiliary public key`
10. Each guardian must send each encrypted `election partial key backup` to the designated guardian directly or through a `mediator`.
11. Each guardian checks if all encrypted `election partial key backups` have been received by their recipient guardian directly or through a mediator.
12. Each recipient guardian decrypts each received encrypted `election partial key backup` with their own `auxiliary private key`
13. Each recipient guardian verifies each `election partial key backup` and sends confirmation of verification
    - If the proof verifies, continue
    - If the proof fails
      1. Sender guardian publishes the `election partial key backup` value sent to recipient as a `election partial key challenge` where the value is **unencrypted** to all the other guardians \*
      2. Alternate guardian (outside sender or original recipient) attempts to verify key
         - If the proof verifies, continue
         - If the proof fails again, the accused (sender guardian) should be evicted and process should be restarted with new guardian.
14. On receipt of all verifications of `election partial private keys` by all guardians, generate and publish `joint key` from election public keys

\* **Note:** _The confidentiality of this value is now gone, but since the two Guardians are in the dispute, at least one is misbehaving and could be revealing this data._

## Files

- [`key_ceremony.py`](src/electionguard/key_ceremony.py)
- [`guardian.py`](src/electionguard/guardian.py)
- [`key_ceremony_mediator.py`](src/electionguard/key_ceremony_mediator.py)

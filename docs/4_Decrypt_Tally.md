# Decryption

At the conclusion of voting, all of the cast ballots are published in their encrypted form in the election record together with the proofs that the ballots are well-formed.  Additionally, all of the encryptions of each option are homomorphically-combined to form an encryption of the total number of times that each option was selected.  The homomorphically-combined encryptions are decrypted to generate the election tally.  Individual cast ballots are not decrypted.  Individual spoiled ballots are decrypted and the plaintext values are published along with the encrypted representations and the proofs.

In order to decrypt the homomorphically-combined encryption of each selection, each `Guardian` participating in the decryption must compute a specific `Decryption Share` of the decryption.

It is preferable that all guardians be present for decryption, however in the event that guardians cannot be present, Electionguard includes a mechanism to decrypt with the `Quorum of Guardians`.

During the [Key Ceremony](1_Key_Ceremony.md) a `Quorum of Guardians` is defined that represents the minimum number of guardians that must be present to decrypt the election.  If the decryption is to proceed with a `Quorum of Guardians` greater than or equal to the `Quorum` count, but less than the total number of guardians, then a subset of the `Available Guardians` must also each construct a `Partial Decryption Share` for the missing `Missing Guardian`, in addition to providing their own `Decryption Share`.

It is important to note that mathematically not every present guardian has to compute a `Partial Decryption Share` for every `Missing Guardian`.  Only the `Quorum Count` of guardians are necessary to construct `Partial Decryption Shares` in order to compensate for any Missing Guardian.  

In this implementation, we take an approach that utilizes all Available Guardians to compensate for Missing Guardians.  When it is determined that guardians are missing, all available guardians each calculate a `Partial Decryption Share` for the missing guardian and publish the result.  A `Quorum of Guardians` count of available `Partial Decryption Shares` is randomly selected from the pool of available partial decryption shares for a given` Missing Guardian`.  If more than one guardian is missing, we randomly choose to ignore the `Partial Decryption Share` provided by one of the Available Guardians whose partial decryption share was chosen for the previous Missing Guardian, and randomly select again from the pool of available Partial Decryption Shares.  This ensures that all available guardians have the opportunity to participate in compensating for Missing Guardians.

## Glossary
- **Guardian** A guardian of the election who holds the ability to partially decrypt the election results
- **Decryption Share** A guardian's partial share of a decryption
- **Encrypted Tally** The homomorphically-combined and encrypted representation of all selections made for each option on every contest in the election.  See [Ballot Box]() for more information.
- **Key Ceremony** The process conducted at the beginning of the election to create the joint encryption context for encrypting ballots during the election.  See [Key Ceremony](1_Key_Ceremony.md) for more information.
- **Quorum of Guardians** The minimum count (_threshold_) of guardians that must be present in order to successfully decrypt the election results.
- **Available Guardian** A guardian that has announced as _present_ for the decryption phase
- **Missing Guardian** A guardian who was configured during the `Key Ceremony` but who is not present for the decryption of the election results.
- **Compensated Decryption Share** - a partial decryption share value computed by an available guardian to compensate for a missing guardian so that the missing guardian's share can be generated and the election results can be successfully decrypted.
- **Decryption Mediator** - A component or actor responsible for composing each guardian's partial decryptions or compensated decryptions into the plaintext tally

## Process

1. Each `Guardian` that will participate in the decryption process computes a `Decryption Share` of the _Ciphertext Tally_.
2. Each `Guardian` also computes a Chaum-Pedersen proof of correctness of their `Decryption Share`.

### Decryption when All Guardians are Present

3. If all guardians are present, the Decryption Shares are combined to generate a tally for each option on every contest

### Decryption when some Guardians are Missing 

_warning: The functionality described in this segment is still a 🚧 Work In Progress_

When one or more of the Guardians are missing, any subset of the Guardians that are present can use the information they have about the other guardian's private keys to reconstruct the partial decryption shares for the missing guardians.

4. Each `Available Guardian` computes a `Partial Decryption Share` for each `Missing Guardian`
5. at least a `Quorum` count of `Partial Decryption Shares` are chosen from the values generated in the previous step for a specific `Missing guardian`
6. Each chosen `Available Guardian` uses its `Partial Decryption Share` to compute a share of the missing partial decryption.
7. the process is re-run until all Missing Guardians are compensated for.
8. The `Compensated Decryption Shares` are combined to _reconstruct_ the missing `TallyDecryptionShare`
9. finally, all of the `DecryptionShares` are combined to generate a tally for each option on every contest

## Challenged/Spoiled Ballots

If a ballot is not to be included in the vote count, it is considered challenged, or [Spoiled](https://en.wikipedia.org/wiki/Spoilt_vote).  Every ballot spoiled in an election is individually verifiably decrypted in exactly the same way that the aggregate ballot of tallies is decrypted.  Since spoiled ballots are not included as part of the vote count, they are included in the Election Record with their plaintext values included along with the encrypted representations.

Spoiling ballots is an important part of the ElectionGuard process as it allows voters to explicitly generate challenge ballots that are verifiable as part of the Election Record.

## Usage Example

Here is a simple example of how to execute the decryption process.

```python

internal_manifest: InternalManifest       # Load the election manifest
context: CiphertextElectionContext          # Load the election encryption context
encrypted_Tally: CiphertextTally            # Provide a tally from the previous step
          
available_guardians: List[Guardian]         # Provite the list of guardians who will participate
missing_guardians: List[str]                # Provide a list of guardians who will not participate

mediator = DecryptionMediator(internal_manifest, context, encrypted_tally)

# Loop through the available guardians and annouce their presence
for guardian in available_guardians:
    if (mediator.announce(guardian) is None):
        break

# loop through the missing guardians and compensate for them
for guardian in missing_guardians:
    if (mediator.compensate(guardian) is None):
        break

# Generate the plaintext tally
plaintext_tally = mediator.get_plaintext_tally()

# The plaintext tally automatically includes the election tally and the spoiled ballots
contest_tallies = plaintext_tally.contests
spoiled_ballots = plaintext_tally.spoiled_ballots

```

## Implementation Considerations

In certain use cases where the `Key Ceremony` is not used, ballots and tallies can be decrypted directly using the secret key of the election.  See the [Tally Tests](https://github.com/microsoft/electionguard-python/tree/main/tests/test_tally.md) for an example of how to decrypt the tally using the secret key.

# Cast and Spoil Ballots

Each ballot that is completed by a voter must be either cast or spoiled.  A cast ballot is a ballot that the voter accepts as valid and wishes to include in the official election tally.  A spoiled ballot, also referred to as a challenged ballot, is a ballot that the voter does not accept as valid and wishes to exclude from the official election tally.

ElectionGuard includes a mechanism to mark a specific ballot as either cast or spoiled.  Cast ballots are included in the tally record, while spoiled ballots are not.  Spoiled ballots are decrypted into plaintext and published along with the rest of the election record.

## Jurisdictional Differences

Depending on the jurisdiction conducting an election the process of casting and spoiling ballots may be handled differently. For this reason, there are multiple ways to interact with the `BallotBox` and `Tally`.

- By calling [accept_ballot](###-Function-Example) - Ballots can be marked cast or spoiled manually.
- By using the [Ballot Box](###-Class-Example) - Ballots can be marked cast or spoiled using a stateful class.

### Unknown Ballots

In some jurisdictions, there is a limit on the number of ballots that may be marked as spoiled.  If this is the case, you may use the `BallotBoxState.UNKNOWN` state, or extend the enumeration to support your specific use case.

## Encrypted Tally

Once all of the ballots are marked as _cast_ or _spoiled_, all of the encryptions of each option are homomorphically combined to form an encryption of the total number of times that each option was selected in the election.  

> This process is completed only for cast ballot.

> The spoiled ballots are simply marked for inclusion in the election results.

## Glossary

- **Ciphertext Ballot** An encrypted representation of a voter's filled-in ballot.
- **Submitted Ballot** A wrapper around the `CiphertextBallot` that represents a ballot that is submitted for inclusion in election results and is either: cast or spoiled.
- **Ballot Box** A stateful collection of ballots that are either cast or spoiled.
- **Ballot Store** A repository for retaining cast and spoiled ballots.
- **Cast Ballot** A ballot which a voter has accepted as valid to be included in the official election tally.
- **Spoiled Ballot** A ballot which a voter did not accept as valid and is not included in the tally.
- **Unknown Ballot** A ballot which may not yet be determined as cast or spoiled, or that may have been spoiled but is otherwise not published in the election results.
- **Homomorphic Tally** An encrypted representation of every selection on every ballot that was cast.  This representation is stored in a `CiphertextTally` object.

## Process

1. Each ballot is loaded into memory (if it is not already).
2. Each ballot is verified to be correct according to the specific election metadata and encryption context.
3. Each ballot is `submitted` and identified as either being `cast` or `spoiled`.
4. The collection of cast and spoiled ballots is cached in the `DataStore`.
5. All ballots are tallied.  The `cast` ballots are combined to create a `CiphertextTally` The spoiled ballots are cached for decryption later.

## Ballot Box

The ballot box can be interacted with via a stateful class that caches the election context, or via stateless functions.  The following examples demonstrate some ways to interact with the ballot box.

Depending on the specific election workflow, the `BallotBox`class  may not be used for a given election.  For instance, in one case a ballot can be **submitted** directly on an electronic device, in which case there is no `BallotBox`.  In a different workflow, a ballot may be explicitly cast or spoiled in a later step, such as after printing for voter review.

In all cases, a ballot must be marked as either `cast` or `spoiled` to be included in a tally result.

### Class Example

```python

from electionguard.ballot_box import BallotBox

internal_manifest: InternalManifest
encryption: CiphertextElection
store: DataStore
ballots_to_cast: List[CiphertextBallot]
ballots_to_spoil: List[CiphertextBallot]

# The Ballot Box is a thin wrapper around the `accept_ballot` function method
ballot_box = BallotBox(internal_manifest, encryption, store)

# Cast the ballots
for ballot in ballots_to_cast:
    submitted_ballot = ballot_box.cast(ballot)
    # The ballot is both returned, and placed into the ballot store
    assert(store.get(submitted_ballot.object_id) == submitted_ballot)

# Spoil the ballots
for ballot in ballots_to_spoil:
    assert(ballot_box.spoil(ballot) is not None)

```

### Function Example

``` python

from electionguard.ballot_box import accept_ballot

internal_manifest: InternalManifest
encryption: CiphertextElection
store: DataStore
ballots_to_cast: List[CiphertextBallot]
ballots_to_spoil: List[CiphertextBallot]

for ballot in ballots_to_cast:
    submitted_ballot = accept_ballot(
        ballot, BallotBoxState.CAST, internal_manifest, encryption, store
    )

for ballot in ballots_to_spoil:
    submitted_ballot = accept_ballot(
        ballot, BallotBoxState.SPOILED, internal_manifest, encryption, store
    )

```

## Tally

Generating the encrypted `CiphertextTally` can be completed by creating a `CiphertextTally` stateful class and manually marshalling each cast and spoiled ballot.  Using this method is preferable when the collection of ballots is very large

For convenience, stateless functions are also provided to automatically generate the `CiphertextTally` from a `DataStore`.  This method is preferred when the collection of ballots is arbitrarily small, or when the `DataStore` is overloaded with a custom implementation.

### Using the Stateful Class

```python

internal_manifest: InternalManifest
context: CiphertextElectionContext

ballots: List[SubmittedBallot]

tally = CiphertextTally(internal_manifest, context)

for ballot in ballots:
    assert(tally.append(ballot))

```

### Functional Method

```python

internal_manifest: InternalManifest
context: CiphertextElectionContext
store: DataStore

tally = tally_ballots(store, internal_manifest, context)
assert(tally is not None)

```

# Ballot Box

At the conclusion of voting, all of the ballot encryptions are published in the election record together with the proofs that the ballots are well formed.  Additionally, all of the encryptions of each option are homomorphically combined to form an encryption of the total number of times that each option was selected.

## Casting and Spoiling Ballots

ElectionGuard includes a mechanism to mark a specific ballot as either cast or spoiled.  Cast ballots are included in the tally record, while spoiled ballots are not.  Spoiled ballots are decrypted into plaintext and published along with the rest of the election record.

## Jurisdictional Differences

Depending on the jurisdiction conducting an election the process of casting and spoiling ballots may be handled differently. For this reason, there are multiple ways to interact with the `BallotBox` and `Tally`.

### Unknown Ballots

In some jurisdictions, there is a limit on the number of ballots that may be marked spoiled.  If this is the case, use the `BallotBoxState.UNKNOWN` state, or extend the enumeration to support your specific use case.

## Encrypted Tally

Once all of the ballots are marked as cast or spoiled, all of the encryptions of each option are homomorphically combined to form an encryption of the total number of times that each option was selected.  

> This process is completed only for cast ballot.

> The spoiled ballots are simply marked for inclusion in the election results.

## Glossary

- **Ciphertext Ballot** An encrypted representation of a voter's filled-in ballot.
- **Ciphertext Accepted Ballot** A wrapper around the `CiphertextBallot` that represents a ballot that is accepted for inclusion in election results and is either, cast, spoiled, or in an unknown state.
- **Ballot Box** A stateful collection of ballots that are either cast or spoiled.
- **Cast Ballot** A ballot which a voter has accepted as valid.
- **Spoiled Ballot** A ballot which a voter did not accept as valid.
- **Unknown Ballot** A ballot which may not yet be determiend as cast or spoiled, or that may have been spoiled but is otherwise not counted in the election results.
- **Homomorphic Tally** An encrypted representation of every selection on every ballt that was cast.  This representation is stored in a `CiphertextTally` object.

## Process

1. Each ballot is loaded into memory (if it is not already).
2. Each ballot is verified to be correct according to the specific election metadata and encryption context.
3. Each ballot is `accepted` and identified as either being `cast` or `spoiled`.
4. The collection of cast and spoiled ballots is cached in the `BallotStore`.
5. All ballots are tallied.  The `cast` ballots are combined to create a `CiphertextTally` The spoiled ballots are cached for decryption later.

## Ballot Box

The ballot box can be interacted with via a stateful class that caches the election context, or via stateless functions.  The following examples demonstrate some ways to interact with the ballot box.

Depending on the specific election workflow, the `BallotBox`class  may not be used for a given election.  For instance, in one case a ballot can be "accepted" directly on an electionic device, in which case there is no `BallotBox`.  In a different workflow, a ballot may be explicitly cast or spoiled in a later step, such as after printing for voter review.

In all cases, a ballot must be marked as either `cast` or `spoiled` to be included in a tally result.

### Class Example

```python

from electionguard.ballot_box import BallotBox

metadata: InternalElectionDescription
encryption: CiphertextElection
store: BallotStore
ballots_to_cast: List[CiphertextBallot]
ballots_to_spoil: List[CiphertextBallot]

# The Ballot Box is a thin wrapper around the function method
ballot_box = BallotBox(metadata, encryption, store)

# Cast the ballots
for ballot in ballots_to_cast:
    accepted_ballot = ballot_box.cast(ballot)
    # The ballot is both returned, and placed into the ballot store
    assert(store.get(accepted_ballot.object_id) == accepted_ballot)

# Spoil the ballots
for ballot in ballots_to_spoil:
    assert(ballot_box.spoil(ballot) is not None)

```

### Function Example

``` python

from electionguard.ballot_box import accept_ballot

metadata: InternalElectionDescription
encryption: CiphertextElection
store: BallotStore
ballots_to_cast: List[CiphertextBallot]
ballots_to_spoil: List[CiphertextBallot]

for ballot in ballots_to_cast:
    accepted_ballot = accept_ballot(
        ballot, BallotBoxState.CAST, metadata, encryption, store
    )

for ballot in ballots_to_spoil:
    accepted_ballot = accept_ballot(
        ballot, BallotBoxState.SPOILED, metadata, encryption, store
    )

```


## BallotBoxAcceptedBallot (ballot.py)

A ballot can be marked either CAST or SPOILED.  When ballots are first associated with the ballot box, they are marked UNKNOWN.

```python

class BallotBoxState(Enum):
     CAST
     SPOILED
     UNKNOWN

class CiphertextAcceptedBallot(CiphertextBallot):
    state: BallotBoxState

```

## Tally

Generating the encrypted `CiphertextTally` can be completed by creating a `CiphertextTally` stateful class and manually marshalling each cast and spoiled ballot.  Usingthis method is preferable when the collection of ballots is very large

For convenience, stateless functions are also provided to automatically generate the `CiphertextTally` from a `BallotStore`.  This method is preferred when the collection of ballots is arbitrarily small, or when the `BallotStore` is overloaded with a csutom implementation.

### Stateful Class

```python

@dataclass
class CiphertextTally(ElectionObjectBase):
    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    # A local cache of ballots id's that have already been cast
    _cast_ballot_ids: Set[str]

    cast: Dict[str, CiphertextTallyContest]

    spoiled_ballots: Dict[str, CiphertextAcceptedBallot]

    def add_cast(self, ballot: CiphertextAcceptedBallot) -> bool:
        ...

    def add_spoiled(self, ballot: CiphertextAcceptedBallot) -> bool:
        ...

```

### Functions

```python

def tally_ballot(
    ballot: CiphertextAcceptedBallot, tally: CiphertextTally
) -> Optional[CiphertextTally]:

def tally_ballots(
    store: BallotStore,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
) -> Optional[CiphertextTally]:

```

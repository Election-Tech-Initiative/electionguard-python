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
- **Ciphertext Ballot Box Ballot** A wrapper around the `CiphertextBallot` that represents a ballot that is either, cast, spoiled, or in an unknown state.
- **Ballot Box** A stateful collection of ballots that are either cast or spoiled.
- **Cast Ballot** A ballot which a voter has accepted as valid.
- **Spoiled Ballot** A ballot which a voter did not accept as valid.
- **Unknown Ballot** A ballot which may not yet be determiend as cast or spoiled, or that may have been spoiled but is otherwise not counted in the election results.
- **Homomorphic Tally** An encrypted representation of every selection on every ballt that was cast.  This representation is stored in a `CiphertextTally` object.

## Process

1. Each ballot is loaded into memory (if it is not already).
2. each ballot is verified to be correct according to the specific election metadata and encryption context.
2. each ballot is identified as either being cast or spoiled.
3. each ballot is set to be cast or spoiled by the `BallotBox`.
4. the collection of cast and spoiled ballots is cached in the `BallotStore`.
5. 

## Ballot Box

The ballot box can be interacted with via a stateful class that caches the election context, or via stateless functions

### Stateful Class

```python

BallotStore = Dict[str, BallotBoxCiphertextBallot]

class BallotBox:

    _metadata: InternalElectionDescription
    _encryption: CiphertextElection
    _store: BallotStore

    def cast(self, ballot: CyphertextBallot) -> Optional[BallotBoxCiphertextBallot]:
        ...

    def spoil(self, ballot: CyphertextBallot) -> Optional[BallotBoxCiphertextBallot]:
        ...

```

### Stateless Functions

``` python

def cast_ballot(
    ballot: CyphertextBallot,
     metadata: InternalElectionDescription, 
     encryption_context: CiphertextElection, 
     store: BallotStore
) -> Optional[BallotBoxCiphertextBallot]:
    ...

def spoil_ballot(
    ballot: CyphertextBallot, 
    metadata: InternalElectionDescription, 
    encryption_context: CiphertextElection, 
    store: BallotStore
) -> Optional[BallotBoxCiphertextBallot]:
    ...

```

## BallotBoxCiphertextBallot (ballot.py)

A ballot can be marked either CAST or SPOILED.  When ballots are first associated with the ballot box, they are marked UNKNOWN.

```python

class BallotBoxState(Enum):
     CAST
     SPOILED
     UNKNOWN

class CiphertextBallotBoxBallot(CiphertextBallot):
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

    spoiled_ballots: Dict[str, CiphertextBallotBoxBallot]

    def add_cast(self, ballot: CiphertextBallotBoxBallot) -> bool:
        ...

    def add_spoiled(self, ballot: CiphertextBallotBoxBallot) -> bool:
        ...

```

### Stateless Functions

```python

def tally_ballot(
    ballot: CiphertextBallotBoxBallot, tally: CiphertextTally
) -> Optional[CiphertextTally]:

def tally_ballots(
    store: BallotStore,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
) -> Optional[CiphertextTally]:

```
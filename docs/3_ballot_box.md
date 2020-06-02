# Ballot Box

At the conclusion of voting, all of the ballot encryptions are published in the election record together wit hthe proofs that the ballots are well formed.  Additionally, all of the encryptions of each option are homomorphically combined to for an encryption of the total number of times that each option was selected.

## Casting and Spoiling Ballots

ElectionGuard includes a mechanism to mark a specific ballot as either cast or spoiled.  Cast ballots are included in the tally record, while spoiled ballots are not.  Spoiled ballots are decrypted into plaintext and published along with the tally record and the encrypted representation of all cast ballots.

## Jurisdictional Differences

Depending on the jurisdiction conducting an election, and the implementation of the software program that consumes the ElectionGuard SDK, the process of casting and spoiling ballots may be handled differently.  

## Glossary
**Ciphertext Ballot** An encrypted representation of a voter's filled-in ballot.
**Ballot Box** A stateful collection of ballots that are either cast or spoiled.
**Cast Ballot** A ballot which a voter has accepted as valid.
**Spoiled Ballot** A ballot which a voter did not accept as valid.


## Process

1. Each ballot is loaded into memory.
2. each ballot is verified to be correct according to the specific election.
2. each ballot is identified as either being cast or spoiled.
3. each ballot is set to be cast or spoiled.
4. the collection of cast and spoiled ballots is cached.

## Ballot Box

### Stateful Class

```python

BallotStore = Dict[str, BallotBoxCiphertextBallot]

class BallotBox:

    _metadata: InternalElectionDescription
    _encryption: CiphertextElection
    _store: BallotStore


    def cast(self, ballot: CyphertextBallot) -> BallotBoxCiphertextBallot:
        cast_ballot(ballot, self._metadata, self._encryption, self._store)

    def spoil(self, ballot: CyphertextBallot) -> BallotBoxCiphertextBallot:
        spoil_ballot(ballot, self._metadata, self._encryption, self._store)




```

### Stateless Methods

``` python

def load_ballot() -> CyphertextBallot:
    pass

def load_ballots() -> List[CyphertextBallot]:
    pass

def cast_ballot(self, ballot: CyphertextBallot, metadata: InternalElectionDescription, encryption_context: CiphertextElection, store: BallotStore) -> Optional[BallotBoxCiphertextBallot]:
    pass

def spoil_ballot(self, ballot: CyphertextBallot, metadata: InternalElectionDescription, encryption_context: CiphertextElection, store: BallotStore) -> Optional[BallotBoxCiphertextBallot]:
    pass

```

## BallotBoxCiphertextBallot

```python

class BallotBoxState(Enum):
     CAST
     SPOILED

class BallotBoxCiphertextBallot(CiphertextBallot):
    state: BallotBoxState


```

## State Diagram

```mermaid

```


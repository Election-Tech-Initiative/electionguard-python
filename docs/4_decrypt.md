# Decryption

At the conclusion of voting, all of the ballot encryptions are published in the election record together with the proofs that the ballots are well-formed. Additionally, all of the encryptions of each option are homomorphically combined to form an encryption of the total number of times that each option was selected.

In order to decrypt the homomorphically-combined encryption of each selection, each `Guardian` participating in the decryption must compute a specific `Decryption Share` of the decryption.

It is preferable that all guardians be present for decryption, however in the event that guardians cannot be present, Electionguard includes a mechanism to decrypt with the `Quorum of Guardians`.

During the `Key Ceremony` a `Quorum of Guardians` is defined that represents the minimum number of guardians that must be present to decrypt the election.  If the decryption is to proceed with a `Quorum of Guardians` greater than or equal to the `Quorum` count, but less than the total number of guardians configured during the key ceremony, then a subset of the `Present Guardians` must also each construct a `Partial Decryption Share` for the missing `Missing Guardian`, in addition to providing their own `Decryption Share`.

It is important to note that mathematically not every present guardian has to compute a `Partial Decryption Share` for every `Missing Guardian`.  Only the `Quorum Count` of guardians are necessary to construct `Partial Decryption Shares` in order to compensate for any Missing Guardian.  

In this implementation, we take an approach that utilizes all Available Guardians to compensate for Missing Guardians.  When it is determined that guardians are missing, all available guardians each calculate a `Partial Decryption Share` for the missing guardian and publish the result.  A `Quorum of Guardians` count of available `Partial Decryption Shares` is randomly selected from the pool of availalbe partial decryption shares for a given` Missing Guardian`.  If more than one guardian is missing, we randomly choose to ignore the `Partial Decryption Share` provided by one of the Available Guardians whose partial decrypotion share was chosen for the previous Missing Guardian, and randomly select again from the pool of available Partial Decryption Shares.  This ensures that all available guardians have the opportunity to participate in compensating for Missing Guardians.




## Glossary
- **Guardian** - 
- **Decryption Share** - 
- **Encrypted Tally** - The homomorphically-combined and encrypted representation of all selections made for each option on every contest in the election.  See [Ballot Box]() for more information.
- **Homomorphic Tally** -
- **Key Ceremony** - The process conducted at the beginning of the election to create the joint encryption context for encrypting ballots during the election.  See [Key Ceremony]() for more information.
- **Quorum of Guardians** - The mininimum count (threshold) of guardians that must be present in order to successfully decrypt the election results.
- **Missing Guardian** - A guardian who was configured during the `Key Ceremony` but who is not present for the decryption of the election results.
- **Partial Decryption Share** - a value computed bya present guardian to compensate for a missing guardian so that the missing guardian's share can be generated and the election results can be successfully decrypted.
- **Decryption Mediator** - 

## Process

1. Each ballot is accumulated in the Tally (TODO: move this to ballot box segment)
1. Each `Guardian` that will participate in the decryption process computes a `Decryption Share` of the `Encrypted Tally`.
3. Each `Guardian` also computes a Chaum-Pedersen proof of correctness of their `Decryption Share`.

### Decryption when All Guardians are Present

4. If all guardians are present, the Decrypion Shares are combined to generate a tally for each option on every contest

### Decryption when some Guardians are Missing

When one or more of the Guardians are missing, any subset of the Guardians that are present can use the information they have about the other guardian's prviate keys to reconstruct the partial decryption shares for the missing trustees.

4. Each `Available Guardian` computes a `Partial Decryption Share` for each `Missing Guardian`
5. a `Quorum` count of `Partial Decryption Shares` are randomly chosen from the values generated in the previous step for a specific `Missing guardian`
6. Each randomly chosen `Available Guardian` uses its `Partial Decryption Share` to compute a share of the missing partial decryption.
7. If there is more than one Missing guardian, then one of the Available Guardians randomly chosen in the previous step is excluded from the next round.
8. the process is re-run until all Missing Guardians are compensated for.

## Decryption

### Ciphertext Decryption Selection

```python

class CiphertextDecryptionSelection(ElectionObjectBase, CryptoHashCheckable):

    # The SelectionDescription hash
    description_hash: ElementModQ

    # The encrypted representation of the decryption share
    message: ElGamalCiphertext

    # M_i in the spec
    share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ConstantChaumPedersenProof

```

```python

class CiphertextPartialDecryptionSelection(ElectionObjectBase, CryptoHashCheckable):

    # The SelectionDescription hash
    description_hash: ElementModQ

    # M_i in the spec
    partial_share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ConstantChaumPedersenProof

```

### Ciphertext Decryption Contest

```python

class CiphertextDecryptionContest(ElectionObjectBase, CryptoHashCheckable):

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: List[CiphertextDecryptionSelection]

```

```python

class CiphertextPartialDecryptionContest(ElectionObjectBase, CryptoHashCheckable):

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: List[CiphertextPartialDecryptionSelection]

```

### Decryption Share

```python

class DecryptionShare:

    # The Available Guardian that this share belongs to
    guardian_id: str

    # The collection of all contests in the election
    contests: List[CiphertextDecryptionContest]

```

### Partial Decryption Share

```python

class PartialDecryptionShare:

    # The Available Guardian that this partial share belongs to
    available_guardian_id: str

    # The Missing Guardian for whom this share is calculated on behalf of
    missing_guardian_id: str

    # The collection of all contests in the election
    contests: List[CiphertextPartialDecryptionContest]

    lagrange_coefficient: ElementModQ

```

### Functions

```python

def compute_decryption_share(guardian: Guardian, tally: ElectionTally) -> Optional[DecryptionShare]:
    ...

def compute_partial_decryption_share(available_guardian: Guardian, missing_guardian_id: str, tally: ElectionTally) -> Optional[PartialDecryptionShare]:
    ...

```

### Decryption Mediator

```python

class DecryptionMediator:

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    _ciphertext_tally: CiphertextTally
    _plaintext_Tally: Optional[PlaintextTally]

    _available_guardians: Dict[str, Guardian]
    _missing_guardians: Set[str]

    # A collection of Decryption Shares for each Available Guardian
    _decryption_shares: Dict[str, List[DecryptionShare]]

    # A collection of Partial Decryption Shares for each Available Guardian
    _partial_decryption_shares: Dict[str, List[PartialDecryptionShare]]

    def __init__(
        self,
        election_metadata: InternalElectionDescription,
        encryption_context: CiphertextElectionContext,
        tally: CiphertextTally
    ):
        self._metadata = election_metadata
        self._encryption = encryption_context
        self._ciphertext_tall = tally
        
        self._plaintextTally = None
        self._available_guardians = {}
        self._missing_guardians = {}
        self._decryption_shares = {}
        self._partial_decryption_shares = {}

    def announce(guardian: Guardian) -> Optional[DecryptionShare]:
        """
        Announce that a Guardian is present.  A Decryption Share will be generated for the Guardian
        """

        # Only allow a guardian to announce once
        if _available_guardians[guardian.object_id] is not None:
            log_warning("guardian already announced")
            return None

        # Compute the Decryption Share for the guardian
        share = compute_decryption_share(guardian, self._ciphertext_tally)
        if share is None:
            return
        
        # Submit the share
        if (self.submit_decryption_share(share)):
            _available_guardians[guardian.object_id] = guardian
            return share
        else:
            log_warning(f"announce could not submit decryption share for {guardian.guardian_id}")
            return None

    # TODO: should return a Dict?
    def compensate(missing_guardian_id: str) -> Optional[List[PartialDecryptionShare]]:
        
        partial_decryptions: List[PartialDecryptionShare] = List()

        # Loop through each of the available guardians
        # and calculate a partial for the missing one
        for guardian in self._available_guardians:
            partial = compute_partial_decryption_share(
                guardian, missing_guardian_id, self._ciphertext_tally
            )
            if partial is None:
                log_warning(f"compensation failed for missing: {missing_guardian_id}")
                break
            else:
                partial_decryptions.append(partial)

        # Verify we generated the correct number of partials
        if len(partial_decryptions) != len(self._available_guardians):
            log_warning(f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}")
            return None
        else:
            return partial_decryptions
        
    def get_plaintext_tally(self) -> Optional[PlaintextTally]:

        if (self._plaintext_tally is not None):
            return self._plaintext_tally

        # Make sure we have a Quorum of Guardians that have announced
        if (len(self._available_guardians) < self._metadata.quorum_guardians):
            log_warning("cannot get plaintext tally with less than quorum available guardians")
            return None

        # If all Guardians are present we can decrypt the tally
        if (len(self._available_guardians) == _metadata.num_guardians):
            return self._decrypt_tally()

        for missing in self._missing_guardians:
            partial_decryptions = compensate(missing)
            if partial_decryptions is None:
                break
            self._submit_partial_decryption_shares(partial_decryptions)

        return self._decrypt_tally()

    def _decrypt_tally(self) -> Optional[PlaintextTally]:
        ...

    def _submit_decryption_share(share: DecryptionShare) -> Bool:

        # Wipe the keys from memory
        ...

    def _submit_partial_decryption_shares(shares: List[PartialDecryptionShare]) -> Bool:
        ...

    def _submit_partial_decryption_share(share: PartialDecryptionShare) -> Bool:
        # wipe the keyshares from memory?
        ...

```

## Usage Example

```python

guardians: List[Guardian]
available_guardians: List[Guardian]
missing_guardians: List[str]

mediator = DecryptionMediator()

for guardian in available_guardians:
    if (mediator.announce(guardian) is None):
        break

for guardian in missing_guardians:
    if (mediator.compensate(guardian) is None):
        break

plaintext_tally = mediator.get_plaintext_tally()

```
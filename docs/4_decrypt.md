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

## Usage Example

Here is a simple example of how to execute the decryption process

```python

metadata: InternalElectionDescription       # Load the election metadata
context: CiphertextElectionContext          # Load the election encryption context
encrypted_Tally: CiphertextTally            # Provide a tally from the previous step
          
available_guardians: List[Guardian]         # Provite the list of guardians who will participate
missing_guardians: List[str]                # Provide a list of guardians who will not participate

mediator = DecryptionMediator(metadata, context, encrypted_tally)

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

```
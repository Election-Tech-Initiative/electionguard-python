from io import TextIOWrapper
from typing import List, Tuple
import click
from electionguard.ballot import BallotBoxState, SubmittedBallot

from electionguard.election import CiphertextElectionContext, Configuration
from electionguard.election_builder import ElectionBuilder
from electionguard.elgamal import ElGamalPublicKey
from electionguard.group import ElementModQ
from electionguard.scheduler import Scheduler
from electionguard.tally import CiphertextTally
from electionguard.utils import get_optional
from ..cli_models import BuildElectionResults, ImportBallotInputs
from ..e2e_steps import (
    DecryptStep,
    ImportBallotsInputRetrievalStep,
)


@click.command()
@click.option(
    "--guardian-count",
    prompt="Number of guardians",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
@click.option(
    "--manifest",
    prompt="Manifest file",
    help="The location of an election manifest.",
    type=click.File(),
)
@click.option(
    "--ballots-dir",
    prompt="Ballots file",
    help="The location of a file that contains plaintext ballots.",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
def import_ballots(
    guardian_count: int, quorum: int, manifest: TextIOWrapper, ballots_dir: str
) -> None:
    """
    Imports ballots
    """

    # get user inputs
    election_inputs = ImportBallotsInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, ballots_dir
    )

    # perform election
    build_election_results = _make_election_results(election_inputs)
    (ciphertext_tally, spoiled_ballots) = _create_tally(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_tally(
        ciphertext_tally,
        spoiled_ballots,
        election_inputs.guardians,
        build_election_results,
    )
    click.echo(decrypt_results.plaintext_tally)


# todo: convert into a step
def _make_election_results(election_inputs: ImportBallotInputs) -> BuildElectionResults:
    election_builder = ElectionBuilder(
        election_inputs.guardian_count,
        election_inputs.quorum,
        election_inputs.manifest,
    )
    context = _get_context()
    election_builder.set_public_key(context.elgamal_public_key)
    election_builder.set_commitment_hash(context.commitment_hash)
    build_result = election_builder.build()
    internal_manifest, context = get_optional(build_result)
    return BuildElectionResults(internal_manifest, context)


# todo: replace with read json file
def _get_context() -> CiphertextElectionContext:
    joint_public_key: ElGamalPublicKey = ElGamalPublicKey(
        "4F6A18073EECFFBBE83FB25C959F84E84CDB0976A483265FC232A7AC63D74146DDD3DA52B10D01CAFCDB578A25DC02549207AF160372B7837F4270AE8F7CB875854916B1F57FDEA6B6F94830B6258D474793FF6AF76D5E4D6709496490DCB6809C09CBF2F1924FA9F0ADDAEE2A763C0D004849E71164D7F01367CEE331EB34EAA8B05930C925B231F6D4E9013AF4DB1DB34DB17C185C5081810DDDEC91917D74F242F1287EE95091FAA95554EF9B222B64DF3B6638B203052FC3AF4B76C8F9B8E2C594C57D2D9FC8692526AF3BCADE84BD9FD56F5E343A6A39F5B0C09ACB9A980269C26F59CB3C3917F1736B85205136F06A04511BB90BD571144A26EC0A8D3546FFF2B20F7F2F23D0EBDCB1001C4FDAF79C6E350CFC2B3759DA3F2AC7931451A980531F35D56C74567A362A4F74961BAAF4952706DB4A37D4592B2F1F86232053641DB3E7C436906DF75ED15D26501980423114A4F04720FD674C441722F0E4844093597AACB18EB5C03FFFC70F7739CD00EDEDF90C042B694D25DA9B9338C8D2C081519B83BAB7146C5B27400D9D71AFDFACDE59755B21174DFE94C2449E3E77E7F0D668853F9F4AD156B33F67E844E54BA8F1B4AC76EEDDE03B31F00179D740F82B93CE39CDBF5A449AA983AF6CEA02DAB1DD1E59196B280274DA0D4D23C2449EF33E9B3A9A4BC68703A49519F341D4EAC8FC19A934AF9E47FAE8BAB1413A"
    )
    commitment_hash = ElementModQ(
        "0C099666FB5B5A5D62D2D34FBF3B5766F8FE17D56E9FEE4ACCDF2336E547D887"
    )
    manifest_hash = ElementModQ(
        "C2DB999CFEC53C050F14E776A4203BAAC1E76E1A959C7281A63C2EC110D3B87D"
    )
    crypto_base_hash = ElementModQ(
        "C2A51684F8EFEECF08F772FDA24479A93FEADEEED42BB328BFF95396FE663FA7"
    )
    crypto_extended_base_hash = ElementModQ(
        "815F0D9FF363882F12C9805FE0CCE04A8E1FE4F6A791F0EC4EFED8B99C56907F"
    )
    return CiphertextElectionContext(
        2,
        2,
        joint_public_key,
        commitment_hash,
        manifest_hash,
        crypto_base_hash,
        crypto_extended_base_hash,
        None,
        Configuration(False, 1000000),
    )


# todo: make this into a step
def _create_tally(
    election_inputs: ImportBallotInputs, build_election_results: BuildElectionResults
) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
    tally = CiphertextTally(
        "object_id",
        build_election_results.internal_manifest,
        build_election_results.context,
    )
    ballots = [(None, b) for b in election_inputs.submitted_ballots]
    with Scheduler() as scheduler:
        tally.batch_append(ballots, scheduler)

    spoiled_ballots = [
        b
        for b in election_inputs.submitted_ballots
        if b.state == BallotBoxState.SPOILED
    ]

    return (tally, spoiled_ballots)

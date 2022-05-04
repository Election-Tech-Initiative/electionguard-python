import importlib.metadata

# <AUTOGEN_INIT>
from electionguard import ballot
from electionguard import ballot_box
from electionguard import ballot_code
from electionguard import ballot_compact
from electionguard import ballot_validator
from electionguard import big_integer
from electionguard import chaum_pedersen
from electionguard import constants
from electionguard import data_store
from electionguard import decrypt_with_secrets
from electionguard import decrypt_with_shares
from electionguard import decryption
from electionguard import decryption_mediator
from electionguard import decryption_share
from electionguard import discrete_log
from electionguard import election
from electionguard import election_builder
from electionguard import election_object_base
from electionguard import election_polynomial
from electionguard import elgamal
from electionguard import encrypt
from electionguard import group
from electionguard import guardian
from electionguard import hash
from electionguard import hmac
from electionguard import key_ceremony
from electionguard import key_ceremony_mediator
from electionguard import logs
from electionguard import manifest
from electionguard import nonces
from electionguard import proof
from electionguard import scheduler
from electionguard import schnorr
from electionguard import serialize
from electionguard import singleton
from electionguard import tally
from electionguard import type
from electionguard import utils

from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    CiphertextContest,
    CiphertextSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    SubmittedBallot,
    create_ballot_hash,
    from_ciphertext_ballot,
    make_ciphertext_ballot,
    make_ciphertext_ballot_contest,
    make_ciphertext_ballot_selection,
    make_ciphertext_submitted_ballot,
)
from electionguard.ballot_box import (
    BallotBox,
    accept_ballot,
    get_ballots,
)
from electionguard.ballot_code import (
    get_ballot_code,
    get_hash_for_device,
)
from electionguard.ballot_compact import (
    CompactPlaintextBallot,
    CompactSubmittedBallot,
    NO_VOTE,
    YES_VOTE,
    compress_plaintext_ballot,
    compress_submitted_ballot,
    expand_compact_plaintext_ballot,
    expand_compact_submitted_ballot,
)
from electionguard.ballot_validator import (
    ballot_is_valid_for_election,
    ballot_is_valid_for_style,
    contest_is_valid_for_style,
    selection_is_valid_for_style,
)
from electionguard.big_integer import (
    BigInteger,
)
from electionguard.chaum_pedersen import (
    ChaumPedersenProof,
    ConstantChaumPedersenProof,
    DisjunctiveChaumPedersenProof,
    make_chaum_pedersen,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
    make_disjunctive_chaum_pedersen_one,
    make_disjunctive_chaum_pedersen_zero,
)
from electionguard.constants import (
    EXTRA_SMALL_TEST_CONSTANTS,
    ElectionConstants,
    LARGE_TEST_CONSTANTS,
    MEDIUM_TEST_CONSTANTS,
    PrimeOption,
    SMALL_TEST_CONSTANTS,
    STANDARD_CONSTANTS,
    create_constants,
    get_cofactor,
    get_constants,
    get_generator,
    get_large_prime,
    get_small_prime,
)
from electionguard.data_store import (
    DataStore,
    ReadOnlyDataStore,
)
from electionguard.decrypt_with_secrets import (
    decrypt_ballot_with_nonce,
    decrypt_ballot_with_secret,
    decrypt_contest_with_nonce,
    decrypt_contest_with_secret,
    decrypt_selection_with_nonce,
    decrypt_selection_with_secret,
)
from electionguard.decrypt_with_shares import (
    decrypt_ballot,
    decrypt_contest_with_decryption_shares,
    decrypt_selection_with_decryption_shares,
    decrypt_tally,
)
from electionguard.decryption import (
    RecoveryPublicKey,
    compensate_decrypt,
    compute_compensated_decryption_share,
    compute_compensated_decryption_share_for_ballot,
    compute_compensated_decryption_share_for_contest,
    compute_compensated_decryption_share_for_selection,
    compute_decryption_share,
    compute_decryption_share_for_ballot,
    compute_decryption_share_for_contest,
    compute_decryption_share_for_selection,
    compute_lagrange_coefficients_for_guardian,
    compute_lagrange_coefficients_for_guardians,
    compute_recovery_public_key,
    partially_decrypt,
    reconstruct_decryption_contest,
    reconstruct_decryption_share,
    reconstruct_decryption_share_for_ballot,
)
from electionguard.decryption_mediator import (
    DecryptionMediator,
)
from electionguard.decryption_share import (
    CiphertextCompensatedDecryptionContest,
    CiphertextCompensatedDecryptionSelection,
    CiphertextDecryptionContest,
    CiphertextDecryptionSelection,
    CompensatedDecryptionShare,
    DecryptionShare,
    ProofOrRecovery,
    create_ciphertext_decryption_selection,
    get_shares_for_selection,
)
from electionguard.discrete_log import (
    DiscreteLog,
    DiscreteLogCache,
    DiscreteLogExponentError,
    DiscreteLogNotFoundError,
    compute_discrete_log,
    compute_discrete_log_async,
    compute_discrete_log_cache,
    precompute_discrete_log_cache,
)
from electionguard.election import (
    CiphertextElectionContext,
    Configuration,
    make_ciphertext_election_context,
)
from electionguard.election_builder import (
    ElectionBuilder,
)
from electionguard.election_object_base import (
    ElectionObjectBase,
    OrderedObjectBase,
    list_eq,
    sequence_order_sort,
)
from electionguard.election_polynomial import (
    Coefficient,
    ElectionPolynomial,
    LagrangeCoefficientsRecord,
    PublicCommitment,
    SecretCoefficient,
    compute_lagrange_coefficient,
    compute_polynomial_coordinate,
    generate_polynomial,
    verify_polynomial_coordinate,
)
from electionguard.elgamal import (
    ElGamalCiphertext,
    ElGamalKeyPair,
    ElGamalPublicKey,
    ElGamalSecretKey,
    HashedElGamalCiphertext,
    elgamal_add,
    elgamal_combine_public_keys,
    elgamal_encrypt,
    elgamal_keypair_from_secret,
    elgamal_keypair_random,
    hashed_elgamal_encrypt,
)
from electionguard.encrypt import (
    ContestData,
    EncryptionDevice,
    EncryptionMediator,
    contest_from,
    encrypt_ballot,
    encrypt_ballot_contests,
    encrypt_contest,
    encrypt_selection,
    generate_device_uuid,
    selection_from,
)
from electionguard.group import (
    BaseElement,
    ElementModP,
    ElementModPOrQ,
    ElementModPOrQorInt,
    ElementModPorInt,
    ElementModQ,
    ElementModQorInt,
    a_minus_b_q,
    a_plus_bc_q,
    add_q,
    div_p,
    div_q,
    g_pow_p,
    hex_to_p,
    hex_to_q,
    int_to_p,
    int_to_q,
    mult_inv_p,
    mult_p,
    mult_q,
    negate_q,
    pow_p,
    pow_q,
    rand_q,
    rand_range_q,
)
from electionguard.guardian import (
    Guardian,
    GuardianRecord,
    PrivateGuardianRecord,
    get_valid_ballot_shares,
    publish_guardian_record,
)
from electionguard.hash import (
    CryptoHashCheckable,
    CryptoHashable,
    CryptoHashableAll,
    CryptoHashableT,
    hash_elems,
)
from electionguard.hmac import (
    get_hmac,
)
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionJointKey,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    combine_election_public_keys,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from electionguard.key_ceremony_mediator import (
    BackupVerificationState,
    GuardianPair,
    KeyCeremonyMediator,
)
from electionguard.logs import (
    ElectionGuardLog,
    FORMAT,
    LOG,
    get_file_handler,
    get_stream_handler,
    log_add_handler,
    log_critical,
    log_debug,
    log_error,
    log_handlers,
    log_info,
    log_remove_handler,
    log_warning,
)
from electionguard.manifest import (
    AnnotatedString,
    BallotStyle,
    Candidate,
    CandidateContestDescription,
    ContactInformation,
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    ElectionType,
    GeopoliticalUnit,
    InternalManifest,
    InternationalizedText,
    Language,
    Manifest,
    Party,
    ReferendumContestDescription,
    ReportingUnitType,
    SelectionDescription,
    SpecVersion,
    VoteVariationType,
    contest_description_with_placeholders_from,
    generate_placeholder_selection_from,
    generate_placeholder_selections_from,
)
from electionguard.nonces import (
    Nonces,
)
from electionguard.proof import (
    Proof,
    ProofUsage,
)
from electionguard.scheduler import (
    Scheduler,
)
from electionguard.schnorr import (
    SchnorrProof,
    make_schnorr_proof,
)
from electionguard.serialize import (
    PAD_INDICATOR_SIZE,
    PaddedDataSize,
    TruncationError,
    construct_path,
    from_file,
    from_file_wrapper,
    from_list_in_file,
    from_list_in_file_wrapper,
    from_raw,
    get_schema,
    padded_decode,
    padded_encode,
    to_file,
    to_raw,
)
from electionguard.singleton import (
    Singleton,
)
from electionguard.tally import (
    CiphertextTally,
    CiphertextTallyContest,
    CiphertextTallySelection,
    PlaintextTally,
    PlaintextTallyContest,
    PlaintextTallySelection,
    PublishedCiphertextTally,
    tally_ballot,
    tally_ballots,
)
from electionguard.type import (
    BallotId,
    ContestId,
    GuardianId,
    MediatorId,
    SelectionId,
    VerifierId,
)
from electionguard.utils import (
    BYTE_ENCODING,
    BYTE_ORDER,
    ContestErrorType,
    flatmap_optional,
    get_optional,
    get_or_else_optional,
    get_or_else_optional_func,
    match_optional,
    space_between_capitals,
    to_hex_bytes,
    to_iso_date_string,
    to_ticks,
)

__all__ = [
    "AnnotatedString",
    "BYTE_ENCODING",
    "BYTE_ORDER",
    "BackupVerificationState",
    "BallotBox",
    "BallotBoxState",
    "BallotId",
    "BallotStyle",
    "BaseElement",
    "BigInteger",
    "Candidate",
    "CandidateContestDescription",
    "CeremonyDetails",
    "ChaumPedersenProof",
    "CiphertextBallot",
    "CiphertextBallotContest",
    "CiphertextBallotSelection",
    "CiphertextCompensatedDecryptionContest",
    "CiphertextCompensatedDecryptionSelection",
    "CiphertextContest",
    "CiphertextDecryptionContest",
    "CiphertextDecryptionSelection",
    "CiphertextElectionContext",
    "CiphertextSelection",
    "CiphertextTally",
    "CiphertextTallyContest",
    "CiphertextTallySelection",
    "Coefficient",
    "CompactPlaintextBallot",
    "CompactSubmittedBallot",
    "CompensatedDecryptionShare",
    "Configuration",
    "ConstantChaumPedersenProof",
    "ContactInformation",
    "ContestData",
    "ContestDescription",
    "ContestDescriptionWithPlaceholders",
    "ContestErrorType",
    "ContestId",
    "CryptoHashCheckable",
    "CryptoHashable",
    "CryptoHashableAll",
    "CryptoHashableT",
    "DataStore",
    "DecryptionMediator",
    "DecryptionShare",
    "DiscreteLog",
    "DiscreteLogCache",
    "DiscreteLogExponentError",
    "DiscreteLogNotFoundError",
    "DisjunctiveChaumPedersenProof",
    "EXTRA_SMALL_TEST_CONSTANTS",
    "ElGamalCiphertext",
    "ElGamalKeyPair",
    "ElGamalPublicKey",
    "ElGamalSecretKey",
    "ElectionBuilder",
    "ElectionConstants",
    "ElectionGuardLog",
    "ElectionJointKey",
    "ElectionKeyPair",
    "ElectionObjectBase",
    "ElectionPartialKeyBackup",
    "ElectionPartialKeyChallenge",
    "ElectionPartialKeyVerification",
    "ElectionPolynomial",
    "ElectionPublicKey",
    "ElectionType",
    "ElementModP",
    "ElementModPOrQ",
    "ElementModPOrQorInt",
    "ElementModPorInt",
    "ElementModQ",
    "ElementModQorInt",
    "EncryptionDevice",
    "EncryptionMediator",
    "FORMAT",
    "GeopoliticalUnit",
    "Guardian",
    "GuardianId",
    "GuardianPair",
    "GuardianRecord",
    "HashedElGamalCiphertext",
    "InternalManifest",
    "InternationalizedText",
    "KeyCeremonyMediator",
    "LARGE_TEST_CONSTANTS",
    "LOG",
    "LagrangeCoefficientsRecord",
    "Language",
    "MEDIUM_TEST_CONSTANTS",
    "Manifest",
    "MediatorId",
    "NO_VOTE",
    "Nonces",
    "OrderedObjectBase",
    "PAD_INDICATOR_SIZE",
    "PaddedDataSize",
    "Party",
    "PlaintextBallot",
    "PlaintextBallotContest",
    "PlaintextBallotSelection",
    "PlaintextTally",
    "PlaintextTallyContest",
    "PlaintextTallySelection",
    "PrimeOption",
    "PrivateGuardianRecord",
    "Proof",
    "ProofOrRecovery",
    "ProofUsage",
    "PublicCommitment",
    "PublishedCiphertextTally",
    "ReadOnlyDataStore",
    "RecoveryPublicKey",
    "ReferendumContestDescription",
    "ReportingUnitType",
    "SMALL_TEST_CONSTANTS",
    "STANDARD_CONSTANTS",
    "Scheduler",
    "SchnorrProof",
    "SecretCoefficient",
    "SelectionDescription",
    "SelectionId",
    "Singleton",
    "SpecVersion",
    "SubmittedBallot",
    "TruncationError",
    "VerifierId",
    "VoteVariationType",
    "YES_VOTE",
    "a_minus_b_q",
    "a_plus_bc_q",
    "accept_ballot",
    "add_q",
    "ballot",
    "ballot_box",
    "ballot_code",
    "ballot_compact",
    "ballot_is_valid_for_election",
    "ballot_is_valid_for_style",
    "ballot_validator",
    "big_integer",
    "chaum_pedersen",
    "combine_election_public_keys",
    "compensate_decrypt",
    "compress_plaintext_ballot",
    "compress_submitted_ballot",
    "compute_compensated_decryption_share",
    "compute_compensated_decryption_share_for_ballot",
    "compute_compensated_decryption_share_for_contest",
    "compute_compensated_decryption_share_for_selection",
    "compute_decryption_share",
    "compute_decryption_share_for_ballot",
    "compute_decryption_share_for_contest",
    "compute_decryption_share_for_selection",
    "compute_discrete_log",
    "compute_discrete_log_async",
    "compute_discrete_log_cache",
    "compute_lagrange_coefficient",
    "compute_lagrange_coefficients_for_guardian",
    "compute_lagrange_coefficients_for_guardians",
    "compute_polynomial_coordinate",
    "compute_recovery_public_key",
    "constants",
    "construct_path",
    "contest_description_with_placeholders_from",
    "contest_from",
    "contest_is_valid_for_style",
    "create_ballot_hash",
    "create_ciphertext_decryption_selection",
    "create_constants",
    "data_store",
    "decrypt_ballot",
    "decrypt_ballot_with_nonce",
    "decrypt_ballot_with_secret",
    "decrypt_contest_with_decryption_shares",
    "decrypt_contest_with_nonce",
    "decrypt_contest_with_secret",
    "decrypt_selection_with_decryption_shares",
    "decrypt_selection_with_nonce",
    "decrypt_selection_with_secret",
    "decrypt_tally",
    "decrypt_with_secrets",
    "decrypt_with_shares",
    "decryption",
    "decryption_mediator",
    "decryption_share",
    "discrete_log",
    "div_p",
    "div_q",
    "election",
    "election_builder",
    "election_object_base",
    "election_polynomial",
    "elgamal",
    "elgamal_add",
    "elgamal_combine_public_keys",
    "elgamal_encrypt",
    "elgamal_keypair_from_secret",
    "elgamal_keypair_random",
    "encrypt",
    "encrypt_ballot",
    "encrypt_ballot_contests",
    "encrypt_contest",
    "encrypt_selection",
    "expand_compact_plaintext_ballot",
    "expand_compact_submitted_ballot",
    "flatmap_optional",
    "from_ciphertext_ballot",
    "from_file",
    "from_file_wrapper",
    "from_list_in_file",
    "from_list_in_file_wrapper",
    "from_raw",
    "g_pow_p",
    "generate_device_uuid",
    "generate_election_key_pair",
    "generate_election_partial_key_backup",
    "generate_election_partial_key_challenge",
    "generate_placeholder_selection_from",
    "generate_placeholder_selections_from",
    "generate_polynomial",
    "get_ballot_code",
    "get_ballots",
    "get_cofactor",
    "get_constants",
    "get_file_handler",
    "get_generator",
    "get_hash_for_device",
    "get_hmac",
    "get_large_prime",
    "get_optional",
    "get_or_else_optional",
    "get_or_else_optional_func",
    "get_schema",
    "get_shares_for_selection",
    "get_small_prime",
    "get_stream_handler",
    "get_valid_ballot_shares",
    "group",
    "guardian",
    "hash",
    "hash_elems",
    "hashed_elgamal_encrypt",
    "hex_to_p",
    "hex_to_q",
    "hmac",
    "int_to_p",
    "int_to_q",
    "key_ceremony",
    "key_ceremony_mediator",
    "list_eq",
    "log_add_handler",
    "log_critical",
    "log_debug",
    "log_error",
    "log_handlers",
    "log_info",
    "log_remove_handler",
    "log_warning",
    "logs",
    "make_chaum_pedersen",
    "make_ciphertext_ballot",
    "make_ciphertext_ballot_contest",
    "make_ciphertext_ballot_selection",
    "make_ciphertext_election_context",
    "make_ciphertext_submitted_ballot",
    "make_constant_chaum_pedersen",
    "make_disjunctive_chaum_pedersen",
    "make_disjunctive_chaum_pedersen_one",
    "make_disjunctive_chaum_pedersen_zero",
    "make_schnorr_proof",
    "manifest",
    "match_optional",
    "mult_inv_p",
    "mult_p",
    "mult_q",
    "negate_q",
    "nonces",
    "padded_decode",
    "padded_encode",
    "partially_decrypt",
    "pow_p",
    "pow_q",
    "precompute_discrete_log_cache",
    "proof",
    "publish_guardian_record",
    "rand_q",
    "rand_range_q",
    "reconstruct_decryption_contest",
    "reconstruct_decryption_share",
    "reconstruct_decryption_share_for_ballot",
    "scheduler",
    "schnorr",
    "selection_from",
    "selection_is_valid_for_style",
    "sequence_order_sort",
    "serialize",
    "singleton",
    "space_between_capitals",
    "tally",
    "tally_ballot",
    "tally_ballots",
    "to_file",
    "to_hex_bytes",
    "to_iso_date_string",
    "to_raw",
    "to_ticks",
    "type",
    "utils",
    "verify_election_partial_key_backup",
    "verify_election_partial_key_challenge",
    "verify_polynomial_coordinate",
]

# </AUTOGEN_INIT>

# single source version from pyproject.toml
try:
    __version__ = importlib.metadata.version(__package__.split("_", maxsplit=1)[0])
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

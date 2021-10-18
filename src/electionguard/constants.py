"""Creating and managing mathematic constants for the election."""
from dataclasses import dataclass
from enum import Enum
from os import getenv
from typing import List

# pylint: disable=no-name-in-module
from gmpy2 import xmpz

from .powradix import PowRadix, PowRadixOption


class PrimeOption(Enum):
    """Option for primes to determine election constants."""

    Standard = "Standard"
    TestOnly = "TestOnly"


@dataclass
class ElectionConstants:
    """The constants for mathematical functions during the election."""

    large_prime: int
    """large prime or p"""

    small_prime: int
    """small prime or q"""

    cofactor: int  # (p - 1) / q
    """cofactor or r"""

    generator: int
    """generator or g"""  # 2^r mod p


@dataclass
class ElectionConstantInternals:
    """
    Related values, derived from the ElectionConstants, but not meant for public consumption.
    Instead, these are meant for accelerated computation with commonly used values.
    """

    prime_option: PrimeOption
    """whether we're using test or standard primes"""

    pow_radix_option: PowRadixOption
    """how aggressively we're accelerating modular exponentiation"""

    g_xmpz: xmpz
    """generator"""

    p_xmpz: xmpz
    """large prime"""

    q_xmpz: xmpz
    """small prime"""

    r_xmpz: xmpz
    """cofactor"""

    g_powradix: PowRadix
    """acceleration structure for g_pow_p"""


def create_constants(
    large_prime: int,
    small_prime: int,
    cofactor: int,
    generator: int,
) -> ElectionConstants:
    """Create constants for election."""
    return ElectionConstants(large_prime, small_prime, cofactor, generator)


def create_constant_internals(
    constants: ElectionConstants,
    prime_option: PrimeOption,
    pow_radix_option: PowRadixOption,
) -> ElectionConstantInternals:
    """
    Creates a variety of internal constants that are used for accelerated computation.
    """
    g_xmpz = xmpz(constants.generator)
    p_xmpz = xmpz(constants.large_prime)
    q_xmpz = xmpz(constants.small_prime)

    return ElectionConstantInternals(
        prime_option=prime_option,
        pow_radix_option=pow_radix_option,
        g_xmpz=g_xmpz,
        p_xmpz=p_xmpz,
        q_xmpz=q_xmpz,
        r_xmpz=xmpz(constants.cofactor),
        g_powradix=PowRadix(
            basis=g_xmpz,
            option=pow_radix_option,
            small_prime=q_xmpz,
            large_prime=p_xmpz,
        ),
    )


# pylint: disable=line-too-long
STANDARD_CONSTANTS = create_constants(
    1044388881413152506691752710716624382579964249047383780384233483283953907971553643537729993126875883902173634017777416360502926082946377942955704498542097614841825246773580689398386320439747911160897731551074903967243883427132918813748016269754522343505285898816777211761912392772914485521155521641049273446207578961939840619466145806859275053476560973295158703823395710210329314709715239251736552384080845836048778667318931418338422443891025911884723433084701207771901944593286624979917391350564662632723703007964229849154756196890615252286533089643184902706926081744149289517418249153634178342075381874131646013444796894582106870531535803666254579602632453103741452569793905551901541856173251385047414840392753585581909950158046256810542678368121278509960520957624737942914600310646609792665012858397381435755902851312071248102599442308951327039250818892493767423329663783709190716162023529669217300939783171415808233146823000766917789286154006042281423733706462905243774854543127239500245873582012663666430583862778167369547603016344242729592244544608279405999759391099769165589722584216017468464576217318557948461765770700913220460557598574717173408252913596242281190298966500668625620138188265530628036538314433100326660047110143,
    115792089237316195423570985008687907853269984665640564039457584007913129639747,  # pow(2, 256) - 189
    9019518416950528558373478086511232658951474842525520401496114928154304263969655687927867442562559311457926593510757267649063628681241064260953609180947464800958467390949485096429653122916928704841547265126247408167856620024815508684472819746384115369148322548696439327979752948311712506113890045287907335656308945630141969472484100558565879585476547782717283106837945923693806973017510492730838409381014701258202694245760602718602550739205297257940969992371799325870179746191672464736721424617639973324090288952006260483222894269928179970153634220390287255837625331668555933039199194619824375869291271098935000699785346405055160394688637074599519052655517388596327473273906029869030988064607361165803129718773877185415445291671089029845994683414682274353665003204293107284473196033588697845087556526514092678744031772226855409523354476737660407619436531080189837076164818131039104397776628128325247709678431023369197272126578394856752060591013812807437681624251867074769638052097737959472027002770963255207757153746376691827309573603635608169799503216990026029763868313819255248026666854405409059422844776556067163611304891154793770115766608153679099327786,
    119359756198641231858139651428439585561105914902686985078252796680474637856752833978884422594516170665312423393830118608408063594508087813277769835084746883589963798527237870817233369094387978405585759195339509768803496494994109693743279157584139079471178850751266233150727771094796709619646350222242437970473900636242584673413224137139139346254912172628651028694427789523683070264102332413084663100402635889283790741342401259356660761075766365672754329863241692760862540151023800163269173550320623249398630247531924855997863109776955214403044727497968354022277828136634059011708099779241302941071701051050378539485717425482151777277387633806111112178267035315726401285294598397677116389893642725498831127977915200359151833767358091365292230363248410124916825814514852703770457024102738694375502049388804979035628232209959549199366986471874840784466132903083308458356458177839111623113116525230200791649979270165318729763550486200224695556789081331596212761936863634467236301450039399776963661755684863012396788149479256016157814129329192490798309248914535389650594573156725696657302152874510063002532052622638033113978672254680147128450265983503193865576932419282003012093526302631221491418211528781074474515924597472841036553107847,
)

# TEST ONLY
# These constants serve as sets of primes for future developers
# Currently, all the sets are all valid but may break certain tests
# As tests adapt, these constants can be used to speed up tests
EXTRA_SMALL_TEST_CONSTANTS = create_constants(157, 13, 12, 16)
SMALL_TEST_CONSTANTS = create_constants(503, 251, 2, 5)
MEDIUM_TEST_CONSTANTS = create_constants(65267, 32633, 2, 3)
LARGE_TEST_CONSTANTS = create_constants(
    18446744073704586917, 65521, 281539415968996, 15463152587872997502
)

_saved_constants: List[ElectionConstants] = []
_saved_internals: List[ElectionConstantInternals] = []


def get_constants() -> ElectionConstants:
    """Get constants for the election by the option for the primes."""

    if len(_saved_constants) == 0:
        push_new_constants_from_environment()

    return _saved_constants[-1]


get_large_prime = lambda: get_constants().large_prime
get_small_prime = lambda: get_constants().small_prime
get_cofactor = lambda: get_constants().cofactor
get_generator = lambda: get_constants().generator


def pop_constants() -> None:
    """Retires a set of constants that was previously pushed."""

    if len(_saved_constants) > 0:
        _saved_internals.pop()
        _saved_constants.pop()


def push_new_constants(
    prime_option: PrimeOption = PrimeOption.Standard,
    pow_radix_option: PowRadixOption = PowRadixOption.HIGH_MEMORY_USE,
) -> None:
    """
    Given one of the possible options for how the primes should be, pushes those primes into
    use in the system. This can be undone later on by calling pop_constants().
    """

    _saved_constants.append(
        LARGE_TEST_CONSTANTS
        if prime_option == PrimeOption.TestOnly
        else STANDARD_CONSTANTS
    )
    _saved_internals.append(
        create_constant_internals(_saved_constants[-1], prime_option, pow_radix_option)
    )


def push_new_constants_from_environment() -> None:
    """Pushes a new set of constants, based on the environment variables "PRIME_OPTION" and "POWRADIX_OPTION" if they exist."""
    prime_env = getenv("PRIME_OPTION")
    pow_radix_env = getenv("POWRADIX_OPTION")

    try:
        prime_option = (
            PrimeOption[prime_env] if prime_env is not None else PrimeOption.Standard
        )
    except KeyError:
        prime_option = PrimeOption.Standard

    try:
        pow_radix_option = (
            PowRadixOption[pow_radix_env]
            if pow_radix_env is not None
            else PowRadixOption.HIGH_MEMORY_USE
        )
    except KeyError:
        pow_radix_option = PowRadixOption.HIGH_MEMORY_USE

    push_new_constants(prime_option, pow_radix_option)


def get_internals() -> ElectionConstantInternals:
    """Get internal constants for the election."""
    if len(_saved_internals) == 0:
        push_new_constants_from_environment()

    return _saved_internals[-1]


using_test_constants = lambda: get_internals().prime_option == PrimeOption.TestOnly
get_powradix_option = lambda: get_internals().pow_radix_option
get_g_mpz = lambda: get_internals().g_xmpz
get_p_mpz = lambda: get_internals().p_xmpz
get_q_mpz = lambda: get_internals().q_xmpz
get_r_mpz = lambda: get_internals().r_xmpz
get_g_powradix = lambda: get_internals().g_powradix

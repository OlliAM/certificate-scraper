from .better_biomass import BetterBiomassStrategy
from .twobsvs import TwobsvsStrategy

STRATEGIES = {
    "https://betterbiomass.nl/": BetterBiomassStrategy,
    "https://www.2bsvs.org/certificates/valid-certificates/": TwobsvsStrategy
}

def get_strategy(name, max_concurrency=3):
    cls = STRATEGIES.get(name)
    if not cls:
        raise ValueError(f"No strategy registered for {name}")
    return cls(max_concurrency)
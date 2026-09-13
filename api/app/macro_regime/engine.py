from dataclasses import dataclass
from enum import Enum


class Regime(Enum):
    CALM = "calm"
    ELEVATED = "elevated"
    CRISIS = "crisis"


@dataclass
class MacroProxy:
    name: str
    value: float
    elevated_threshold: float
    crisis_threshold: float

    def score(self) -> Regime:
        if self.value >= self.crisis_threshold:
            return Regime.CRISIS
        if self.value >= self.elevated_threshold:
            return Regime.ELEVATED
        return Regime.CALM


@dataclass
class RegimeOverrides:
    spacing_multiplier: float
    size_multiplier: float
    trading_halted: bool


REGIME_OVERRIDES: dict[Regime, RegimeOverrides] = {
    Regime.CALM: RegimeOverrides(spacing_multiplier=1.0, size_multiplier=1.0, trading_halted=False),
    Regime.ELEVATED: RegimeOverrides(
        spacing_multiplier=1.5, size_multiplier=0.5, trading_halted=False
    ),
    Regime.CRISIS: RegimeOverrides(
        spacing_multiplier=2.0, size_multiplier=0.0, trading_halted=True
    ),
}


class MacroRegimeEngine:
    def __init__(self, proxies: list[MacroProxy]) -> None:
        self.proxies = proxies

    def current_regime(self) -> Regime:
        scores = {proxy.score() for proxy in self.proxies}
        if Regime.CRISIS in scores:
            return Regime.CRISIS
        if Regime.ELEVATED in scores:
            return Regime.ELEVATED
        return Regime.CALM

    def overrides(self) -> RegimeOverrides:
        return REGIME_OVERRIDES[self.current_regime()]

    def apply_to_grid_config(self, config) -> None:
        overrides = self.overrides()
        config.spacing_multiplier = config.spacing_multiplier * overrides.spacing_multiplier
        config.size_per_level = max(0, round(config.size_per_level * overrides.size_multiplier))

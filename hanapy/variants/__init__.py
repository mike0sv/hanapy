from typing import Dict

from hanapy.core.loop import GameVariant
from hanapy.variants.classic import ClassicGame
from hanapy.variants.smol import SmolGame

VARIANTS: Dict[str, GameVariant] = {
    "classic": ClassicGame,
    "smol2x2": SmolGame.variant(2, 2),
    "smol1x2": SmolGame.variant(1, 2),
    "smol1x1": SmolGame.variant(1, 1),
}

from typing import List, Tuple, Any, Dict, Optional, Callable, TypeAlias
from types import FunctionType

Strategy: TypeAlias = Callable[[List[bool], List[bool], int], bool | List[bool]]
from typing import List, Tuple, Any, Dict, Optional, Callable, TypeAlias

Strategy: TypeAlias = Callable[[List[bool], List[bool], int], bool]
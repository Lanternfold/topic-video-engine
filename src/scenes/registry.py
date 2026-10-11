"""Scene registry mapping scene type identifiers to their renderer implementations."""

from typing import Any, Dict, Type

from src.scenes.base import BaseScene
from src.scenes.chart_scene import ChartScene
from src.scenes.conclusion_scene import ConclusionScene
from src.scenes.stat_scene import StatScene
from src.scenes.terminal_scene import TerminalScene
from src.scenes.title_scene import TitleScene

SCENE_REGISTRY: Dict[str, Type[BaseScene]] = {
    "title": TitleScene,
    "intro": TitleScene,
    "terminal_workflow": TerminalScene,
    "terminal": TerminalScene,
    "code": TerminalScene,
    "data_chart": ChartScene,
    "chart": ChartScene,
    "stat_callout": StatScene,
    "stat": StatScene,
    "conclusion": ConclusionScene,
    "summary": ConclusionScene,
}


def get_scene_renderer(scene_type: str, profile: Dict[str, Any], width: int = 1080, height: int = 1920) -> BaseScene:
    """Retrieve and instantiate scene renderer for given type."""
    normalized = scene_type.strip().lower()
    renderer_cls = SCENE_REGISTRY.get(normalized)
    if not renderer_cls:
        available = ", ".join(sorted(SCENE_REGISTRY.keys()))
        raise ValueError(f"Unknown scene type '{scene_type}'. Available scene types: {available}")
    return renderer_cls(profile=profile, width=width, height=height)

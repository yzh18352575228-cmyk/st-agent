"""Global AnnData storage — supports single + multi-file workflows.

All tools read/write through this module.
"""

import anndata as ad

_adatas: dict[str, ad.AnnData] = {}
_primary_path: str | None = None


def add_adata(adata: ad.AnnData, path: str) -> None:
    global _primary_path
    _adatas[path] = adata
    _primary_path = path


def get_adata(path: str | None = None) -> ad.AnnData | None:
    if path:
        return _adatas.get(path)
    if _primary_path:
        return _adatas.get(_primary_path)
    return None


def get_adatas() -> dict[str, ad.AnnData]:
    return _adatas


def list_loaded() -> list[str]:
    return list(_adatas.keys())


def set_primary(path: str) -> None:
    global _primary_path
    if path in _adatas:
        _primary_path = path


def has_data() -> bool:
    return len(_adatas) > 0


def remove_adata(path: str) -> None:
    global _primary_path
    _adatas.pop(path, None)
    if _primary_path == path:
        _primary_path = next(iter(_adatas), None) if _adatas else None


def clear_all() -> None:
    global _primary_path
    _adatas.clear()
    _primary_path = None


def set_adata(adata: ad.AnnData, path: str | None = None) -> None:
    key = path or f"data_{len(_adatas)}"
    add_adata(adata, key)


def get_primary_path() -> str | None:
    return _primary_path


def cache_figure(tool_name: str, figure_path: str) -> None:
    adata = get_adata()
    if adata is None:
        return
    index = adata.uns.setdefault("figure_index", {})
    index.setdefault(tool_name, []).append(figure_path)


def get_cached_figures(tool_name: str | None = None) -> dict[str, list[str]]:
    adata = get_adata()
    if adata is None:
        return {}
    index = adata.uns.get("figure_index", {})
    if tool_name:
        return {tool_name: index.get(tool_name, [])}
    return dict(index)


def has_cached_figures(tool_name: str) -> bool:
    return bool(get_cached_figures(tool_name).get(tool_name))


def get_data_path() -> str | None:
    return _primary_path

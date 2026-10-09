import importlib

import pytest


def reload_config(monkeypatch, **env_vars):
    monkeypatch.setenv("CHUNK_SIZE", "400")
    monkeypatch.setenv("CHUNK_OVERLAP", "50")
    monkeypatch.setenv("TOP_K", "5")

    for name, value in env_vars.items():
        monkeypatch.setenv(name, str(value))

    import app.core.config as config_module
    return importlib.reload(config_module)


def test_valid_configuration_is_accepted(monkeypatch):
    config_module = reload_config(
        monkeypatch,
        CHUNK_SIZE=400,
        CHUNK_OVERLAP=50,
        TOP_K=5,
    )

    assert config_module.settings.CHUNK_SIZE == 400
    assert config_module.settings.CHUNK_OVERLAP == 50
    assert config_module.settings.TOP_K == 5


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_invalid_chunk_size_is_rejected(monkeypatch, chunk_size):
    with pytest.raises(ValueError, match="CHUNK_SIZE must be greater than 0"):
        reload_config(monkeypatch, CHUNK_SIZE=chunk_size)


@pytest.mark.parametrize("overlap", [-1, 400, 401])
def test_invalid_chunk_overlap_is_rejected(monkeypatch, overlap):
    with pytest.raises(ValueError, match="CHUNK_OVERLAP must be non-negative"):
        reload_config(
            monkeypatch,
            CHUNK_SIZE=400,
            CHUNK_OVERLAP=overlap,
        )


@pytest.mark.parametrize("top_k", [0, -1])
def test_invalid_top_k_is_rejected(monkeypatch, top_k):
    with pytest.raises(ValueError, match="TOP_K must be greater than 0"):
        reload_config(monkeypatch, TOP_K=top_k)

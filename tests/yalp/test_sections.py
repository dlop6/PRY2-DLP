import pytest
from yalp_reader import _split_sections, YAParError

FIXTURE = "tests/yalp/fixtures"


def test_separacion_correcta():
    tokens_sec, prod_sec = _split_sections("%token A\n%%\nprod: A ;")
    assert "A" in tokens_sec
    assert "prod" in prod_sec


def test_error_falta_separador(tmp_path):
    with pytest.raises(YAParError) as exc:
        _split_sections("%token TOKEN_1\nproduction1:\n    TOKEN_1\n;")
    assert str(exc.value) == "Error YAPar: falta separador %% entre tokens y producciones."


def test_error_multiples_separadores():
    with pytest.raises(YAParError) as exc:
        _split_sections("%token A\n%%\nprod: A ;\n%%\notro: A ;")
    assert str(exc.value) == "Error YAPar: se encontró más de un separador %%."


def test_secciones_vacias_permitidas():
    tokens_sec, prod_sec = _split_sections("%%")
    assert tokens_sec == ""
    assert prod_sec == ""

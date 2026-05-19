import pytest
from yalpReader import _splitSections, YAParError

FIXTURE = "tests/yalp/fixtures"


def test_separacion_correcta():
    tokensSec, prodSec = _splitSections("%token A\n%%\nprod: A ;")
    assert "A" in tokensSec
    assert "prod" in prodSec


def test_error_falta_separador(tmp_path):
    with pytest.raises(YAParError) as exc:
        _splitSections("%token TOKEN_1\nproduction1:\n    TOKEN_1\n;")
    assert str(exc.value) == "Error YAPar: falta separador %% entre tokens y producciones."


def test_error_multiples_separadores():
    with pytest.raises(YAParError) as exc:
        _splitSections("%token A\n%%\nprod: A ;\n%%\notro: A ;")
    assert str(exc.value) == "Error YAPar: se encontró más de un separador %%."


def test_secciones_vacias_permitidas():
    tokensSec, prodSec = _splitSections("%%")
    assert tokensSec == ""
    assert prodSec == ""

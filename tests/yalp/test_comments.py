import pytest
from yalpReader import _removeComments, YAParError


def test_elimina_comentario_simple():
    resultado = _removeComments("antes /* foo */ despues")
    assert "foo" not in resultado
    assert "antes" in resultado
    assert "despues" in resultado


def test_elimina_comentario_multilinea():
    texto = "inicio\n/* linea1\nlinea2\n*/\nfin"
    resultado = _removeComments(texto)
    assert "linea1" not in resultado
    assert "linea2" not in resultado
    assert "inicio" in resultado
    assert "fin" in resultado


def test_elimina_multiples_comentarios():
    texto = "/* a */ x /* b */ y"
    resultado = _removeComments(texto)
    assert "a" not in resultado
    assert "b" not in resultado
    assert "x" in resultado
    assert "y" in resultado


def test_error_comentario_sin_cerrar():
    with pytest.raises(YAParError) as exc:
        _removeComments("/* sin cerrar\n%token TOKEN_1")
    assert str(exc.value) == "Error YAPar: comentario sin cerrar."


def test_sin_comentarios_no_modifica():
    texto = "%token TOKEN_1\n%%\nprod: TOKEN_1 ;"
    assert _removeComments(texto) == texto

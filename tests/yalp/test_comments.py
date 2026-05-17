import pytest
from yalp_reader import _remove_comments, YAParError


def test_elimina_comentario_simple():
    resultado = _remove_comments("antes /* foo */ despues")
    assert "foo" not in resultado
    assert "antes" in resultado
    assert "despues" in resultado


def test_elimina_comentario_multilinea():
    texto = "inicio\n/* linea1\nlinea2\n*/\nfin"
    resultado = _remove_comments(texto)
    assert "linea1" not in resultado
    assert "linea2" not in resultado
    assert "inicio" in resultado
    assert "fin" in resultado


def test_elimina_multiples_comentarios():
    texto = "/* a */ x /* b */ y"
    resultado = _remove_comments(texto)
    assert "a" not in resultado
    assert "b" not in resultado
    assert "x" in resultado
    assert "y" in resultado


def test_error_comentario_sin_cerrar():
    with pytest.raises(YAParError) as exc:
        _remove_comments("/* sin cerrar\n%token TOKEN_1")
    assert str(exc.value) == "Error YAPar: comentario sin cerrar."


def test_sin_comentarios_no_modifica():
    texto = "%token TOKEN_1\n%%\nprod: TOKEN_1 ;"
    assert _remove_comments(texto) == texto

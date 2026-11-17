

def test_anotar_en_ideas_cierra_la_idea_de_la_spec(tmp_path):
    from bt.evaluar import anotar_en_ideas

    ruta = tmp_path / "ideas.md"
    ruta.write_text("| # | Idea | Estado |\n|---|---|---|\n| 7 | algo → otra cosa | **pre-registrada** (s-1): 4h |\n"
                    "| 8 | otra | propuesta |\n", encoding="utf-8")
    ev = {"id": "s-1", "veredicto": "RECHAZADA", "nivel": None, "fecha": "2026-11-10T06:00:00+00:00",
          "desarrollo": {"global": {"n": 100, "avgRNeto": -0.05, "ic95": [-0.1, 0.0]}}, "holdout": None}
    assert anotar_en_ideas(ev, ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "**pre-registrada** (s-1): 4h → **rechazada** (2026-11-10): desarrollo n=100 -0.050" in texto
    assert "holdout no mirado" in texto and "| 8 | otra | propuesta |" in texto
    assert not anotar_en_ideas(ev, ruta)  # ya anotada: no repite
    assert not anotar_en_ideas({**ev, "id": "otra"}, ruta)


def test_anotar_en_ideas_dice_si_pasa_el_cribado(tmp_path):
    from bt.evaluar import anotar_en_ideas

    ruta = tmp_path / "ideas.md"
    fila = "| 20 | x | **pre-registrada** (c-1): cribado |\n| 21 | y | **pre-registrada** (c-2): cribado |\n"
    ruta.write_text(fila, encoding="utf-8")
    base = {"nivel": None, "fecha": "2026-11-18T06:00:00+00:00", "holdout": None, "spec": {"solo_desarrollo": True},
            "desarrollo": {"global": {"n": 300, "avgRNeto": 0.12, "ic95": [0.05, 0.19]}}}
    motivo = "holdout no mirado (solo_desarrollo): sin holdout no hay veredicto de aprobación"
    anotar_en_ideas({**base, "id": "c-1", "veredicto": "NO_CONCLUYENTE", "motivos": [motivo]}, ruta)
    anotar_en_ideas({**base, "id": "c-2", "veredicto": "RECHAZADA", "motivos": ["desarrollo: falla «tramos»"]}, ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "→ **pasa el cribado: va a pre-registro completo**" in texto and "→ **no pasa el cribado**" in texto

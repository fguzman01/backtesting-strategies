import datetime as dt
import json

from bt import operador


def issue(n, titulo, estado, prio="P2"):
    return {"number": n, "title": titulo, "state": "OPEN", "body": "**Problema:** x <b>\n\n---\n_pie_",
            "labels": [{"name": f"estado:{estado}"}, {"name": "tipo:mejora"}, {"name": f"prio:{prio}"}],
            "html_url": f"u/{n}"}


def test_texto_issue_y_pr():
    t = operador.texto_issue(issue(45, "Motor <intrabar>", "propuesta"), "propuesta")
    assert "#45 Motor &lt;intrabar&gt;" in t and "¿Se hace?" in t and "_pie_" not in t and "&lt;b&gt;" in t
    p = operador.texto_pr({"number": 60, "title": "Algo", "body": "cuerpo", "additions": 10, "deletions": 2,
                           "changed_files": 3})
    assert "PR #60" in p and "+10 −2 en 3" in p and "¿Se fusiona?" in p


def test_cierre_solo_si_hay_algo():
    hoy = dt.date(2026, 11, 6)
    assert operador.texto_cierre([issue(1, "a", "hecha")], [], [], hoy) is None
    t = operador.texto_cierre([issue(45, "Motor", "propuesta"), issue(49, "Pedido", "aprobada")],
                              [{"number": 60, "title": "PR x"}, {"number": 61, "title": "[rutina] y"}],
                              ["PR #58 fusionado: z"], hoy)
    assert "Espera tu decisión (2)" in t and "#45 Motor" in t and "PR #60" in t and "[rutina]" not in t
    assert "Mañana se trabaja" in t and "#49" in t and "06-11" in t


def test_cli_sin_operador_no_falla(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPERADOR_URL", raising=False)
    ev = tmp_path / "ev.json"
    ev.write_text(json.dumps({"label": {"name": "estado:propuesta"}, "issue": issue(45, "Motor", "propuesta")}))
    assert operador.main(["issue", str(ev)]) == 0
    assert "no se envía" in capsys.readouterr().out
    ev.write_text(json.dumps({"label": {"name": "tipo:mejora"}, "issue": issue(45, "Motor", "propuesta")}))
    assert operador.main(["issue", str(ev)]) == 0
    assert "no pide decisión" in capsys.readouterr().out


def test_tarjeta_del_plan_muestra_el_plan():
    i = issue(51, "Algo", "diseñada")
    i["body"] = "**Problema:** largo " + "x" * 700 + "\n\n## Plan\n**Qué cambia:** esto"
    t = operador.texto_issue(i, "diseñada")
    assert "## Plan" in t and "Qué cambia" in t and "xxxx" not in t and "¿Se implementa este plan?" in t


def test_comentarios_marcados_y_recordatorios():
    i = issue(49, "Pedido", "aprobada")
    assert operador.texto_comentario(i, {"body": "sin marca"}) is None
    t = operador.texto_comentario(i, {"body": "<!-- telegram -->\nLa respuesta <b>"})
    assert "#49 Pedido" in t and "La respuesta &lt;b&gt;" in t and "telegram" not in t
    r = operador.recordatorios([issue(45, "A", "propuesta"), issue(49, "B", "aprobada"), issue(46, "C", "diseñada")],
                               [{"number": 60, "title": "PR x", "url": "u"}, {"number": 61, "title": "[rutina] y"}])
    assert [(x[0], x[2]) for x in r] == [("issue", 45), ("issue", 46), ("pr", 60)]
    assert r[0][1].startswith("🔁")


def test_salud_avisa_lo_trabado_y_no_la_cola_del_desarrollador():
    import datetime as dt

    from bt.operador import salud, texto_cierre

    ahora = dt.datetime(2026, 11, 10, 21, tzinfo=dt.UTC)
    hace = lambda d: (ahora - dt.timedelta(days=d)).isoformat()  # noqa: E731
    issues = [
        {"number": 1, "labels": [{"name": "estado:aprobada"}], "updatedAt": hace(2)},      # diseñador no lo tomó
        {"number": 2, "labels": [{"name": "estado:en-curso"}], "updatedAt": hace(9)},      # cola: no avisa
        {"number": 3, "labels": [{"name": "estado:requiere-sesion"}], "updatedAt": hace(4)},
        {"number": 4, "labels": [{"name": "estado:propuesta"}], "updatedAt": hace(1)},     # todavía a tiempo
    ]
    prs = [{"number": 9, "createdAt": hace(2)}, {"number": 10, "createdAt": hace(0)}]
    runs = [{"workflowName": "ci"}, {"workflowName": "ci"}]
    avisos = salud(issues, prs, runs, ahora)
    texto = " ".join(avisos)
    assert "#1 " in texto and "#3 " in texto and "#2 " not in texto and "#4 " not in texto
    assert "PR #9" in texto and "PR #10" not in texto and "«ci» falló 2 veces" in texto
    # Un aviso basta para mandar el cierre aunque no haya otro movimiento.
    cierre = texto_cierre([], [], [], ahora.date(), avisos)
    assert cierre and "Salud del proceso" in cierre
    assert "nada trabado" in texto_cierre([], [], ["algo"], ahora.date(), [])

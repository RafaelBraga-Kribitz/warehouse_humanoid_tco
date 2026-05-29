---
status: accepted
decision_date: 2026-05-22
superseded_by: null
linked_invariant_test: null
---

# ADR-0007: Simulation-Agent-Routing-Fehler und Behebung

**Date:** 2026-05-22
**Status:** Accepted
**Supersedes:** ADR-0006 (Fehldiagnose der Grundursache)
**Decider:** Rafael Braga

## Kontext

Modul 2 (SimPy diskrete Ereignissimulation) lieferte statistisch nicht unterscheidbare Durchsatzwerte über alle 5 Szenarien hinweg (Kruskal-Wallis p=1,0) — selbst nach dem Wechsel auf reale UnifoLM-Zykluszeit-Daten mit deutlicher Streuung (Standardabweichung=41,8 s bei einem Mittelwert von 61,4 s). ADR-0006 vermutete einen Datenartefakt als Ursache und behauptete, der Wechsel auf reale Daten habe das Problem behoben; die Validierung nach dem Datenwechsel zeigte jedoch weiterhin p=1,0.

## Untersuchung

Die Überprüfung des Quellcodes in `src/warehouse_humanoid_tco/models/simulation.py` legte offen, dass die Ursache nicht in den Daten lag, sondern in der Simulationslogik. In der Generatorfunktion `pick_order` (Zeilen 57–71) bewirkte ein vorzeitiges `return`-Statement innerhalb der `for profile in scenario.agent_profiles`-Schleife, dass die Funktion nach dem ersten nicht-leeren Agent-Profil abgebrochen wurde.

Da in allen Szenarien das erste Profil stets "human" ist, wurde jeder Auftrag dem menschlichen Personaltyp zugeteilt. Nachfolgende Profile — Humanoide und AMRs in hybriden Szenarien — wurden nie angefragt.

Zur Verifikation: Wenn die Zykluszeit der Humanoiden in einem hybriden Szenario auf 250 s gesetzt wurde (das 10-fache der menschlichen Zykluszeit), lag der Durchsatz dennoch innerhalb von ~8 % gegenüber dem Nur-Mensch-Szenario. Dies bestätigte, dass Humanoide trotz Verfügbarkeit keine Aufträge verarbeiteten.

## Entscheidung

`pick_order` wurde so umgebaut, dass eine gewichtet-zufällige Agent-Auswahl anhand der Belegschaftsgröße erfolgt:

```python
eligible = [p for p in scenario.agent_profiles if p.count > 0]
if not eligible:
    return
weights = np.array([p.count for p in eligible], dtype=float)
weights /= weights.sum()
chosen_idx = int(rng.choice(len(eligible), p=weights))
profile = eligible[chosen_idx]
# ...process order with chosen profile...
```

Ein Regressionstest `tests/test_simulation.py::test_scenarios_with_different_agent_mixes_produce_different_throughput` wurde ergänzt, um ein erneutes Auftreten des Fehlers zu verhindern.

## Konsequenzen

- Das Agent-Routing verteilt Aufträge nun korrekt auf alle verfügbaren Agent-Typen, proportional zur Belegschaftszusammensetzung.
- Der Durchsatz variiert nun szenarienübergreifend in Abhängigkeit von der Agent-Zusammensetzung.
- Kruskal-Wallis-Test nach der Behebung auf realen Daten: ~1 % Streuung der Mittelwerte über die Szenarien (p-Wert bleibt wahrscheinlich ≥0,05, jedoch aufgrund niedriger Systemauslastung — nicht aufgrund des Routing-Fehlers).
- Alle veröffentlichten Diagramme und Dashboards müssen aus der korrigierten Simulation neu erzeugt werden.
- Die Schlussfolgerung aus ADR-0006 — "bestätigt, dass reale Daten die Konvergenz auflösen" — ist unzutreffend; die tatsächliche Grundursache war die Simulationslogik, nicht die Datenqualität.

## Warum p=1,0 weiterhin auftritt

Nach der Behebung bleibt die Durchsatzstreuung gering (~948–950 Aufträge/Schicht über 5 Szenarien), weil:

1. Die Auftragseingansrate beträgt 120/Stunde (geringe Auslastung der Gesamtkapazität von ~500–1.150 Aufträgen/Stunde je nach Agent-Mix)
2. Bei niedriger Auslastung ist die Warteschlangenwirkung minimal, und alle Szenarien verarbeiten Aufträge mit der Ankunftsrate
3. Statistische Konvergenz im Durchsatz ist nach dieser Behebung **kein** Hinweis auf einen Routing-Fehler — sie zeigt, dass das System nicht stark genug ausgelastet ist, um Unterschiede sichtbar zu machen

Dies ist **erwartetes Verhalten** und keine Regression. Um aussagekräftige Durchsatzunterschiede zu beobachten, ist entweder

- die Auftragseingansrate so weit zu erhöhen, dass die Kapazitätsgrenze der Belegschaft erreicht wird, oder
- es sind Szenarien mit extremeren Mix-Unterschieden zu untersuchen (z. B. rein humanoid vs. rein menschlich bei hoher Last).

## Commit-Hash

fix(simulation): correct agent routing bug; orders now distributed across all agent profiles
test(simulation): add regression test for agent routing differentiation
fix(tco): remove misleading npv_std/ci fields; throughput doesn't scale fixed labor costs

---

**Revisionsverlauf:**

- Ursprüngliche Hypothese in ADR-0006: synthetische Zykluszeit-Verteilung verursachte Konvergenz → widerlegt
- Tatsächliche Ursache identifiziert: vorzeitiges `return` in einer einzigen Zeile von `pick_order` → behoben
- Regressionstest hinzugefügt, um Wiedereinführung des Fehlers zu verhindern
- TCO-Modell präzisiert: Durchsatz beeinflusst den Kapitalwert (NPV) im Festkosten-Personalmodell nicht (ausschlaggebend ist ausschließlich die Agent-Zusammensetzung)

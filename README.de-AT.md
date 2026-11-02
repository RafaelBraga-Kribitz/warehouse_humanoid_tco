# Total Cost of Ownership humanoider Roboter im Lager

[🇧🇷 PT-BR](README.pt-BR.md) · [🇬🇧 EN-UK](README.md) · [🇦🇹 DE-AT](README.de-AT.md)

## Überblick

Dieses Projekt vergleicht sieben Lagerteams über fünf Jahre und unterstützt eine Investitionsentscheidung zwischen Beschäftigten, humanoiden Robotern und autonomen mobilen Robotern (AMR). Die Gesamtbetriebskosten (Total Cost of Ownership, TCO) umfassen Anschaffung, abgezinste Betriebskosten und Restwert.

Im modellierten Szenario kostet das schlanke Team aus **einer Arbeitskraft und drei AMR** €452.706 als Barwert. Drei Arbeitskräfte kosten €647.401. Die modellierte Ersparnis gegenüber diesem Vergleich beträgt €194.695. Das überbesetzte Referenzteam mit acht Arbeitskräften kostet €1.726.403. Kein Team mit humanoiden Robotern liegt unter dieser Referenz.

Die aktuelle Empfehlung lautet, den Kauf humanoider Roboter aufzuschieben: Bei der modellierten Nachfrage ist die schlanke Kombination aus Arbeitskraft und AMR günstiger, selbst bei getesteten Humanoidpreisen zwischen €10.000 und €500.000. In 99,8 % von 10.000 Monte-Carlo-Simulationen war diese Kombination am günstigsten.

## Wesentliche Grenzen

Dies ist ein modellierter Vergleich und kein Beschaffungsvorschlag für einen konkreten Standort. Der Geschwindigkeitsfaktor für Humanoide stammt aus Haushaltstätigkeiten, nicht aus Lageraufgaben. Öffentliche Preise, geschätzte österreichische Kollektivvertragslöhne, Verfügbarkeit und Integrationskosten beruhen ebenfalls auf Annahmen. Ein durch Kundendaten bestätigter Business Case liegt nicht vor.

## Weiterlesen und ausführen

Das [vollständige README auf Englisch](README.md) enthält alle sieben Teams, Diagramme, Daten, Annahmen, Governance und Ausführungsanleitung. Das Projekt benötigt Python 3.11 oder neuer. Die gesamte Pipeline startet mit `make all`. Das interaktive Dashboard ist auf [Tableau Public](https://public.tableau.com/app/profile/rafael.braga.kribitz/viz/HumanoidRoboticsTCO/Dashboard1) verfügbar.

[Repository](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco) · [Einschränkungen](governance/LIMITATIONS.md) · [Wirtschaftliche Bewertung](docs/economic-evaluation.md)

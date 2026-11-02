# Custo total de propriedade de robôs humanoides em armazéns

[🇧🇷 PT-BR](README.pt-BR.md) · [🇬🇧 EN-UK](README.md) · [🇦🇹 DE-AT](README.de-AT.md)

## Resumo

Este projeto compara sete configurações de equipes de armazém ao longo de cinco anos para apoiar uma decisão de investimento: trabalhadores, robôs humanoides e robôs móveis autônomos (AMRs). O custo total de propriedade (TCO) inclui investimento inicial, custos operacionais descontados e valor residual.

No cenário modelado, a equipe enxuta de **1 trabalhador + 3 AMRs** custa €452.706 em valor presente, contra €647.401 para três trabalhadores. O modelo estima economia de €194.695 frente a essa comparação. A equipe de referência superdimensionada de oito trabalhadores custa €1.726.403. Nenhuma equipe com humanoides fica abaixo dessa referência.

A recomendação atual é adiar a compra de humanoides: no nível de demanda modelado, a combinação enxuta de trabalhador e AMRs é mais barata, inclusive quando o modelo testa preços de humanoides de €10.000 a €500.000. A combinação enxuta foi a mais barata em 99,8% de 10.000 simulações de Monte Carlo.

## Limites essenciais

Este é um comparativo modelado, não uma proposta de compra para um local específico. O fator de velocidade dos humanoides é transferido de tarefas domésticas, não de tarefas de armazém. Preços públicos, salários estimados segundo convenções coletivas austríacas, disponibilidade e custos de integração também dependem de hipóteses. A recomendação não é um caso de negócio validado por cliente.

## Explorar e reproduzir

O [README completo em inglês](README.md) contém as sete equipes, gráficos, dados, hipóteses, governança e instruções de execução. O projeto utiliza Python 3.11 ou superior. Para executar toda a pipeline: `make all`. A demonstração interativa está no [Tableau Public](https://public.tableau.com/app/profile/rafael.braga.kribitz/viz/HumanoidRoboticsTCO/Dashboard1).

[Repositório](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco) · [Limitações](governance/LIMITATIONS.md) · [Avaliação econômica](docs/economic-evaluation.md)

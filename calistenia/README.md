# Treinador de Calistenia

Programa progressivo de 12 semanas para calistenia, com embasamento científico, e um app
que roda em qualquer navegador (celular, computador ou TV) sem instalar nada.

- **PLANO.md**: o programa completo, os princípios, a técnica de cada movimento e as referências.
- **index.html** + **dados.js**: o app. Abra o `index.html` no navegador e pronto. Funciona offline.

## O que o app faz

1. **Teste inicial** (5 medidas) e posiciona você automaticamente no nível certo de cada
   uma das 12 cadeias de progressão.
2. Monta o **treino do dia** (A ou B alternados, 3 por semana) com séries, faixa de repetições
   e RIR alvo que mudam conforme o bloco da semana (base, força, força e habilidade, deloads).
3. Em cada exercício mostra: variação atual, **mapa corporal com os músculos** principais e
   auxiliares, execução passo a passo, erros comuns e o sinal de sobrecarga que pede regressão.
4. **Cronômetro de descanso** grande com apito, pensado para a TV.
5. Registra repetições e RIR de cada série e aplica a **dupla progressão** sozinho: duas
   sessões no topo da faixa com RIR na meta sobe de nível; duas abaixo do fundo desce.
6. Check-in de **dor** no início de cada treino com regressão ou pausa automática da região.
7. **Alerta de carga semanal** quando a semana atual passa de 1,3x a média das 4 anteriores.
8. Histórico completo, biblioteca de exercícios, exportação e importação de backup.

## Como usar na TV

Opção simples: abra o `index.html` no celular ou notebook e espelhe a tela (Chromecast,
AirPlay, Miracast ou cabo HDMI). Os atalhos de teclado funcionam com teclado Bluetooth
ou com um controle remoto que emule teclado:

| Tecla | Ação |
|---|---|
| Espaço ou Enter | concluir série, pular descanso, avançar fase |
| Seta para a direita | próximo exercício |
| Setas cima/baixo | ajustar repetições no registro |
| 0 a 4 | marcar o RIR no registro |
| Esc | cancelar ou sair |

Opção publicada: ative o GitHub Pages neste repositório (Settings, Pages, branch `main`,
pasta raiz) e abra o endereço gerado direto no navegador da TV.

## Dados

Tudo fica no `localStorage` do navegador em que você usa. Em **Ajustes** há exportação e
importação de backup em JSON para trocar de aparelho.

## Editar o programa

Os exercícios, cadeias, dicas, faixas, blocos e regras de posicionamento estão em
`dados.js`, em texto simples. O código do app em `index.html` não precisa ser tocado
para mudar o programa.

## Roteiro

- [x] Plano de 12 semanas com referências
- [x] App para TV com progressão automática, mapa corporal e cronômetro
- [ ] Demonstrações visuais por exercício (animação 3D ou vídeo real licenciado; IA gerada quando a qualidade compensar)
- [ ] Câmera com estimativa de pose: contagem de repetições e alerta de amplitude
- [ ] Treinador com IA que ajusta o plano pelo histórico, fadiga e dor

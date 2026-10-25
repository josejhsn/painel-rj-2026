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

## Como usar na TV LG (webOS)

A TV LG roda webOS. Há três caminhos, do mais simples ao mais completo.

**1. Navegador da TV (recomendado para começar)**

1. Publique o app no GitHub Pages: no repositório, Settings, Pages, branch `main`, pasta raiz.
   Pages gratuito exige repositório público; o app não guarda nenhum dado seu no repositório,
   só no navegador da TV.
2. Na TV, abra o app **Navegador** (Web Browser), digite o endereço gerado e adicione aos favoritos.
3. Use o controle Magic Remote como mouse: aponte e aperte OK nos botões. Os botões são grandes
   de propósito. As setas do controle também movem o foco entre botões.
4. Faça o teste inicial uma vez. Os dados ficam no navegador da TV. Não limpe os dados de
   navegação sem antes exportar um backup em Ajustes.

**2. Espelhar o celular**

Abra o `index.html` ou o endereço do Pages no celular e espelhe na TV (Screen Share ou AirPlay
nas LG recentes). O cronômetro e o mapa corporal aparecem na TV; você registra as séries no celular.

**3. Instalar como app na TV (ícone na tela inicial, funciona offline)**

A pasta já tem o `appinfo.json`, `icon.png` e `largeIcon.png` que o webOS exige.

1. Na TV, instale o app **Developer Mode** da LG Content Store, entre com uma conta LG Developer
   (gratuita em webostv.developer.lge.com) e ligue Dev Mode e Key Server.
2. No computador, instale o Node.js e a CLI da LG: `npm install -g @webos-tools/cli`.
3. Empacote, conecte e instale:

```
ares-package calistenia/
ares-setup-device            # cadastre a TV com o IP e a passphrase que o Developer Mode mostra
ares-install --device tv com.josejhsn.calistenia_1.0.0_all.ipk
ares-launch --device tv com.josejhsn.calistenia
```

O Developer Mode expira em 50 horas de uso e precisa ser renovado no app da TV; o app instalado
continua lá. Para ficar permanente sem renovação é preciso publicar na LG Content Store.

Teclas do controle dentro do app instalado: OK aciona o botão focado, setas movem o foco,
Voltar fecha o overlay aberto.

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
- [x] Pacote webOS (LG) pronto para instalar via Developer Mode
- [ ] Demonstrações visuais por exercício (animação 3D ou vídeo real licenciado; IA gerada quando a qualidade compensar)
- [ ] Câmera com estimativa de pose: contagem de repetições e alerta de amplitude
- [ ] Treinador com IA que ajusta o plano pelo histórico, fadiga e dor

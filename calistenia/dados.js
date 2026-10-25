/* Dados do programa: cadeias de progressao, tecnica, musculos, sessoes e regras.
   Fonte: PLANO.md (mesma pasta). Editar aqui muda o app sem tocar no codigo. */
window.DADOS = {
  musculos: {
    peitoral:      { nome: "Peitoral maior",        lado: "frente" },
    deltoide_ant:  { nome: "Deltoide anterior",     lado: "frente" },
    deltoide_med:  { nome: "Deltoide medial",       lado: "frente" },
    deltoide_post: { nome: "Deltoide posterior",    lado: "costas" },
    triceps:       { nome: "Triceps braquial",      lado: "costas" },
    biceps:        { nome: "Biceps e braquial",     lado: "frente" },
    antebraco:     { nome: "Antebraco (preensao)",  lado: "frente" },
    serratil:      { nome: "Serratil anterior",     lado: "frente" },
    abdomen:       { nome: "Reto abdominal",        lado: "frente" },
    obliquos:      { nome: "Obliquos",              lado: "frente" },
    flexores_quadril: { nome: "Flexores de quadril", lado: "frente" },
    quadriceps:    { nome: "Quadriceps",            lado: "frente" },
    adutores:      { nome: "Adutores",              lado: "frente" },
    panturrilha:   { nome: "Panturrilha",           lado: "costas" },
    dorsal:        { nome: "Latissimo do dorso",    lado: "costas" },
    trapezio:      { nome: "Trapezio e romboides",  lado: "costas" },
    trapezio_sup:  { nome: "Trapezio superior",     lado: "costas" },
    lombar:        { nome: "Eretores da espinha",   lado: "costas" },
    gluteo:        { nome: "Gluteo maximo e medio", lado: "costas" },
    posterior:     { nome: "Posterior de coxa",     lado: "costas" }
  },

  /* Cada cadeia: id, nome, tipo ("reps" ou "tempo"), descanso em segundos,
     faixa padrao e faixa de forca (Bloco 3), e niveis em ordem de dificuldade.
     Em cada nivel: nome, musculos (principais primeiro), dicas, erros, alerta
     (sinal de sobrecarga que pede regressao), e faixas opcionais que sobrepoem
     as da cadeia. */
  cadeias: {
    push_h: {
      nome: "Empurrar horizontal", tipo: "reps", descanso: 150,
      faixa: [8, 12], forca: [6, 10],
      alerta: "Dor na frente do ombro ou no punho em extensao: regrida um nivel hoje.",
      niveis: [
        { nome: "Flexao inclinada alta (maos em mesa)", musculos: ["peitoral","triceps","deltoide_ant","serratil","abdomen"],
          faixa: [10, 15],
          dicas: ["Corpo em linha reta da cabeca ao calcanhar", "Cotovelos a 45 graus do tronco", "Desca ate o peito quase tocar a mesa", "No topo, empurre a mesa para longe (protrair escapulas)"],
          erros: ["Quadril caido", "Pescoco projetado a frente", "Amplitude parcial"] },
        { nome: "Flexao inclinada baixa (maos em cadeira)", musculos: ["peitoral","triceps","deltoide_ant","serratil","abdomen"],
          faixa: [8, 15],
          dicas: ["Mesma regra: corpo rigido como prancha", "Desca em 2 s, suba em 1 s", "Olhar para um ponto 30 cm a frente das maos"],
          erros: ["Quadril caido", "Cotovelos abertos a 90 graus"] },
        { nome: "Flexao padrao", musculos: ["peitoral","triceps","deltoide_ant","serratil","abdomen"],
          dicas: ["Maos na largura dos ombros ou um pouco mais", "Escapulas retraem na descida e protraem no topo", "Gluteo contraido, quadril nao cai nem sobe", "Peito toca ou quase toca o chao"],
          erros: ["Lombar em hiperextensao", "Cotovelos abertos", "Cabeca cai primeiro"] },
        { nome: "Flexao declinada (pes elevados)", musculos: ["peitoral","deltoide_ant","triceps","serratil","abdomen"],
          dicas: ["Pes em cadeira ou caixa de 30 a 50 cm", "Testa desce para a frente das maos", "Mais carga em peitoral superior e ombro"],
          erros: ["Quadril caindo", "Descer so a cabeca sem o peito"] },
        { nome: "Flexao diamante", musculos: ["triceps","peitoral","deltoide_ant","serratil"],
          dicas: ["Maos juntas sob o centro do peito", "Cotovelos fechados, apontando para tras", "Peito toca as maos"],
          erros: ["Cotovelos abrindo para fora", "Punhos doloridos: afaste um pouco as maos"] },
        { nome: "Flexao archer", musculos: ["peitoral","triceps","deltoide_ant","serratil","abdomen"],
          faixa: [6, 10], forca: [4, 8],
          dicas: ["Maos bem afastadas; um braco estende reto para o lado", "O braco de trabalho dobra, o outro apenas apoia", "Alterne lados a cada repeticao", "Conte 1 repeticao = 1 de cada lado"],
          erros: ["Rodar o tronco", "Braco reto ajudando demais"] },
        { nome: "Flexao pseudo-planche", musculos: ["deltoide_ant","peitoral","triceps","serratil","biceps","abdomen"],
          faixa: [5, 10], forca: [4, 8],
          dicas: ["Maos na altura da cintura, dedos para o lado ou para tras", "Inclinar os ombros bem a frente das maos", "Entrar devagar: punhos e cotovelos precisam de semanas para adaptar"],
          erros: ["Maos muito a frente (vira flexao comum)", "Quadril alto"] }
      ]
    },

    pull_v: {
      nome: "Puxar vertical", tipo: "reps", descanso: 150,
      faixa: [5, 8], forca: [4, 6],
      alerta: "Dor na face interna do cotovelo ou no ombro ao pendurar: regrida um nivel e reduza o volume.",
      niveis: [
        { nome: "Suspensao passiva + scapular pulls", tipo: "tempo", musculos: ["antebraco","dorsal","trapezio"],
          faixa: [20, 40],
          dicas: ["Pendure com bracos estendidos pelo tempo alvo", "Em seguida faca 8 scapular pulls: deprima as escapulas sem dobrar o cotovelo", "Peito aberto, pescoco longo"],
          erros: ["Encolher ombros para cima", "Balancar"] },
        { nome: "Negativas na barra", musculos: ["dorsal","biceps","trapezio","antebraco"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Suba com um pulo ou cadeira ate o queixo acima da barra", "Desca em 3 a 5 segundos, controlando ate a extensao completa", "Cada repeticao comeca do topo"],
          erros: ["Despencar nos ultimos 20 cm", "Soltar as escapulas no fundo"] },
        { nome: "Barra assistida (elastico ou pe em cadeira)", musculos: ["dorsal","biceps","trapezio","antebraco"],
          dicas: ["Amplitude completa: bracos estendidos embaixo, queixo acima em cima", "Use a assistencia minima que permite a faixa alvo", "Inicie o movimento deprimindo as escapulas"],
          erros: ["Empurrar demais com a perna", "Balanco de quadril"] },
        { nome: "Barra fixa estrita", musculos: ["dorsal","biceps","trapezio","antebraco","abdomen"],
          dicas: ["Pegada pronada ou neutra, largura dos ombros", "Primeiro deprima as escapulas, depois dobre os cotovelos", "Peito vai em direcao a barra", "Desca controlado ate a extensao completa"],
          erros: ["Kipping (balancar)", "Encolher ombros no topo", "Nao estender embaixo"] },
        { nome: "Barra com pausa de 2 s ou com carga (mochila)", musculos: ["dorsal","biceps","trapezio","antebraco","abdomen"],
          faixa: [4, 8], forca: [3, 6],
          dicas: ["Pausa de 2 s com queixo acima da barra", "Descida de 3 s", "Ou coloque 5 a 10 % do peso corporal numa mochila"],
          erros: ["Perder a posicao das escapulas na pausa"] },
        { nome: "Barra archer", musculos: ["dorsal","biceps","trapezio","antebraco","abdomen"],
          faixa: [3, 6], forca: [3, 5],
          dicas: ["Pegada larga; um braco puxa, o outro desliza pela barra ficando reto", "Queixo vai para a mao que puxa", "Alterne lados; 1 rep = 1 de cada lado"],
          erros: ["Braco reto fazendo mais que apoio", "Cotovelo de trabalho muito aberto"] },
        { nome: "Preparacao para muscle-up (barra explosiva + transicao)", musculos: ["dorsal","biceps","triceps","peitoral","trapezio","antebraco"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Barra explosiva: puxe ate o esterno chegar na barra", "Transicao em barra baixa: pratique passar o peito sobre a barra com os pes no chao", "So entre aqui com 10 barras estritas limpas"],
          erros: ["Kipping exagerado", "Cotovelos indo para fora na transicao"] }
      ]
    },

    pull_h: {
      nome: "Puxar horizontal", tipo: "reps", descanso: 150,
      faixa: [8, 12], forca: [6, 10],
      alerta: "Dor na face interna do cotovelo: aproxime a pegada e regrida um nivel.",
      niveis: [
        { nome: "Remada alta (barra ou mesa na altura do peito)", musculos: ["dorsal","trapezio","deltoide_post","biceps"],
          faixa: [10, 15],
          dicas: ["Corpo em linha, calcanhares no chao", "Inicie retraindo as escapulas", "Puxe ate o peito tocar a barra", "Desca controlado ate os bracos estendidos"],
          erros: ["Quadril caido", "Encolher ombros"] },
        { nome: "Remada inclinada (barra na altura da cintura)", musculos: ["dorsal","trapezio","deltoide_post","biceps","abdomen"],
          dicas: ["Corpo a cerca de 45 graus", "Cotovelos passam rente ao tronco", "2 s subindo, 2 s descendo"],
          erros: ["Cotovelos acima da linha dos ombros", "Pescoco a frente"] },
        { nome: "Remada horizontal (corpo paralelo ao chao)", musculos: ["dorsal","trapezio","deltoide_post","biceps","abdomen","gluteo"],
          dicas: ["Barra baixa, corpo rigido como prancha", "Peito toca a barra em cada repeticao", "Gluteo contraido o tempo todo"],
          erros: ["Quadril caindo", "Amplitude parcial"] },
        { nome: "Remada com pes elevados", musculos: ["dorsal","trapezio","deltoide_post","biceps","abdomen","gluteo"],
          dicas: ["Pes em cadeira na altura da barra", "Mesma tecnica, mais carga", "Pausa de 1 s no topo"],
          erros: ["Perder a linha do corpo"] },
        { nome: "Remada archer", musculos: ["dorsal","trapezio","deltoide_post","biceps","abdomen"],
          faixa: [5, 10], forca: [4, 8],
          dicas: ["Um braco puxa ate o peito, o outro estende reto", "Tronco nao gira", "Alterne lados"],
          erros: ["Rotacao do tronco", "Braco reto puxando"] },
        { nome: "Tuck front lever + remada em tuck", musculos: ["dorsal","trapezio","abdomen","biceps","deltoide_post"],
          tipo: "tempo", faixa: [10, 20],
          dicas: ["Pendurado, traga os joelhos ao peito e leve as costas paralelas ao chao", "Bracos retos, escapulas deprimidas", "Segure o tempo alvo; se sobrar, faca 3 remadas em tuck"],
          erros: ["Quadril abaixo dos ombros", "Cotovelos dobrando na isometria"] }
      ]
    },

    push_v: {
      nome: "Empurrar vertical", tipo: "reps", descanso: 120,
      faixa: [6, 10], forca: [4, 8],
      alerta: "Dor em punho, ombro anterior ou pescoco: regrida um nivel e aqueca os punhos por mais tempo.",
      niveis: [
        { nome: "Pike push-up com maos elevadas", musculos: ["deltoide_ant","deltoide_med","triceps","trapezio_sup","serratil"],
          faixa: [8, 12],
          dicas: ["Maos em banco baixo, quadril alto formando um V invertido", "Cabeca desce a frente das maos (triangulo com as maos)", "Cotovelos apontam para tras, nao para fora"],
          erros: ["Cabeca entre as maos", "Arquear a lombar"] },
        { nome: "Pike push-up no chao", musculos: ["deltoide_ant","deltoide_med","triceps","trapezio_sup","serratil"],
          dicas: ["Pes mais perto das maos = mais carga nos ombros", "Testa toca o chao a frente das maos", "Empurre o chao e protraia no topo"],
          erros: ["Transformar em flexao comum (quadril baixo)", "Cotovelos abertos"] },
        { nome: "Pike push-up com pes elevados", musculos: ["deltoide_ant","deltoide_med","triceps","trapezio_sup","serratil"],
          dicas: ["Pes em cadeira ou caixa", "Tronco o mais vertical possivel", "Mesma linha de descida da parada de mao"],
          erros: ["Olhar para os pes", "Amplitude parcial"] },
        { nome: "Negativas de flexao em parada de mao (parede)", musculos: ["deltoide_ant","deltoide_med","triceps","trapezio_sup","serratil","abdomen"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Em parada de mao de costas para a parede", "Desca em 3 a 5 s ate a cabeca tocar uma almofada", "Volte ao topo com ajuda dos pes na parede"],
          erros: ["Despencar", "Arquear a lombar"] },
        { nome: "Flexao em parada de mao na parede (HSPU)", musculos: ["deltoide_ant","deltoide_med","triceps","trapezio_sup","serratil","abdomen"],
          faixa: [3, 6], forca: [3, 5],
          dicas: ["Comece com amplitude parcial (2 almofadas), depois 1, depois completa", "Cotovelos para tras, cabeca a frente das maos", "Corpo em linha, costelas fechadas"],
          erros: ["Cotovelos abertos", "Arco lombar", "Punhos frios"] }
      ]
    },

    dips: {
      nome: "Empurrar com dips", tipo: "reps", descanso: 150,
      faixa: [6, 10], forca: [4, 8],
      alerta: "Dor na frente do ombro ou no esterno: reduza a profundidade e regrida um nivel.",
      niveis: [
        { nome: "Flexao declinada ou diamante (sem paralelas)", musculos: ["peitoral","triceps","deltoide_ant","serratil"],
          faixa: [8, 12],
          dicas: ["Use quando nao tiver duas cadeiras firmes ou paralelas", "Pes elevados ou maos juntas", "Descida controlada de 2 s"],
          erros: ["Quadril caido"] },
        { nome: "Dip com apoio dos pes", musculos: ["peitoral","triceps","deltoide_ant"],
          dicas: ["Entre duas cadeiras firmes, pes no chao ajudando o minimo", "Ombros levemente a frente, cotovelos para tras", "Desca ate o ombro na altura do cotovelo"],
          erros: ["Encolher ombros ate as orelhas", "Cotovelos abertos"] },
        { nome: "Dip negativo", musculos: ["peitoral","triceps","deltoide_ant"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Comece no topo com bracos estendidos", "Desca em 3 a 5 s ate o ombro na altura do cotovelo", "Suba ajudando com os pes"],
          erros: ["Descer fundo demais sem controle"] },
        { nome: "Dip completo", musculos: ["peitoral","triceps","deltoide_ant","serratil"],
          dicas: ["Tronco levemente inclinado a frente", "Cotovelos para tras, nao abrem", "Desca ate ombro na linha do cotovelo, suba ate travar"],
          erros: ["Ombros subindo", "Balanco de pernas"] },
        { nome: "Dip com pausa de 2 s ou com carga", musculos: ["peitoral","triceps","deltoide_ant","serratil"],
          faixa: [4, 8], forca: [3, 6],
          dicas: ["Pausa de 2 s embaixo, sem relaxar o ombro", "Ou 5 a 10 % do peso corporal numa mochila"],
          erros: ["Relaxar no fundo"] },
        { nome: "Dip em barra reta (preparacao para muscle-up)", musculos: ["peitoral","triceps","deltoide_ant","serratil","abdomen"],
          faixa: [4, 8], forca: [3, 6],
          dicas: ["Pegada falsa (punho sobre a barra) se possivel", "Inclinar a frente, cotovelos para tras", "E a segunda metade do muscle-up"],
          erros: ["Cotovelos para fora"] }
      ]
    },

    pernas_bi: {
      nome: "Pernas bilateral", tipo: "reps", descanso: 120,
      faixa: [10, 15], forca: [8, 12],
      alerta: "Dor na frente do joelho que piora durante a serie: reduza a profundidade e regrida um nivel.",
      niveis: [
        { nome: "Agachamento em caixa/cadeira", musculos: ["quadriceps","gluteo","adutores"],
          faixa: [10, 15],
          dicas: ["Sente controlado e levante sem balancar", "Pes na largura dos ombros, joelhos na direcao dos pes", "Calcanhares no chao"],
          erros: ["Despencar na cadeira", "Joelhos para dentro"] },
        { nome: "Agachamento livre completo", musculos: ["quadriceps","gluteo","adutores","lombar","panturrilha"],
          faixa: [12, 20],
          dicas: ["Desca o mais fundo que a mobilidade permitir com calcanhar no chao", "Joelhos acompanham a direcao dos pes", "Tronco firme, olhar a frente"],
          erros: ["Valgo dinamico (joelhos caindo para dentro)", "Peso na ponta dos pes", "Tronco caindo a frente"] },
        { nome: "Agachamento com pausa de 3 s", musculos: ["quadriceps","gluteo","adutores","lombar"],
          dicas: ["Pausa de 3 s na posicao mais baixa, sem relaxar", "Subida forte", "Respire no topo"],
          erros: ["Relaxar na pausa", "Perder o arco neutro da lombar"] },
        { nome: "Agachamento com salto controlado ou com mochila", musculos: ["quadriceps","gluteo","panturrilha","adutores"],
          faixa: [8, 12],
          dicas: ["Salto: aterrisse macio, joelhos dobrados, sem barulho", "Ou mochila com 10 a 20 % do peso corporal", "Pausa de 1 s entre repeticoes"],
          erros: ["Aterrissar com joelhos travados", "Joelhos para dentro no salto"] },
        { nome: "Agachamento bulgaro", musculos: ["quadriceps","gluteo","posterior","adutores"],
          faixa: [8, 12], forca: [6, 10],
          dicas: ["Pe de tras numa cadeira, pe da frente a 60 a 80 cm", "Joelho da frente na linha do pe", "Desca ate a coxa paralela; tronco ereto", "Conte por perna"],
          erros: ["Pe da frente perto demais (joelho sofre)", "Inclinar o tronco"] },
        { nome: "Pistol assistido", musculos: ["quadriceps","gluteo","posterior","abdomen"],
          faixa: [5, 8], forca: [4, 6],
          dicas: ["Segure um apoio (porta, barra) com uma mao", "Desca em uma perna ate o fundo, outra perna estendida a frente", "Use a mao o minimo possivel"],
          erros: ["Calcanhar subindo", "Joelho caindo para dentro"] },
        { nome: "Pistol", musculos: ["quadriceps","gluteo","posterior","abdomen"],
          faixa: [4, 8], forca: [3, 6],
          dicas: ["Bracos a frente para equilibrio", "Descida de 3 s, subida controlada", "Se o calcanhar sobe, trabalhe mobilidade de tornozelo"],
          erros: ["Joelho valgo", "Despencar no fundo"] }
      ]
    },

    pernas_uni: {
      nome: "Pernas unilateral", tipo: "reps", descanso: 120,
      faixa: [8, 12], forca: [6, 10],
      alerta: "Dor na frente do joelho ou na virilha: regrida um nivel e reduza a amplitude.",
      niveis: [
        { nome: "Afundo estatico (split squat)", musculos: ["quadriceps","gluteo","posterior","adutores"],
          dicas: ["Pes afastados, um a frente; desca ate o joelho de tras quase tocar o chao", "Tronco ereto, joelho da frente na linha do pe", "Conte por perna"],
          erros: ["Joelho da frente passando muito da ponta do pe com calcanhar subindo", "Tronco inclinado"] },
        { nome: "Afundo reverso", musculos: ["quadriceps","gluteo","posterior","adutores"],
          dicas: ["Passo para tras, desca controlado", "Empurre com a perna da frente para voltar", "Mais gluteo e menos joelho que o afundo para frente"],
          erros: ["Passo curto", "Perder equilibrio"] },
        { nome: "Afundo para frente", musculos: ["quadriceps","gluteo","posterior","adutores"],
          dicas: ["Passo longo a frente, desca em 2 s", "Volte empurrando o calcanhar", "Joelho de tras quase toca o chao"],
          erros: ["Joelho para dentro", "Impulsionar com a ponta do pe de tras"] },
        { nome: "Agachamento bulgaro", musculos: ["quadriceps","gluteo","posterior","adutores"],
          dicas: ["Pe de tras numa cadeira", "Joelho da frente na linha do pe", "Desca ate a coxa paralela ou mais"],
          erros: ["Pe da frente perto demais", "Tronco caindo a frente"] },
        { nome: "Bulgaro com pausa ou com mochila", musculos: ["quadriceps","gluteo","posterior","adutores"],
          faixa: [6, 10], forca: [5, 8],
          dicas: ["Pausa de 2 s embaixo ou mochila com 10 a 20 % do peso", "Mesma tecnica"],
          erros: ["Relaxar na pausa"] },
        { nome: "Pistol assistido", musculos: ["quadriceps","gluteo","posterior","abdomen"],
          faixa: [5, 8], forca: [4, 6],
          dicas: ["Segure um apoio com uma mao", "Desca controlado ate o fundo", "Use a mao o minimo possivel"],
          erros: ["Calcanhar subindo", "Joelho valgo"] }
      ]
    },

    posterior: {
      nome: "Posterior de coxa e gluteo", tipo: "reps", descanso: 120,
      faixa: [8, 12], forca: [6, 10],
      alerta: "Dor aguda atras da coxa ou atras do joelho: pare o exercicio hoje.",
      niveis: [
        { nome: "Ponte de gluteo", musculos: ["gluteo","posterior","lombar"],
          faixa: [12, 20],
          dicas: ["Deitado, pes no chao perto do gluteo", "Suba o quadril ate a linha do tronco, segure 1 s", "Nao arquear a lombar; contraia o abdomen"],
          erros: ["Hiperextensao lombar", "Empurrar com a ponta dos pes"] },
        { nome: "Ponte unilateral", musculos: ["gluteo","posterior","lombar"],
          dicas: ["Uma perna estendida ou joelho ao peito", "Quadril nao roda", "Conte por perna"],
          erros: ["Quadril caindo para um lado"] },
        { nome: "Elevacao de quadril unilateral com pes em cadeira", musculos: ["gluteo","posterior","lombar"],
          dicas: ["Calcanhar na cadeira, quadril sobe ate a linha", "Puxe o calcanhar em direcao ao gluteo durante a subida (mais posterior)", "Conte por perna"],
          erros: ["Lombar arqueando"] },
        { nome: "Nordic curl assistido", musculos: ["posterior","gluteo","panturrilha"],
          faixa: [4, 8], forca: [3, 6],
          dicas: ["Joelhos no chao (acolchoado), pes presos sob um sofa ou segurados", "Desca o tronco em linha reta, controlando com o posterior", "Use as maos para amortecer e para voltar"],
          erros: ["Dobrar o quadril (vira inclinacao de tronco)", "Despencar"] },
        { nome: "Nordic negativo", musculos: ["posterior","gluteo","panturrilha"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Desca em 4 a 6 s ate as maos tocarem o chao", "Volte ajudando com as maos", "Volume pequeno: 2 a 3 series bastam"],
          erros: ["Quadril flexionando", "Acelerar no fim"] },
        { nome: "Nordic completo", musculos: ["posterior","gluteo","panturrilha"],
          faixa: [3, 5], forca: [3, 5],
          dicas: ["Desca e suba sem ajuda das maos", "Quadril estendido o tempo todo", "Exercicio avancado; mantenha 2 a 3 series"],
          erros: ["Quadril flexionando para facilitar"] }
      ]
    },

    core_ant: {
      nome: "Core anterior", tipo: "tempo", descanso: 60,
      faixa: [20, 40], forca: [20, 40],
      alerta: "Dor na lombar: a lombar saiu do chao. Regrida um nivel.",
      niveis: [
        { nome: "Dead bug", tipo: "reps", faixa: [8, 12], musculos: ["abdomen","obliquos","flexores_quadril"],
          dicas: ["Deitado, lombar colada no chao, joelhos a 90 graus", "Estenda braco e perna opostos devagar", "Expire ao estender; 1 rep = 1 de cada lado"],
          erros: ["Lombar descolando", "Prender a respiracao"] },
        { nome: "Hollow hold com joelhos dobrados", musculos: ["abdomen","obliquos","flexores_quadril"],
          dicas: ["Lombar pressionada no chao", "Ombros a 10 cm do chao, joelhos dobrados", "Bracos ao lado ou acima da cabeca"],
          erros: ["Lombar arqueando", "Queixo no peito"] },
        { nome: "Hollow hold completo", musculos: ["abdomen","obliquos","flexores_quadril","serratil"],
          dicas: ["Pernas retas a 10 a 20 cm do chao", "Bracos acima da cabeca", "Lombar sempre no chao: se sair, dobre os joelhos"],
          erros: ["Lombar saindo do chao"] },
        { nome: "Hollow rocks", tipo: "reps", faixa: [10, 20], musculos: ["abdomen","obliquos","flexores_quadril","serratil"],
          dicas: ["Mantenha a forma do hollow e balance como uma canoa", "O movimento vem do balanco, nao do quadril"],
          erros: ["Perder a forma e virar abdominal"] },
        { nome: "Tuck L-sit", musculos: ["abdomen","flexores_quadril","triceps","serratil","quadriceps"],
          faixa: [10, 25],
          dicas: ["Em duas cadeiras ou paralelas, bracos retos", "Joelhos ao peito, ombros deprimidos", "Segure o tempo alvo"],
          erros: ["Ombros nas orelhas", "Cotovelos dobrados"] },
        { nome: "L-sit", musculos: ["abdomen","flexores_quadril","triceps","serratil","quadriceps"],
          faixa: [10, 25],
          dicas: ["Pernas retas e paralelas ao chao", "Pontas dos pes estendidas", "Ombros empurrando para baixo"],
          erros: ["Pernas caindo", "Inclinar o tronco para tras"] },
        { nome: "Elevacao de pernas suspenso", tipo: "reps", faixa: [8, 12], musculos: ["abdomen","flexores_quadril","antebraco","dorsal"],
          dicas: ["Pendurado na barra, joelhos dobrados primeiro, depois pernas retas", "Suba ate os pes na altura da barra ou acima", "Desca em 2 a 3 s sem balancar"],
          erros: ["Balanco", "Arquear a lombar na descida"] }
      ]
    },

    core_lat: {
      nome: "Core lateral e anti-rotacao", tipo: "tempo", descanso: 60,
      faixa: [20, 40], forca: [20, 40],
      alerta: "Dor no ombro de apoio ou na lombar: regrida um nivel.",
      niveis: [
        { nome: "Prancha lateral com joelhos", musculos: ["obliquos","gluteo","deltoide_med"],
          dicas: ["Cotovelo sob o ombro, joelhos dobrados", "Quadril alto, corpo em linha", "Tempo por lado"],
          erros: ["Quadril caindo", "Ombro de apoio encolhido"] },
        { nome: "Prancha lateral", musculos: ["obliquos","gluteo","deltoide_med","adutores"],
          dicas: ["Pes empilhados, corpo em linha reta", "Quadril nao cai nem roda", "Respire normalmente"],
          erros: ["Quadril caindo", "Rodar para frente"] },
        { nome: "Prancha lateral com elevacao de perna", musculos: ["obliquos","gluteo","adutores","deltoide_med"],
          dicas: ["Perna de cima elevada 20 a 30 cm", "Mantem o quadril alto"],
          erros: ["Perder a linha"] },
        { nome: "Copenhagen plank (perna de cima na cadeira)", musculos: ["adutores","obliquos","gluteo"],
          faixa: [15, 30],
          dicas: ["Perna de cima apoiada na cadeira, de baixo livre", "Quadril alto, corpo reto", "Protege a virilha; comece curto"],
          erros: ["Dor na virilha: reduza o tempo pela metade"] },
        { nome: "Windshield wipers deitado", tipo: "reps", faixa: [8, 12], musculos: ["obliquos","abdomen","flexores_quadril"],
          dicas: ["Deitado, pernas a 90 graus, bracos abertos", "Leve as pernas de um lado ao outro controlando", "Ombros colados no chao"],
          erros: ["Ombros levantando", "Velocidade"] }
      ]
    },

    hab_parada: {
      nome: "Habilidade: parada de mao na parede", tipo: "tempo", descanso: 90, habilidade: true,
      faixa: [15, 30], forca: [30, 60],
      alerta: "Dor no punho: reduza o tempo pela metade e aqueca mais.",
      niveis: [
        { nome: "Parada de mao peito para a parede", musculos: ["deltoide_ant","trapezio_sup","triceps","serratil","abdomen","antebraco"],
          dicas: ["Entre pela prancha e suba os pes pela parede ate so as pontas tocarem", "Maos a 15 a 30 cm da parede", "Empurre o chao, feche as costelas, gluteo contraido", "Saia andando com as maos para fora"],
          erros: ["Arco lombar (banana)", "Olhar para o chao com o pescoco jogado", "Cotovelos dobrando"] }
      ]
    },

    hab_suspensao: {
      nome: "Habilidade: suspensao ativa", tipo: "tempo", descanso: 90, habilidade: true,
      faixa: [20, 40], forca: [40, 60],
      alerta: "Dor no cotovelo ou ombro pendurado: reduza o tempo.",
      niveis: [
        { nome: "Suspensao ativa (escapulas deprimidas)", musculos: ["antebraco","dorsal","trapezio","abdomen"],
          dicas: ["Pendurado com bracos retos, puxe as escapulas para baixo (pescoco fica longo)", "Corpo em hollow leve", "Alvo final: 60 s"],
          erros: ["Ombros nas orelhas", "Balancar"] }
      ]
    }
  },

  /* Sessoes: lista de cadeias em ordem. "principal" marca os exercicios que ganham
     a 4a serie nos Blocos 2 e 3. */
  sessoes: {
    A: { nome: "Treino A", itens: [
      { cadeia: "hab_parada" },
      { cadeia: "push_h", principal: true },
      { cadeia: "pull_v", principal: true },
      { cadeia: "pernas_bi" },
      { cadeia: "push_v" },
      { cadeia: "pull_h" },
      { cadeia: "core_ant" }
    ]},
    B: { nome: "Treino B", itens: [
      { cadeia: "hab_suspensao" },
      { cadeia: "pull_h", principal: true },
      { cadeia: "dips", principal: true },
      { cadeia: "posterior" },
      { cadeia: "pull_v" },
      { cadeia: "pernas_uni" },
      { cadeia: "core_lat" }
    ]}
  },

  /* Blocos por semana (1 a 12). series = series base; seriesPrincipal nas marcadas.
     rir = RIR alvo. deload reduz series e sobe o RIR. usarForca troca a faixa. */
  blocos: [
    { semanas: [1, 2, 3],   nome: "Bloco 1: Base e tecnica", series: 3, seriesPrincipal: 3, rir: 2, usarForca: false },
    { semanas: [4],         nome: "Bloco 1: Deload",          series: 2, seriesPrincipal: 2, rir: 3, usarForca: false, deload: true },
    { semanas: [5, 6, 7],   nome: "Bloco 2: Forca",           series: 3, seriesPrincipal: 4, rir: 1, usarForca: false },
    { semanas: [8],         nome: "Bloco 2: Deload",          series: 2, seriesPrincipal: 2, rir: 3, usarForca: false, deload: true },
    { semanas: [9, 10, 11], nome: "Bloco 3: Forca e habilidade", series: 3, seriesPrincipal: 4, rir: 1, usarForca: true },
    { semanas: [12],        nome: "Bloco 3: Reteste e deload", series: 2, seriesPrincipal: 2, rir: 3, usarForca: true, deload: true, reteste: true }
  ],

  aquecimento: [
    "2 min de movimento leve: polichinelo, corrida parada ou pular corda",
    "Circulos de ombro (10 para cada lado), rotacao de tronco (10), agachamento livre (10), gato-camelo (8)",
    "Punhos: 30 s em quatro apoios balancando o peso sobre as maos; 10 flexoes de punho",
    "Escapulas: 10 scapular pulls na barra, 10 protracoes em prancha",
    "Uma serie leve (metade das reps) do primeiro exercicio de forca"
  ],

  voltaCalma: [
    "Alongamento de peitoral na porta: 30 a 45 s por lado",
    "Flexores de quadril (afundo baixo): 30 a 45 s por lado",
    "Antebraco (palma na parede, dedos para baixo): 30 s por lado",
    "Dorsal (pendurado relaxado ou apoiado numa mesa): 30 a 45 s"
  ],

  /* Regras de posicionamento a partir do teste inicial. Retornam indice de nivel (0-based). */
  posicionar: {
    push_h:    function (t) { var f = t.flexoes; return f < 3 ? 0 : f < 8 ? 1 : f < 20 ? 2 : f < 30 ? 3 : 4; },
    dips:      function (t) { var f = t.flexoes; return f < 8 ? 0 : f < 20 ? (t.paralelas ? 1 : 0) : (t.paralelas ? 2 : 0); },
    pull_v:    function (t) { var b = t.barras, s = t.suspensao; return b === 0 ? (s < 20 ? 0 : 1) : b < 4 ? 2 : b < 8 ? 3 : b < 15 ? 4 : 5; },
    pull_h:    function (t) { var b = t.barras; return b === 0 ? (t.suspensao < 20 ? 0 : 1) : b < 4 ? 1 : b < 8 ? 2 : 3; },
    push_v:    function (t) { var f = t.flexoes; return f < 8 ? 0 : f < 20 ? 1 : 2; },
    pernas_bi: function (t) { var a = t.agachamentos; return a < 15 ? 0 : a < 30 ? 1 : a < 50 ? 2 : 3; },
    pernas_uni:function (t) { var a = t.agachamentos; return a < 15 ? 0 : a < 30 ? 1 : a < 50 ? 2 : 3; },
    posterior: function (t) { var a = t.agachamentos; return a < 15 ? 0 : a < 30 ? 1 : 2; },
    core_ant:  function (t) { var h = t.hollow; return h < 20 ? 0 : h < 30 ? 1 : h < 45 ? 2 : 3; },
    core_lat:  function (t) { var h = t.hollow; return h < 20 ? 0 : 1; },
    hab_parada:function () { return 0; },
    hab_suspensao: function () { return 0; }
  }
};

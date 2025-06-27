// ✅ Função chamada quando houver edição na planilha (manual)
function onEdit(e) {
  if (!e || !e.source) return;
  if (e.source.getActiveSheet().getName() !== "Leituras") return;

  const col = e.range.getColumn();
  const row = e.range.getRow();

  if (col !== 1 || row === 1) return;

  const sheet = e.range.getSheet();
  const valor = e.value || e.range.getValue();
  if (valor) {
    processarLeituraAppSheet(e);
  }
}

// ✅ Função chamada por integração externa para processar leitura
function processarLeituraAppSheet(e) {
  if (!e || !e.source || !e.value) return;

  const sheet = e.source.getActiveSheet();
  if (!sheet || sheet.getName() !== "Leituras") return;

  const col = e.range.getColumn();
  const row = e.range.getRow();
  if (col !== 1 || row === 1) return;

  const valor = e.value || e.range.getValue();
  if (!valor) return;

  try {
    const valorOriginal = valor.toString().trim();
    e.range.setValue(valorOriginal); // Simula input manual
    SpreadsheetApp.flush();

    processarLeitura(e.range, valorOriginal);

    const proximaLinha = moverParaProximaLinhaVazia(sheet);
    if (proximaLinha) {
      const proximaCelula = sheet.getRange(proximaLinha, 1);
      proximaCelula.activate();
      sheet.setActiveRange(proximaCelula);
      SpreadsheetApp.flush();
    }
  } catch (error) {
    console.error("Erro ao processar leitura do AppSheet:", error);
    moverParaProximaLinhaVazia(sheet);
  }
}

// ✅ NOVO: Verifica novas leituras automaticamente
function verificarNovasLeituras() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("Leituras");
  if (!sheet) return;

  const data = sheet.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    const serial = data[i][0];
    const status = data[i][2];

    if (serial && !status) {
      const range = sheet.getRange(i + 1, 1);
      const valorOriginal = serial.toString().trim();

      try {
        sheet.getRange(i + 1, 3).setValue("PROCESSANDO");
        range.setValue(valorOriginal);
        SpreadsheetApp.flush();
        processarLeitura(range, valorOriginal);
      } catch (err) {
        sheet.getRange(i + 1, 3).setValue("ERRO");
        sheet.getRange(i + 1, 4).setValue("Erro automático: " + err.toString());
      }
    }
  }
}

// ✅ Processa o serial e gera o pedido
function processarLeitura(range, valorSerial) {
  const serial = valorSerial || range.getValue();
  if (!serial) return;

  const sheet = range.getSheet();
  const agora = new Date();
  const timestamp = formatarData(agora);
  sheet.getRange(range.getRow(), 2).setValue(timestamp);

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const verificacao = verificarPedidoRecente(serial);
    if (verificacao.duplicado) {
      sheet.getRange(range.getRow(), 3).setValue("AVISO");
      sheet.getRange(range.getRow(), 4).setValue(
        `Pedido ${verificacao.numeroPedido} já existe para este item e Semiacabado ${verificacao.semiacabado} ` +
        `(criado em ${verificacao.dataAnterior}). Aguarde 10 segundos para criar um novo pedido.`
      );
      sheet.getRange(range.getRow(), 5).setValue(verificacao.numeroPedido);
      moverParaProximaLinhaVazia(sheet);
      return;
    }

    const pacoSheet = ss.getSheetByName("paco");
    if (!pacoSheet) {
      sheet.getRange(range.getRow(), 3).setValue("ERRO");
      sheet.getRange(range.getRow(), 4).setValue("Aba 'paco' não encontrada");
      return;
    }

    const pacoData = pacoSheet.getDataRange().getValues();
    const headers = pacoData[0];
    const serialIdx = headers.indexOf("Serial");
    const maquinaIdx = headers.indexOf("Maquina");
    const postoIdx = headers.indexOf("Posto");
    const coordenadaIdx = headers.indexOf("Coordenada");
    const modeloIdx = headers.indexOf("Modelo");
    const otIdx = headers.indexOf("OT");
    const semiacabadoIdx = headers.indexOf("Semiacabado");
    const pagodaIdx = headers.indexOf("Pagoda");

    let itemEncontrado = null;
    for (let i = 1; i < pacoData.length; i++) {
      const row = pacoData[i];
      if (row[serialIdx] && row[serialIdx].toString().trim().toUpperCase() === serial.toString().trim().toUpperCase()) {
        itemEncontrado = {
          serial: row[serialIdx],
          maquina: row[maquinaIdx],
          posto: row[postoIdx],
          coordenada: row[coordenadaIdx],
          modelo: row[modeloIdx],
          ot: row[otIdx],
          semiacabado: row[semiacabadoIdx],
          pagoda: row[pagodaIdx]
        };
        break;
      }
    }

    if (!itemEncontrado) {
      sheet.getRange(range.getRow(), 3).setValue("ERRO");
      sheet.getRange(range.getRow(), 4).setValue("Item não encontrado na base de dados");
      return;
    }

    const pedidosSheet = ss.getSheetByName("Pedidos");
    if (!pedidosSheet) {
      sheet.getRange(range.getRow(), 3).setValue("ERRO");
      sheet.getRange(range.getRow(), 4).setValue("Aba 'Pedidos' não encontrada");
      return;
    }

    let proximoNum = 1;
    const ultimoPedidos = pedidosSheet.getRange("A2:A").getValues();
    if (ultimoPedidos.length > 0) {
      const nums = ultimoPedidos
        .filter(row => row[0] && row[0].toString().startsWith("REQ-"))
        .map(row => parseInt(row[0].split("-")[1]) || 0);
      if (nums.length > 0) {
        proximoNum = Math.max(...nums) + 1;
      }
    }

    const numeroPedido = `REQ-${String(proximoNum).padStart(3, "0")}`;
    const novoPedido = [
      numeroPedido, timestamp, itemEncontrado.serial, itemEncontrado.maquina, itemEncontrado.posto,
      itemEncontrado.coordenada, itemEncontrado.modelo, itemEncontrado.ot, itemEncontrado.semiacabado,
      itemEncontrado.pagoda, "PENDENTE", "Não", timestamp, "AppSheet", "", "", "", "", "AppSheet",
      "Pedido gerado automaticamente via AppSheet"
    ];

    pedidosSheet.appendRow(novoPedido);

    const itensSheet = ss.getSheetByName("Itens");
    if (itensSheet) {
      itensSheet.appendRow([numeroPedido, itemEncontrado.serial, 1]);
    }

    sheet.getRange(range.getRow(), 3).setValue("SUCESSO");
    sheet.getRange(range.getRow(), 4).setValue(`Pedido ${numeroPedido} criado com sucesso`);
    sheet.getRange(range.getRow(), 5).setValue(numeroPedido);

    moverParaProximaLinhaVazia(sheet);
  } catch (error) {
    sheet.getRange(range.getRow(), 3).setValue("ERRO");
    sheet.getRange(range.getRow(), 4).setValue(`Erro ao processar: ${error.toString()}`);
    moverParaProximaLinhaVazia(sheet);
  }
}

function moverParaProximaLinhaVazia(sheet) {
  const lastRow = sheet.getLastRow();
  const proximaLinha = lastRow + 1;
  const range = sheet.getRange(proximaLinha, 1);
  range.activate();
  sheet.setActiveRange(range);
  SpreadsheetApp.flush();
  return proximaLinha;
}

function formatarData(data) {
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  const hora = String(data.getHours()).padStart(2, '0');
  const minuto = String(data.getMinutes()).padStart(2, '0');
  const segundo = String(data.getSeconds()).padStart(2, '0');
  return `${ano}-${mes}-${dia} ${hora}:${minuto}:${segundo}`;
}

function verificarPedidoRecente(serial, intervaloSegundos = 10) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const pacoSheet = ss.getSheetByName("paco");
  if (!pacoSheet) return { duplicado: false };

  const pacoData = pacoSheet.getDataRange().getValues();
  const pacoHeaders = pacoData[0];
  const serialIdx = pacoHeaders.indexOf("Serial");
  const semiacabadoIdx = pacoHeaders.indexOf("Semiacabado");

  let semiacabadoAtual = null;
  for (let i = 1; i < pacoData.length; i++) {
    if (pacoData[i][serialIdx]?.toString().trim().toUpperCase() === serial.toString().trim().toUpperCase()) {
      semiacabadoAtual = pacoData[i][semiacabadoIdx];
      break;
    }
  }
  if (!semiacabadoAtual) return { duplicado: false };

  const pedidosSheet = ss.getSheetByName("Pedidos");
  if (!pedidosSheet) return { duplicado: false };

  const pedidosData = pedidosSheet.getDataRange().getValues();
  const headers = pedidosData[0];
  const serialIdxP = headers.indexOf("Serial");
  const semiacabadoIdxP = headers.indexOf("Semiacabado");
  const dataIdx = headers.indexOf("Data");
  const numeroPedidoIdx = headers.indexOf("Numero_Pedido");
  const statusIdx = headers.indexOf("Status");

  const agora = new Date();

  for (let i = 1; i < pedidosData.length; i++) {
    const row = pedidosData[i];
    if (
      row[serialIdxP]?.toString().trim().toUpperCase() === serial.toString().trim().toUpperCase() &&
      row[semiacabadoIdxP]?.toString().trim().toUpperCase() === semiacabadoAtual.toString().trim().toUpperCase()
    ) {
      const dataPedido = new Date(row[dataIdx]);
      const segundos = Math.abs((agora - dataPedido) / 1000);
      if (segundos <= intervaloSegundos && row[statusIdx] !== "CANCELADO") {
        return {
          duplicado: true,
          numeroPedido: row[numeroPedidoIdx],
          dataAnterior: formatarData(dataPedido),
          semiacabado: semiacabadoAtual
        };
      }
    }
  }

  return { duplicado: false };
}

// ✅ Configura todos os gatilhos e prepara a planilha
function setupAppSheetTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    const fn = trigger.getHandlerFunction();
    if (["processarLeituraAppSheet", "onEdit", "verificarNovasLeituras"].includes(fn)) {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();

  ScriptApp.newTrigger('processarLeituraAppSheet')
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();

  ScriptApp.newTrigger('verificarNovasLeituras')
    .timeBased()
    .everyMinutes(1)
    .create();

  setupPlanilha();
  Logger.log('Todos os gatilhos configurados!');
  return '✅ Configuração concluída com sucesso!';
}

function setupPlanilha() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let leiturasSheet = ss.getSheetByName("Leituras");
  if (!leiturasSheet) {
    leiturasSheet = ss.insertSheet("Leituras");
    leiturasSheet.getRange(1, 1, 1, 5).setValues([
      ["Serial", "Data_Leitura", "Status", "Mensagem", "Numero_Pedido"]
    ]);
    leiturasSheet.getRange(1, 1, 1, 5).setFontWeight("bold");
    leiturasSheet.setFrozenRows(1);
  }

  let pedidosSheet = ss.getSheetByName("Pedidos");
  if (!pedidosSheet) {
    pedidosSheet = ss.insertSheet("Pedidos");
    pedidosSheet.getRange(1, 1, 1, 20).setValues([
      ["Numero_Pedido", "Data", "Serial", "Maquina", "Posto", "Coordenada", "Modelo", "OT", "Semiacabado", "Pagoda", "Status", "Urgente", "Ultima_Atualizacao", "Responsavel_Atualizacao", "Responsavel_Separacao", "Data_Separacao", "Responsavel_Coleta", "Data_Coleta", "Solicitante", "Observacoes"]
    ]);
    pedidosSheet.getRange(1, 1, 1, 20).setFontWeight("bold");
    pedidosSheet.setFrozenRows(1);
  }

  let itensSheet = ss.getSheetByName("Itens");
  if (!itensSheet) {
    itensSheet = ss.insertSheet("Itens");
    itensSheet.getRange(1, 1, 1, 3).setValues([
      ["Numero_Pedido", "Serial", "Quantidade"]
    ]);
    itensSheet.getRange(1, 1, 1, 3).setFontWeight("bold");
    itensSheet.setFrozenRows(1);
  }
}

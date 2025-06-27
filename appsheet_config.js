// Configurações globais
const APPSHEET_API_KEY = PropertiesService.getScriptProperties().getProperty('APPSHEET_API_KEY');
const WORKSPACE_ID = PropertiesService.getScriptProperties().getProperty('WORKSPACE_ID');

// Função para verificar configurações
function checkConfig() {
  const ui = SpreadsheetApp.getUi();
  
  if (!APPSHEET_API_KEY || !WORKSPACE_ID) {
    ui.alert(
      'Configuração Necessária',
      'As credenciais do AppSheet não estão configuradas. Vou abrir a tela de configuração.',
      ui.ButtonSet.OK
    );
    setupAppSheetConfig();
    return false;
  }
  return true;
}

// Função para criar o app AppSheet via API REST
function createAppSheetApp() {
  const ui = SpreadsheetApp.getUi();
  
  // Verificar configurações
  if (!checkConfig()) {
    return;
  }

  try {
    Logger.log('Iniciando criação do app...');
    Logger.log('Workspace ID configurado: ' + WORKSPACE_ID);
    
    const spreadsheetId = SpreadsheetApp.getActiveSpreadsheet().getId();
    const spreadsheetUrl = SpreadsheetApp.getActiveSpreadsheet().getUrl();
    
    Logger.log('Planilha ID: ' + spreadsheetId);
    Logger.log('Planilha URL: ' + spreadsheetUrl);
    
    // Configuração do app AppSheet
    const appConfig = {
      "application": {
        "name": "Scanner de Códigos de Barras",
        "description": "App para leitura de códigos de barras e sincronização com Google Sheets",
        "workspaceId": WORKSPACE_ID,
        "templateName": "Blank",
        "locale": "pt_BR",
        "timeZone": "America/Sao_Paulo"
      },
      "dataSource": {
        "type": "GoogleSheets",
        "spreadsheetUrl": spreadsheetUrl
      },
      "structure": {
        "tables": [{
          "name": "Leituras",
          "sheetName": "Leituras",
          "columns": [
            {
              "name": "Serial",
              "type": "TEXT",
              "required": true,
              "showInGrid": true
            },
            {
              "name": "Data_Leitura",
              "type": "DATETIME",
              "required": true,
              "showInGrid": true,
              "defaultValue": "NOW()"
            },
            {
              "name": "Status",
              "type": "TEXT",
              "required": true,
              "showInGrid": true
            },
            {
              "name": "Mensagem",
              "type": "TEXT",
              "showInGrid": true
            },
            {
              "name": "Numero_Pedido",
              "type": "TEXT",
              "showInGrid": true
            }
          ]
        }]
      },
      "userInterface": {
        "formView": {
          "name": "Scanner",
          "tableName": "Leituras",
          "showAsCard": true,
          "fields": ["Serial"],
          "barcodeScanningEnabled": true
        },
        "gridView": {
          "name": "Histórico",
          "tableName": "Leituras",
          "sortBy": [{"column": "Data_Leitura", "direction": "DESC"}]
        }
      },
      "security": {
        "authenticationType": "google",
        "requireAuthentication": true
      },
      "settings": {
        "offlineEnabled": true,
        "syncIntervalMinutes": 5,
        "theme": {
          "primaryColor": "#4285f4",
          "accentColor": "#34a853"
        }
      }
    };

    Logger.log('Configuração do app preparada');
    Logger.log('Payload: ' + JSON.stringify(appConfig, null, 2));
    Logger.log('Fazendo chamada para API do AppSheet...');

    // Criar o app via API REST
    const options = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${APPSHEET_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      payload: JSON.stringify({
        name: appConfig.application.name,
        description: appConfig.application.description,
        workspaceId: WORKSPACE_ID,
        properties: {
          source: {
            type: 'GoogleSheets',
            documentId: spreadsheetId
          },
          definition: JSON.stringify(appConfig)
        }
      }),
      muteHttpExceptions: true
    };

    Logger.log('Enviando requisição...');
    const response = UrlFetchApp.fetch('https://api.appsheet.com/rest/applications', options);
    Logger.log('Código de resposta: ' + response.getResponseCode());
    Logger.log('Resposta bruta: ' + response.getContentText());
    
    const responseText = response.getContentText();
    if (!responseText) {
      throw new Error('Resposta vazia da API do AppSheet');
    }

    try {
      const result = JSON.parse(responseText);
      Logger.log('Resposta parseada: ' + JSON.stringify(result, null, 2));

      if (response.getResponseCode() === 200 || response.getResponseCode() === 201) {
        Logger.log("App AppSheet criado com sucesso!");
        PropertiesService.getScriptProperties().setProperty('APP_ID', result.id || '');
        
        ui.alert(
          'Sucesso!',
          'App criado com sucesso!\n\n' +
          'URL do app: ' + (result.applicationUrl || result.url || 'Verifique no AppSheet') + '\n\n' +
          'Abra o AppSheet para configurar permissões.',
          ui.ButtonSet.OK
        );
        
        return {
          success: true,
          appUrl: result.applicationUrl || result.url,
          message: "App criado com sucesso!"
        };
      } else {
        throw new Error(result.message || result.error || 'Erro desconhecido ao criar o app');
      }
    } catch (parseError) {
      Logger.log('Erro ao fazer parse da resposta: ' + parseError);
      throw new Error('Erro ao processar resposta da API: ' + responseText);
    }
  } catch (error) {
    Logger.log("Erro detalhado: " + error.toString());
    Logger.log("Stack trace: " + error.stack);
    
    ui.alert(
      'Erro',
      'Falha ao criar o app:\n\n' + 
      error.toString() + '\n\n' +
      'Por favor, verifique:\n' +
      '1. Se sua API Key está correta\n' +
      '2. Se seu Workspace ID está correto\n' +
      '3. Se você tem permissão para criar apps\n\n' +
      'Verifique o log para mais detalhes.',
      ui.ButtonSet.OK
    );
    
    return {
      success: false,
      error: error.toString(),
      message: "Falha ao criar o app. Verifique as configurações."
    };
  }
}

// Função para configurar as credenciais do AppSheet
function setupAppSheetConfig() {
  const ui = SpreadsheetApp.getUi();
  
  // Solicitar API Key
  const apiKeyResult = ui.prompt(
    'Configuração do AppSheet',
    'Cole sua API Key do AppSheet:\n\n' +
    '(Você pode encontrar em appsheet.com > Account > API Keys)',
    ui.ButtonSet.OK_CANCEL
  );
  if (apiKeyResult.getSelectedButton() == ui.Button.CANCEL) return;
  
  // Solicitar Workspace ID
  const workspaceResult = ui.prompt(
    'Configuração do AppSheet',
    'Cole seu Workspace ID do AppSheet:\n\n' +
    '(Você pode encontrar em appsheet.com > Account > API Keys, no topo da página)',
    ui.ButtonSet.OK_CANCEL
  );
  if (workspaceResult.getSelectedButton() == ui.Button.CANCEL) return;
  
  // Salvar configurações
  PropertiesService.getScriptProperties().setProperties({
    'APPSHEET_API_KEY': apiKeyResult.getResponseText().trim(),
    'WORKSPACE_ID': workspaceResult.getResponseText().trim()
  });
  
  ui.alert(
    'Configuração',
    'Configurações salvas com sucesso!\n\n' +
    'Agora você pode criar o app usando a opção "2. Criar App Scanner"',
    ui.ButtonSet.OK
  );
}

// Função para limpar configurações
function limparConfiguracoes() {
  const ui = SpreadsheetApp.getUi();
  
  // Limpar todas as propriedades
  PropertiesService.getScriptProperties().deleteAllProperties();
  
  ui.alert(
    'Configurações Limpas',
    'Todas as configurações foram removidas.\n\n' +
    'Agora você pode configurar novamente usando a opção "1. Configurar AppSheet"',
    ui.ButtonSet.OK
  );
}

// Função para configurar o menu na planilha
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('AppSheet')
    .addItem('0. Limpar Configurações', 'limparConfiguracoes')
    .addItem('1. Configurar AppSheet', 'setupAppSheetConfig')
    .addItem('2. Criar App Scanner', 'createAppSheetApp')
    .addToUi();
} 
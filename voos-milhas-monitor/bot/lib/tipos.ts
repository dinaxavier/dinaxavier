// Tipos compartilhados entre as ferramentas

export interface Conexao {
  aeroporto_chegada: string;
  cidade_chegada: string;
  pais_chegada: string;
  aeroporto_partida: string;
  cidade_partida: string;
  horario_chegada: string;
  horario_partida: string;
  tempo_conexao_minutos: number;
  companhia: string;
  troca_companhia: boolean;
  mudanca_aeroporto: boolean;
  troca_terminal: boolean;
  redespacho_bagagem: boolean;
}

export interface DadosVoo {
  id: string;
  timestamp: string;
  origem: string;
  destino: string;
  data_ida: string;
  data_volta?: string;
  companhia: string;
  
  // Preços
  preco_por_pessoa: number;
  preco_total: number;
  preco_referencia: number;
  economia_estimada: number;
  desconto_percentual: number;
  
  // Logística
  tipo_voo_ida: "Direto" | "1 Conexão" | "2+ Conexões";
  tipo_voo_volta?: "Direto" | "1 Conexão" | "2+ Conexões";
  conexoes_ida: Conexao[];
  conexoes_volta: Conexao[];
  duracao_total_ida: string;
  duracao_total_volta?: string;
  tempo_voo_ida: string;
  tempo_voo_volta?: string;
  mudanca_aeroporto: boolean;
  
  // Avaliação
  classificacao_logistica: "Excelente" | "Boa" | "Moderada" | "Atenção";
  alertas_logisticos: string[];
  score: number;
  
  // Extras
  bagagem_incluida: string;
  tipo_bilhete: string;
  link?: string;
  observacoes?: string;
}

export interface DadosMilhas {
  id: string;
  timestamp: string;
  programa: string;
  tipo_promocao: string;
  descricao: string;
  
  // Promoção
  quantidade_base: number;
  bonus_percentual: number;
  quantidade_total: number;
  preco_total: number;
  
  // Análise
  custo_por_milheiro: number;
  referencia_historica: number;
  economia_por_milheiro: number;
  desconto_percentual: number;
  
  // Condições
  elegibilidade: string;
  validade_promocao: string;
  validade_milhas: string;
  condicoes_especiais: string[];
  
  // Avaliação
  score: number;
  
  // Extras
  link_oficial?: string;
  observacoes?: string;
}

export interface OportunidadeCombinada {
  id: string;
  timestamp: string;
  rota: string;
  datas: string;
  programa: string;
  companhia: string;
  
  // Custos
  milhas_necessarias: number;
  custo_aquisicao_milhas: number;
  taxas_encargos: number;
  custo_total_emissao: number;
  
  // Comparação
  preco_em_dinheiro: number;
  economia_liquida: number;
  economia_percentual: number;
  
  // Disponibilidade
  disponibilidade_emissao: boolean;
  dados_logisticos: any;
  
  // Avaliação
  score: number;
  
  // Links
  link_promocao_milhas?: string;
  link_emissao?: string;
}

export interface ConfiguracaoMonitor {
  // Voos
  origens: string[];
  destinos: string[];
  data_ida_inicio: string;
  data_ida_fim: string;
  data_volta_inicio?: string;
  data_volta_fim?: string;
  passageiros: number;
  preco_maximo?: number;
  desconto_minimo: number;
  voo_direto_preferencial: boolean;
  max_conexoes?: number;
  aceitar_mudanca_aeroporto: boolean;
  
  // Milhas
  programas_milhas?: string[];
  custo_maximo_milheiro?: number;
  desconto_minimo_milhas: number;
  
  // Notificações
  email_destinatarios: string[];
  dashboard_url?: string;
  
  // Planilha
  google_sheets_id?: string;
}

export interface ResultadoValidacao {
  timestamp: string;
  total_verificadas: number;
  ativas: any[];
  atualizadas: any[];
  expiradas: any[];
  inconclusivas: any[];
  erros: string[];
}

export interface ResultadoBusca {
  timestamp: string;
  parametros: any;
  total_encontradas: number;
  oportunidades: any[];
  referencias_historicas: Record<string, number>;
  erros: string[];
}

export interface LogExecucao {
  execucao_id: string;
  data_hora_inicio: string;
  data_hora_fim: string;
  fontes_consultadas: string[];
  ofertas_verificadas: number;
  ofertas_confirmadas: number;
  ofertas_expiradas: number;
  novas_oportunidades: number;
  falhas: string[];
  status_atualizacao_planilha: boolean;
  status_atualizacao_dashboard: boolean;
  status_envio_email: boolean;
}

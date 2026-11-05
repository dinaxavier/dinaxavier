import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  // A rotina copia preço e conexões de páginas públicas. Composer gasta menos token que o padrão.
  model: "composer-2.5",
});

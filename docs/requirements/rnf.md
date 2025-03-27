## Tabela de Requisitos Não Funcionais

| ID     | Descrição                                                                                           |
|--------|-----------------------------------------------------------------------------------------------------|
| RNF001 | Precisão mínima na localização: ±2 metros                                                           |
| RNF002 | Tempo máximo atualização das posições: até 5 segundos                                               |
| RNF003 | Vida útil mínima das baterias dos beacons: ≥2 anos                                                  |
| RNF004 | Escalabilidade para suportar até 500 beacons simultaneamente                                        |
| RNF004 | As comunicações entre dispositivos móveis, beacons e backend devem utilizar criptografia forte (TLS v1.3 ou superior) |
| RNF005 | Armazenar os dados criptografados utilizando AES-256                                                |
| RNF006 | Garantir autenticação multifatorial (MFA) para acessos administrativos e críticos                   |
| RNF007 | Anonimização ou pseudonimização dos dados pessoais coletados, garantindo privacidade por padrão ("Privacy by Design") |
| RNF008 | Realizar testes automatizados de segurança (análise estática, testes de penetração) antes de cada release em produção |
| RNF009 | O tempo máximo para detecção e notificação automática de incidentes ou tentativas suspeitas de acesso não autorizado ao sistema não pode ultrapassar 5 minutos após o evento |
| RNF010 | Os backups realizados devem ser armazenados em local seguro, isolado fisicamente do ambiente principal, com retenção mínima de 30 dias |


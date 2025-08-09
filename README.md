# Projeto-Final
# Sistema de Gestão de Doações para ONGs Locais

Projeto em Python que ajuda pequenas ONGs a registrar doações, gerenciar estoque, receber pedidos e distribuir itens de forma organizada.

Problema:
ONGs locais muitas vezes têm dificuldade em gerenciar doações (quem doou, o que foi doado, estoque por categoria), unir doadores a pedidos, evitar desperdício e distribuir itens para famílias ou projetos da maneira mais eficiente.

Inovação:
Sistema leve e local (CLI) que organiza doações, classifica por categoria, faz matching entre doações e pedidos, controla estoque, gerencia fila de pedidos (prioridade por urgência), registra histórico (pilha para desfazer operações) e permite busca rápida por doadores/itens (hash table). Útil para pequenas ONGs que não têm sistemas complexos.

## Funcionalidades
- Cadastro de doadores
- Registro de doações por categoria
- Cadastro de pedidos (necessidades) com prioridade (alta/média/baixa)
- Alocação automática de doações para pedidos compatíveis
- Pilha de histórico para desfazer alocações
- Consulta de estoque e relatórios básicos
- Salvamento simples em JSON (opcional)

## Estruturas de Dados Usadas
- **Hash Table (dict):** estoque por categoria ({categoria: lista_de_itens}) e busca rápida de doadores por ID.
- **Fila (deque):** fila de pedidos; prioridade implementada com três filas (alta, média, baixa) ou usar heapq para fila de prioridade.
- **Pilha (list):** histórico de alocações (para desfazer).
- **Listas:** listar doadores, pedidos e logs.
- **Classificação/Ordenação:** para organizar pedidos/relatórios

## Como executar
1. Tenha Python 3.8+ instalado.
2. Salve o arquivo `main.py`.
3. Rode no terminal:
```bash
python main.py
Siga o menu interativo para cadastrar doadores, registrar doações e pedidos.

Testes
Para rodar os testes (arquivo test_main.py):
(python -m unittest test_main.py)

bash
Copiar
Editar
python -m unittest test_main.py
Exemplo de execução
Ao iniciar, o sistema carrega dados de exemplo (doadores, doações e pedidos). Você pode cadastrar mais e testar as funções.





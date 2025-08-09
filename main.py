#!/usr/bin/env python3
# main.py
"""
Sistema de Gestão de Doações para ONGs Locais
Funcionalidades:
- Cadastrar doadores
- Registrar doações (itens, categoria)
- Registrar pedidos/necessidades (com prioridade)
- Alocar doações para pedidos automaticamente (matching por categoria e prioridade)
- Ver estoque por categoria
- Ver fila de pedidos por prioridade
- Desfazer última alocação
- Relatórios simples
"""

from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import datetime
import json
import uuid

# ------------------------------
# Modelos de dados simples
# ------------------------------
@dataclass
class Doador:
    id: str
    nome: str
    contato: str

@dataclass
class ItemDoacao:
    id: str
    nome: str
    categoria: str
    quantidade: int
    data: str  # ISO string

@dataclass
class Pedido:
    id: str
    solicitante: str
    categoria: str
    quantidade: int
    prioridade: str  # 'alta', 'media', 'baixa'
    data: str
    atendido: bool = False

@dataclass
class Alocacao:
    id: str
    item_id: str
    pedido_id: str
    quantidade: int
    data: str

# ------------------------------
# Estruturas do sistema
# ------------------------------

class SistemaDoacoes:
    def __init__(self):
        # Hash table de doadores: id -> Doador
        self.doadores: Dict[str, Doador] = {}
        # Estoque por categoria (hash table): categoria -> list[ItemDoacao]
        self.estoque: Dict[str, List[ItemDoacao]] = defaultdict(list)
        # Filas de pedidos por prioridade (alta, media, baixa)
        self.fila_alta = deque()
        self.fila_media = deque()
        self.fila_baixa = deque()
        # Map id -> Pedido
        self.pedidos: Dict[str, Pedido] = {}
        # Pilha de alocações para desfazer
        self.historico_alocacoes: List[Alocacao] = []
        # Log simples
        self.logs: List[str] = []

    # ---------- utilitários ----------
    def _now(self):
        return datetime.datetime.now().isoformat(timespec='seconds')

    def _novo_id(self):
        return str(uuid.uuid4())[:8]

    def log(self, texto: str):
        ts = self._now()
        entry = f"[{ts}] {texto}"
        self.logs.append(entry)
        print(entry)

    # ---------- doadores ----------
    def cadastrar_doador(self, nome: str, contato: str) -> Doador:
        id_ = self._novo_id()
        doador = Doador(id=id_, nome=nome, contato=contato)
        self.doadores[id_] = doador
        self.log(f"Doador cadastrado: {doador}")
        return doador

    # ---------- doações ----------
    def registrar_doacao(self, nome_item: str, categoria: str, quantidade: int, doador_id: Optional[str]=None) -> ItemDoacao:
        id_ = self._novo_id()
        item = ItemDoacao(id=id_, nome=nome_item, categoria=categoria, quantidade=quantidade, data=self._now())
        self.estoque[categoria].append(item)
        self.log(f"Doação registrada: {item} (doador={doador_id})")
        # após inserir no estoque, tenta alocar para pedidos pendentes dessa categoria
        self._tentar_alocar_para_pedidos(categoria)
        return item

    # ---------- pedidos ----------
    def cadastrar_pedido(self, solicitante: str, categoria: str, quantidade: int, prioridade: str='media') -> Pedido:
        id_ = self._novo_id()
        pedido = Pedido(id=id_, solicitante=solicitante, categoria=categoria, quantidade=quantidade, prioridade=prioridade, data=self._now())
        self.pedidos[id_] = pedido
        # inserir na fila adequada
        if prioridade == 'alta':
            self.fila_alta.append(id_)
        elif prioridade == 'media':
            self.fila_media.append(id_)
        else:
            self.fila_baixa.append(id_)
        self.log(f"Pedido cadastrado: {pedido}")
        # tentar alocar imediatamente se estoque tiver itens
        self._tentar_alocar_para_pedidos(categoria)
        return pedido

    # ---------- alocação (matching) ----------
    def _tentar_alocar_para_pedidos(self, categoria: str):
        """
        Tenta alocar estoque disponível dessa categoria para pedidos na ordem de prioridade.
        Repeats until não há estoque suficiente ou não há pedidos.
        """
        # função local para extrair próxima id de pedido seguindo prioridade
        def prox_pedido():
            for fila in (self.fila_alta, self.fila_media, self.fila_baixa):
                if fila:
                    return fila[0]  # peek
            return None

        while True:
            pedido_id = prox_pedido()
            if not pedido_id:
                break
            pedido = self.pedidos.get(pedido_id)
            if pedido is None or pedido.atendido:
                # remove se inválido/atendido
                for fila in (self.fila_alta, self.fila_media, self.fila_baixa):
                    if fila and fila[0] == pedido_id:
                        fila.popleft()
                continue
            if pedido.categoria != categoria:
                # próxima fila pode ter pedido de outra categoria; procurar pedido compatível
                found = None
                for fila in (self.fila_alta, self.fila_media, self.fila_baixa):
                    for pid in list(fila):
                        p = self.pedidos.get(pid)
                        if p and not p.atendido and p.categoria == categoria:
                            found = pid
                            break
                    if found:
                        # bring found to front by rotating
                        while fila[0] != found:
                            fila.rotate(-1)
                        pedido_id = found
                        pedido = self.pedidos[found]
                        break
                if not found:
                    break  # nenhum pedido dessa categoria
            # agora temos pedido compatível
            if not self.estoque[categoria]:
                break  # sem estoque
            # retirar do estoque o primeiro item (FIFO por doação)
            item = self.estoque[categoria][0]
            alocar_qtd = min(item.quantidade, pedido.quantidade)
            # registrar alocação
            aloc = Alocacao(id=self._novo_id(), item_id=item.id, pedido_id=pedido.id, quantidade=alocar_qtd, data=self._now())
            self.historico_alocacoes.append(aloc)
            self.log(f"Alocado {alocar_qtd}x '{item.nome}' (categoria {categoria}) -> pedido {pedido.id}")
            # ajustar quantidades
            item.quantidade -= alocar_qtd
            pedido.quantidade -= alocar_qtd
            if item.quantidade <= 0:
                # remover item do estoque
                self.estoque[categoria].pop(0)
            if pedido.quantidade <= 0:
                pedido.atendido = True
                # remover pedido da fila (popleft ou remove)
                for fila in (self.fila_alta, self.fila_media, self.fila_baixa):
                    if fila and fila[0] == pedido.id:
                        fila.popleft()
                        break
                    elif pedido.id in fila:
                        fila.remove(pedido.id)
                        break
            # continuar loop para tentar atender mais pedidos dessa categoria

    # ---------- desfazer última alocação ----------
    def desfazer_ultima_alocacao(self) -> bool:
        if not self.historico_alocacoes:
            self.log("Nenhuma alocação para desfazer.")
            return False
        aloc = self.historico_alocacoes.pop()
        # devolver quantidade ao estoque (achar categoria pelo item id)
        # procurar item original (pode ter sido removido se quantidade vir a zero) -> recriar se necessário
        # Simplicidade: registramos item_id -> categoria por varredura nas entradas de estoque históricas (não persistente)
        # Para esta versão básica, vamos recriar um item de reposição simples
        # (em implementação real, manter histórico de itens).
        # Recriar item simples:
        item_recriado = ItemDoacao(id=aloc.item_id, nome=f"Item_recuperado_{aloc.item_id}", categoria="Desconhecido", quantidade=aloc.quantidade, data=self._now())
        # regressar pedido para não-atendido (a menos que pedido original exista e ainda tenha qtd)
        pedido = self.pedidos.get(aloc.pedido_id)
        if pedido:
            # se já estava marcado atendido, revogamos o atendimento e reinserimos na fila conforme prioridade
            if pedido.atendido:
                pedido.atendido = False
                # reinserir no início da fila de sua prioridade
                if pedido.prioridade == 'alta':
                    self.fila_alta.appendleft(pedido.id)
                elif pedido.prioridade == 'media':
                    self.fila_media.appendleft(pedido.id)
                else:
                    self.fila_baixa.appendleft(pedido.id)
            pedido.quantidade += aloc.quantidade
        # adicionar de volta ao estoque em categoria "Desconhecido" (simplificação)
        self.estoque[item_recriado.categoria].append(item_recriado)
        self.log(f"Desfeita alocação {aloc.id} -> devolvido {aloc.quantidade} ao estoque (categoria 'Desconhecido').")
        return True

    # ---------- consultas / relatórios ----------
    def ver_estoque(self) -> Dict[str, Any]:
        resumo = {}
        for cat, itens in self.estoque.items():
            resumo[cat] = [{'id': it.id, 'nome': it.nome, 'qtd': it.quantidade, 'data': it.data} for it in itens]
        return resumo

    def listar_doadores(self) -> List[Dict[str, str]]:
        return [{'id': d.id, 'nome': d.nome, 'contato': d.contato} for d in self.doadores.values()]

    def listar_pedidos(self) -> List[Dict[str, Any]]:
        res = []
        for p in self.pedidos.values():
            res.append({'id': p.id, 'solicitante': p.solicitante, 'categoria': p.categoria, 'qtd': p.quantidade, 'prio': p.prioridade, 'atendido': p.atendido})
        return res

    def listar_historico(self) -> List[Dict[str, Any]]:
        return [{'id': a.id, 'item_id': a.item_id, 'pedido_id': a.pedido_id, 'qtd': a.quantidade, 'data': a.data} for a in self.historico_alocacoes]

    # ---------- persistência básica (opcional) ----------
    def salvar_json(self, caminho: str):
        obj = {
            'doadores': [d.__dict__ for d in self.doadores.values()],
            'estoque': {cat: [it.__dict__ for it in itens] for cat, itens in self.estoque.items()},
            'pedidos': [p.__dict__ for p in self.pedidos.values()],
            'historico': [a.__dict__ for a in self.historico_alocacoes],
            'logs': self.logs
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        self.log(f"Dados salvos em {caminho}")

    def carregar_json(self, caminho: str):
        with open(caminho, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        # parse simples (omitir reconversão completa para esta versão)
        self.log(f"Carregado arquivo {caminho}. (Parsing básico não implementado detalhadamente)")

# ------------------------------
# CLI simples
# ------------------------------
def menu():
    s = SistemaDoacoes()
    # dados de exemplo
    d1 = s.cadastrar_doador("Maria Silva", "maria@ex.com / (81)90000-0001")
    d2 = s.cadastrar_doador("João Pereira", "joao@ex.com / (81)90000-0002")
    s.registrar_doacao("Cesta básica pequena", "Alimentos", 10, d1.id)
    s.registrar_doacao("Agasalho adulto", "Roupas", 5, d2.id)
    s.registrar_doacao("Máscaras", "Higiene", 50, d2.id)
    s.cadastrar_pedido("Família A", "Alimentos", 3, prioridade='alta')
    s.cadastrar_pedido("Abrigo X", "Roupas", 4, prioridade='media')

    while True:
        print("\n=== SISTEMA DE DOAÇÕES ===")
        print("1. Cadastrar doador")
        print("2. Registrar doação")
        print("3. Cadastrar pedido")
        print("4. Ver estoque")
        print("5. Ver pedidos")
        print("6. Desfazer última alocação")
        print("7. Ver doadores")
        print("8. Salvar dados (JSON)")
        print("0. Sair")
        op = input("Escolha: ").strip()
        if op == '1':
            nome = input("Nome do doador: ").strip()
            contato = input("Contato: ").strip()
            s.cadastrar_doador(nome, contato)
        elif op == '2':
            nome_item = input("Nome do item: ").strip()
            categoria = input("Categoria: ").strip()
            qtd = int(input("Quantidade: ").strip())
            doador_id = input("ID do doador (opcional): ").strip() or None
            s.registrar_doacao(nome_item, categoria, qtd, doador_id)
        elif op == '3':
            sol = input("Solicitante (nome da família/entidade): ").strip()
            categoria = input("Categoria desejada: ").strip()
            qtd = int(input("Quantidade: ").strip())
            prio = input("Prioridade (alta/media/baixa) [media]: ").strip() or 'media'
            s.cadastrar_pedido(sol, categoria, qtd, prioridade=prio)
        elif op == '4':
            estoque = s.ver_estoque()
            print("\n--- Estoque por categoria ---")
            for cat, itens in estoque.items():
                print(f"Categoria: {cat}")
                for it in itens:
                    print(f"  - {it['nome']} (id:{it['id']}) qtt:{it['qtd']} doado em {it['data']}")
        elif op == '5':
            pedidos = s.listar_pedidos()
            print("\n--- Pedidos ---")
            for p in pedidos:
                print(f"ID:{p['id']} | {p['solicitante']} | cat:{p['categoria']} | qtd:{p['qtd']} | prio:{p['prio']} | atendido:{p['atendido']}")
        elif op == '6':
            s.desfazer_ultima_alocacao()
        elif op == '7':
            doadores = s.listar_doadores()
            print("\n--- Doadores ---")
            for d in doadores:
                print(f"{d['id']} | {d['nome']} | {d['contato']}")
        elif op == '8':
            caminho = input("Arquivo destino (ex: dados_doacoes.json): ").strip() or "dados_doacoes.json"
            s.salvar_json(caminho)
        elif op == '0':
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    menu()

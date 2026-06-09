"""
Cutoff Adjustment Algorithm (CA) — カットオフ調整アルゴリズム

対応するマッチング問題:
  - 一般上限制約付きの多対1マッチング（保育園マッチング等）

理論的背景:
  - カットオフ: 各受入者の「足切りライン」。市場価格に相当する。
  - 需要 D_r(p): カットオフ p のもとで受入者 r を希望する提案者の集合。
  - 調整関数 T: 需要が制約を超える受入者のカットオフを +1 する。
  - T の最小不動点（タルスキの不動点定理）= 提案者最適公平マッチング。
"""

from dataclasses import dataclass
from typing import Callable

# 一般上限制約の型: 提案者集合（0-indexed）→ 実行可能かどうか
Constraint = Callable[[frozenset[int]], bool]


def capacity_constraint(cap: int) -> Constraint:
    """定員制約: |I'| <= cap"""
    return lambda proposers: len(proposers) <= cap


def budget_constraint(costs: dict[int, float], budget: float) -> Constraint:
    """予算制約: Σ cost_i <= budget

    costs[提案者番号] = コスト のマッピング。
    """
    return lambda proposers: sum(costs.get(p, 0.0) for p in proposers) <= budget


def collision_avoidance_constraint(conflict_pairs: list[tuple[int, int]]) -> Constraint:
    """回避制約: conflict_pairs のいずれかのペアが同じ受入者に配属されないことを保証する（同一受入者に配属された場合に実行不可能と判定する）。

    conflict_pairs: 同じ受入先に配属してはならないペア
    """
    return lambda proposers: not any(a in proposers and b in proposers for a, b in conflict_pairs)


def combined_constraint(cap: int, conflict_pairs: list[tuple[int, int]]) -> Constraint:
    """定員制約と回避制約を組み合わせた複合制約。

    cap           : 受け入れ可能な最大人数
    conflict_pairs: 同じ受入者に配属してはならない 0-indexed 提案者ペアのリスト

    両条件を同時に満たす場合のみ実行可能と判定する:
      1. 提案者集合のサイズが cap 以下
      2. conflict_pairs のいずれのペアも同時に含まない
    """
    cap_c  = capacity_constraint(cap)
    proh_c = collision_avoidance_constraint(conflict_pairs)
    return lambda proposers: cap_c(proposers) and proh_c(proposers)


# ─────────────────────────────────────────────
# データクラス
# ─────────────────────────────────────────────

@dataclass
class Input:
    proposer_prefs: list[list[int]]        # 提案者 i の選好リスト（1-indexed 受入者番号）
    receiver_prefs: list[list[int]]        # 受入者 j の優先順位リスト（1-indexed 提案者番号）
    constraints:    list[Constraint]       # 受入者 j の実行可能性判定関数
    proposer_names: list[str] | None = None  # 提案者の個別名（省略時は "P1", "P2", ...）
    receiver_names: list[str] | None = None  # 受入者の個別名（省略時は "R1", "R2", ...）

    @property
    def n_proposers(self) -> int:
        return len(self.proposer_prefs)

    @property
    def n_receivers(self) -> int:
        return len(self.receiver_prefs)

    def p_name(self, i: int) -> str:
        return self.proposer_names[i] if self.proposer_names else f"P{i+1}"

    def r_name(self, j: int) -> str:
        return self.receiver_names[j] if self.receiver_names else f"R{j+1}"


@dataclass
class Result:
    proposer_match: list[int]        # proposer_match[i] = 受入者の0-index（-1 = 未配分）
    receiver_match: list[list[int]]  # receiver_match[j] = 提案者の0-indexリスト
    cutoff_profile: list[int]        # 最終カットオフプロファイル p*


# ─────────────────────────────────────────────
# メインアルゴリズム
# ─────────────────────────────────────────────

def cutoff_adjustment(data: Input, verbose: bool = True) -> Result:
    """
    CA アルゴリズムを実行し、提案者最適公平マッチングを返す。

    最小カットオフ p = (1, 1, ..., 1) から出発し、カットオフ調整関数 T の最小不動点 p* を求める。
    p* のもとで需要 D_r(p*) を確定させたものが提案者最適公平マッチングとなる。
    """
    P = data.n_proposers
    R = data.n_receivers

    # 受入者の優先順位表（priority_rank[r][p] = 受入者rにとっての提案者pの順位、0=最優先）
    priority_rank = _build_priority_rank(data.receiver_prefs, P)

    # 最小カットオフから開始（すべての提案者を対象に含める）
    cutoff = [1] * R

    if verbose:
        _print_preferences(data)
        print("=== CA アルゴリズム 開始 ===\n")
        print(f"  初期カットオフ: p = {cutoff}\n")

    iteration = 1
    while True:
        # 需要 D_r(p) を計算
        demand = _compute_demand(data, cutoff, priority_rank, P, R)

        # カットオフ調整関数 T(p) を計算
        new_cutoff = list(cutoff)
        is_fixed_point = True

        if verbose:
            print(f"--- 反復 {iteration} ---")

        for r in range(R):
            feasible = data.constraints[r](frozenset(demand[r]))
            if not feasible:
                new_cutoff[r] = cutoff[r] + 1
                is_fixed_point = False
            if verbose:
                demand_str = ", ".join(data.p_name(p) for p in sorted(demand[r]))
                mark = "✅" if feasible else "❌"
                print(f"  {data.r_name(r)}: p={cutoff[r]}, D=[{demand_str}] {mark}")

        if verbose and not is_fixed_point:
            print(f"  → p: {cutoff} → {new_cutoff}\n")

        if is_fixed_point:
            if verbose:
                print(f"\n  不動点到達: p* = {cutoff}\n")
            break

        cutoff = new_cutoff
        iteration += 1

        # 安全装置: すべての受入者でカットオフが P+1 を超えたら終了
        if all(c > P for c in cutoff):
            break

    # 最終マッチングを確定
    demand = _compute_demand(data, cutoff, priority_rank, P, R)
    proposer_match = [-1] * P
    receiver_match = [[] for _ in range(R)]

    for r in range(R):
        receiver_match[r] = sorted(demand[r])
        for p in demand[r]:
            proposer_match[p] = r

    result = Result(
        proposer_match=proposer_match,
        receiver_match=receiver_match,
        cutoff_profile=cutoff,
    )

    print("=== CA アルゴリズム 終了 ===\n")
    _print_result(result, data)
    return result


# ─────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────

def _compute_demand(
    data: Input,
    cutoff: list[int],
    priority_rank: list[list[int]],
    P: int,
    R: int,
) -> list[list[int]]:
    """
    カットオフ p のもとで各受入者の需要 D_r(p) を計算する。

    D_r(p) = {p | p が受入者rの足切りを通過し、rを受け入れ可能で、rが最も好きな足切り通過受入者}

    足切り通過の条件（cutoff[r]=1 で全員通過、cutoff[r]=P+1 で全員除外）
    - priority_rank[r][p] <= P - cutoff[r]
    """
    # 各受入者の足切り通過者集合を求める
    qualified: list[set[int]] = [set() for _ in range(R)]
    for r in range(R):
        threshold = P - cutoff[r]   # この値以下の順位を持つ提案者が通過
        for p in range(P):
            if priority_rank[r][p] <= threshold:
                qualified[r].add(p)

    # 各提案者が最も好きな「足切り通過受入者」を求め、そこに振り分ける
    demand: list[list[int]] = [[] for _ in range(R)]
    for p in range(P):
        for r_1indexed in data.proposer_prefs[p]:
            r = r_1indexed - 1
            if p in qualified[r]:
                demand[r].append(p)
                break  # 最も好きな通過受入者に割り当て、残りはスキップ

    return demand


def _build_priority_rank(
    receiver_prefs: list[list[int]],
    n_proposers: int,
) -> list[list[int]]:
    """優先順位リスト（1-indexed）を順位表（0-indexed）に変換する。

    rank[r][p] = 受入者rにとっての提案者pの順位（0=最優先）
    """
    rank = [[n_proposers] * n_proposers for _ in range(len(receiver_prefs))]
    for r, row in enumerate(receiver_prefs):
        for rank_pos, proposer_1indexed in enumerate(row):
            rank[r][proposer_1indexed - 1] = rank_pos
    return rank


def _print_preferences(data: Input) -> None:
    print("【提案者の選好】")
    for p, pref in enumerate(data.proposer_prefs):
        row = " > ".join(data.r_name(x - 1) for x in pref)
        print(f"  {data.p_name(p)}: {row}")
    print()
    print("【受入者の優先順位】")
    for r, pri in enumerate(data.receiver_prefs):
        row = " > ".join(data.p_name(x - 1) for x in pri)
        print(f"  {data.r_name(r)}: {row}")
    print()


def _print_result(result: Result, data: Input) -> None:
    print("【マッチング結果】")
    for p, r in enumerate(result.proposer_match):
        partner = data.r_name(r) if r != -1 else "未配分"
        print(f"  {data.p_name(p)}: {partner}")
    print()
    print(f"【最終カットオフ】 p* = {result.cutoff_profile}")
    print()

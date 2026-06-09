"""
Deferred Acceptance Algorithm — 受入保留方式

対応するマッチング問題:
  - マッチング（大学入試、病院・研修医配属など）
  - 各受入者は定員（capacities）まで複数の提案者を受け入れられる
"""

from dataclasses import dataclass


# ─────────────────────────────────────────────
# データクラス
# ─────────────────────────────────────────────

@dataclass
class Input:
    proposer_prefs: list[list[int]]        # 提案者 i の選好リスト
    receiver_prefs: list[list[int]]        # 受入者 j の選好リスト
    capacities:     list[int]              # 受入者 j の定員
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
    proposer_match: list[int]        # 応募側のマッチング結果
    receiver_match: list[list[int]]  # 受入側のマッチング結果


# ─────────────────────────────────────────────
# メインアルゴリズム
# ─────────────────────────────────────────────

def deferred_acceptance(data: Input, verbose: bool = True) -> Result:
    """
    DA アルゴリズムを実行し、提案者最適な安定マッチングを返す。
    """
    P = data.n_proposers
    R = data.n_receivers

    # 受入者の優先順位表（r_rank[j][i] = 受入者jにとっての提案者iの順位）
    r_rank = _build_rank(data.receiver_prefs, P)

    proposer_match: list[int]        = [-1] * P   # 応募側のマッチング結果
    receiver_match: list[list[int]]  = [[] for _ in range(R)] # 受入側のマッチング結果
    next_proposal:  list[int]        = [0]  * P   # 次に応募する志望順位
    free: set[int] = set(range(P))                # 未マッチの提案者

    if verbose:
        _print_preferences(data)
        print("=== DA アルゴリズム 開始 ===\n")

    step = 1
    while free:
        if verbose:
            print(f"--- ステップ {step} ---")

        # (a) 提案フェーズ
        proposals: dict[int, list[int]] = {r: [] for r in range(R)}
        for p in list(free):
            if next_proposal[p] >= len(data.proposer_prefs[p]):
                if verbose:
                    print(f"  {data.p_name(p)}: 全受入者に提案済み → 未マッチ")
                continue
            r = data.proposer_prefs[p][next_proposal[p]] - 1
            next_proposal[p] += 1
            proposals[r].append(p)
            if verbose:
                print(f"  {data.p_name(p)} → {data.r_name(r)} に提案")
        free.clear()

        # (b) 受入フェーズ
        if verbose:
            print(f"\n  【受入フェーズ】")

        for r in range(R):
            if not proposals[r]:
                continue

            # 現在の仮受入者 + 新しい提案者を優先順位順にソート
            candidates = sorted(
                receiver_match[r] + proposals[r],
                key=lambda p: r_rank[r][p],
            )
            keep     = candidates[:data.capacities[r]]   # 定員分だけキープ
            overflow = candidates[data.capacities[r]:]   # 溢れた提案者

            # 仮受入を更新（弾かれた提案者は解放）
            for p in receiver_match[r]:
                if p not in keep:
                    proposer_match[p] = -1
            receiver_match[r] = list(keep)
            for p in keep:
                proposer_match[p] = r

            # 溢れた提案者を即時拒否
            rejected_by_cap = []
            for p in overflow:
                free.add(p)
                rejected_by_cap.append(p)

            if verbose:
                keep_str = ", ".join(data.p_name(p) for p in keep)
                print(f"    {data.r_name(r)}（定員{data.capacities[r]}）: キープ=[{keep_str}]")
                if rejected_by_cap:
                    rej_str = ", ".join(data.p_name(p) for p in rejected_by_cap)
                    print(f"      → 定員（{data.capacities[r]}人）により拒否: [{rej_str}]")

        if verbose:
            print()
        step += 1

    result = Result(
        proposer_match=proposer_match,
        receiver_match=receiver_match,
    )

    print("=== DA アルゴリズム 終了 ===\n")
    _print_result(result, data)
    return result


# ─────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────

def _build_rank(prefs: list[list[int]], n: int) -> list[list[int]]:
    """選好リスト（1-indexed）を順位表（0-indexed）に変換する。"""
    rank = [[n] * n for _ in range(len(prefs))]
    for i, row in enumerate(prefs):
        for r, target in enumerate(row):
            rank[i][target - 1] = r
    return rank


def _print_preferences(data: Input) -> None:
    print("【提案者の選好】")
    for i, pref in enumerate(data.proposer_prefs):
        row = " > ".join(data.r_name(x - 1) for x in pref)
        print(f"  {data.p_name(i)}: {row}")
    print()
    print("【受入者の選好と定員】")
    for j, pref in enumerate(data.receiver_prefs):
        row = " > ".join(data.p_name(x - 1) for x in pref)
        print(f"  {data.r_name(j)}（定員{data.capacities[j]}）: {row}")
    print()


def _print_result(result: Result, data: Input) -> None:
    print("【マッチング結果】")
    for i, r in enumerate(result.proposer_match):
        partner = data.r_name(r) if r != -1 else "未マッチ"
        print(f"  {data.p_name(i)}: {partner}")
    print()

"""
Flexible Deferred Acceptance (FDA) Algorithm — 柔軟な受入保留方式

対応するマッチング問題:
  - 地域上限制約付きの多対1マッチング（日本の研修医マッチング等）
"""

from dataclasses import dataclass


# ─────────────────────────────────────────────
# データクラス
# ─────────────────────────────────────────────

@dataclass
class Input:
    proposer_prefs: list[list[int]]        # 提案者 i の選好リスト
    receiver_prefs: list[list[int]]        # 受入者 j の選好リスト
    capacities:     list[int]              # 受入者 j の定員（レギュラーフェーズの閾値）
    max_caps:         list[int]            # 受入者 j の設置上限（物理的な最大）
    regions:          list[int]            # 受入者 j が属する地域
    regional_caps:    list[int]            # 地域 r の上限
    nomination_order: list[int]            # 待機リストフェーズでの受入者の指名順序
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

def flexible_deferred_acceptance(data: Input, verbose: bool = True) -> Result:
    """
    FDA アルゴリズムを実行し、弱安定マッチングを返す。
    """
    P = data.n_proposers
    R = data.n_receivers

    # 受入者の優先順位表（r_rank[j][i] = 受入者jにとっての提案者iの順位）
    r_rank = _build_rank(data.receiver_prefs, P)

    proposer_match: list[int]        = [-1] * P   # 応募側のマッチング結果
    receiver_match: list[list[int]]  = [[] for _ in range(R)] # 受入側のマッチング結果
    wait_list:      list[list[int]]  = [[] for _ in range(R)]
    next_proposal:  list[int]        = [0]  * P   # 次に応募する志望順位
    free: set[int] = set(range(P))                # 未マッチの提案者

    if verbose:
        _print_preferences(data)
        print("=== FDA アルゴリズム 開始 ===\n")

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

        # (b-1) レギュラーフェーズ
        if verbose:
            print(f"\n  【レギュラーフェーズ】")

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

            # 溢れた提案者を待機リストへ追加（設置上限の範囲内）
            rejected_by_cap = []
            for p in overflow:
                if len(receiver_match[r]) + len(wait_list[r]) < data.max_caps[r]:
                    wait_list[r].append(p)   # 即時拒否せず待機リストへ
                else:
                    free.add(p)              # 設置上限も超える場合のみ拒否
                    rejected_by_cap.append(p)

            if verbose:
                keep_str = ", ".join(data.p_name(p) for p in keep)
                wait_str = ", ".join(data.p_name(p) for p in wait_list[r])
                print(f"    {data.r_name(r)}: キープ=[{keep_str}]  待機=[{wait_str}]")
                if rejected_by_cap:
                    rej_str = ", ".join(data.p_name(p) for p in rejected_by_cap)
                    print(f"      → 設置上限（{data.max_caps[r]}人）により拒否: [{rej_str}]")

        # (b-2) 待機リストフェーズ
        if verbose:
            print(f"\n  【待機リストフェーズ】")

        # 地域ごとの現在マッチ数を集計
        regional_count = [0] * len(data.regional_caps)
        for r, matched in enumerate(receiver_match):
            for p in matched:
                regional_count[data.regions[r]] += 1

        for r in data.nomination_order:
            region = data.regions[r]
            release_reason = None
            while wait_list[r]:
                # 地域上限チェック
                if regional_count[region] >= data.regional_caps[region]:
                    release_reason = f"地域上限（{data.regional_caps[region]}人）により拒否"
                    if verbose:
                        print(f"    {data.r_name(r)}: を受入なし")
                    break
                # 設置上限チェック
                if len(receiver_match[r]) >= data.max_caps[r]:
                    release_reason = f"設置上限（{data.max_caps[r]}人）により拒否"
                    if verbose:
                        print(f"    {data.r_name(r)}: を受入なし")
                    break
                # 待機リストから最優先の提案者を1人受入
                best = min(wait_list[r], key=lambda p: r_rank[r][p])
                wait_list[r].remove(best)
                receiver_match[r].append(best)
                proposer_match[best] = r
                regional_count[region] += 1
                if verbose:
                    print(f"    {data.r_name(r)}: {data.p_name(best)} を受入"
                          f"（地域{region}: {regional_count[region]}"
                          f"/{data.regional_caps[region]}）")

            # 上限を超えて受入拒否された参加者の情報を出力
            if verbose and wait_list[r] and release_reason:
                rel_str = ", ".join(data.p_name(p) for p in wait_list[r])
                print(f"      → {release_reason}: [{rel_str}]")

            # 残った待機リストの提案者は次のステップへ
            for p in wait_list[r]:
                free.add(p)
            wait_list[r] = []

        if verbose:
            print()
        step += 1

    result = Result(
        proposer_match=proposer_match,
        receiver_match=receiver_match,
    )

    print("=== FDA アルゴリズム 終了 ===\n")
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
        print(f"  {data.r_name(j)}（定員:{data.capacities[j]}, 設置上限:{data.max_caps[j]}）: {row}")
    print()
    print("【地域情報】")
    for j, region in enumerate(data.regions):
        print(f"  {data.r_name(j)}: 地域{region}（地域上限: {data.regional_caps[region]}）")
    print(f"  指名順序: {' → '.join(data.r_name(r) for r in data.nomination_order)}")
    print()


def _print_result(result: Result, data: Input) -> None:
    print("【マッチング結果】")
    for i, r in enumerate(result.proposer_match):
        partner = data.r_name(r) if r != -1 else "未マッチ"
        print(f"  {data.p_name(i)}: {partner}")
    print()

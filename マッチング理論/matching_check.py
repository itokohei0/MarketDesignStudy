"""
matching_check.py — マッチング結果の性質検証モジュール

検証する性質:
  1. 個人合理性 （Individual Rationality）
  2. ブロッキングペアなし （No Blocking Pair）   ← 公平性 ∧ 効率性 ⟺ ブロッキングペアなし
  3. 安定性     （Stability）= 個人合理性 + ブロッキングペアなし
  4. 弱安定性   （Weak Stability）= 個人合理性 + 強ブロッキングペアなし
  5. 公平性     （Fairness）= 正当な羨望を持つ提案者がいない
  6. 効率性     （Efficiency）= 無駄がない（空き定員があるのに入学できない提案者がいない）

入力形式（全関数共通）:
  proposer_prefs : 提案者 i の選好リスト（受入者番号, 1-indexed）
  receiver_prefs : 受入者 j の優先順位リスト（提案者番号, 1-indexed）
  proposer_match : proposer_match[i] = マッチした受入者の 0-index（-1 = 未マッチ）
  receiver_match : receiver_match[j] = マッチした提案者の 0-indexリスト
  capacities     : 受入者 j の定員（省略時は全員 1 とみなす）
"""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CheckResult:
    """性質検証の結果を保持するデータクラス"""
    passed: bool
    violations: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed

    def __str__(self) -> str:
        status = "✅ 成立" if self.passed else "❌ 不成立"
        if self.violations:
            detail = "\n".join(f"  - {v}" for v in self.violations)
            return f"{status}\n{detail}"
        return status


def _build_rank(prefs: list[list[int]], n: int) -> list[list[int]]:
    """選好リスト（1-indexed）を順位表（0-indexed）に変換する。

    rank[i][j] = エージェント i にとっての相手 j の順位（0 が最優先）。
    選好リストに含まれない相手の順位は n（受け入れ不可能、最低値）とする。
    """
    rank = [[n] * n for _ in range(len(prefs))]
    for i, row in enumerate(prefs):
        for r, target in enumerate(row):
            rank[i][target - 1] = r
    return rank


def _prefers(rank: list[list[int]], agent: int, a: int, b: int, unmatched_rank: int) -> bool:
    """agent が b よりも a を好むかどうかを返す（順位が小さいほど好ましい）。

    a または b が -1（未マッチ）の場合は unmatched_rank を使う。
    """
    rank_a = rank[agent][a] if a != -1 else unmatched_rank
    rank_b = rank[agent][b] if b != -1 else unmatched_rank
    return rank_a < rank_b

def _pn(names: list[str] | None, i: int) -> str:
    """提案者 i の名前を返す（names が None なら "P{i+1}"）。"""
    return names[i] if names else f"P{i+1}"


def _rn(names: list[str] | None, j: int) -> str:
    """受入者 j の名前を返す（names が None なら "R{j+1}"）。"""
    return names[j] if names else f"R{j+1}"


def check_individual_rationality(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    個人合理性（Individual Rationality）を検証する。

    定義:
      各エージェントが自分のマッチ相手を「受け入れ可能」と判断していること。
      選好リストに含まれない相手とのマッチングは受け入れ不可能とみなし、違反とする。

      - 提案者側: proposer_match[p] が proposer_prefs[p] に含まれている
      - 受入者側: receiver_match[r] の各提案者が receiver_prefs[r] に含まれている

    計算量: O(P + R)
    """
    violations: list[str] = []

    # 提案者側のチェック
    for p, r in enumerate(proposer_match):
        if r == -1:
            continue  # 未マッチは個人合理性に反しない
        if (r + 1) not in proposer_prefs[p]:
            violations.append(
                f"{_pn(proposer_names,p)} が受け入れ不可能な {_rn(receiver_names,r)} とマッチしている"
            )

    # 受入者側のチェック
    for r, matched in enumerate(receiver_match):
        acceptable = set(receiver_prefs[r])
        for p in matched:
            if (p + 1) not in acceptable:
                violations.append(
                    f"{_rn(receiver_names,r)} が受け入れ不可能な {_pn(proposer_names,p)} とマッチしている"
                )

    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【個人合理性】{result}")
    return result


def check_no_blocking_pair(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    capacities: list[int] | None = None,
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    ブロッキングペアが存在しないことを検証する（安定性の核心条件）。

    定義:
      ブロッキングペア (p, r) が存在しないこと。

    ブロッキングペアの条件（以下を両方満たすペア）:
      (1) 提案者 p が受け入れ可能な受入者 r を現在の相手よりも厳密に好む
      (2) 受入者 r が提案者 p を受け入れ可能かつ以下のいずれかを満たす:
          (a) r の定員に空きがある  （|μ(r)| < q_r）
          (b) r が p を現在の最悪マッチ相手より厳密に好む

    計算量: O(P × R)
    """
    P = len(proposer_match)
    R = len(receiver_match)

    if capacities is None:
        capacities = [1] * R

    p_rank = _build_rank(proposer_prefs, R)
    r_rank = _build_rank(receiver_prefs, P)

    violations: list[str] = []

    for p in range(P):
        current_r = proposer_match[p]

        for r in range(R):
            # r が p の選好リストにない → p は r を受け入れ不可能
            if (r + 1) not in proposer_prefs[p]:
                continue

            # 条件 (1): p が r を現在の相手より厳密に好む
            if not _prefers(p_rank, p, r, current_r, R):
                continue

            # p が r の優先順位リストにない → r は p を受け入れ不可能
            if (p + 1) not in receiver_prefs[r]:
                continue

            # 条件 (2a): r の定員に空きがある
            if len(receiver_match[r]) < capacities[r]:
                violations.append(
                    f"ブロッキングペア ({_pn(proposer_names,p)}, {_rn(receiver_names,r)}): "
                    f"{_pn(proposer_names,p)} は {_rn(receiver_names,r)} を希望し、{_rn(receiver_names,r)} には空き定員がある"
                )
                continue

            # 条件 (2b): r が p を現在の最悪マッチ相手より厳密に好む
            worst_q = max(receiver_match[r], key=lambda q: r_rank[r][q])
            if _prefers(r_rank, r, p, worst_q, P):
                violations.append(
                    f"ブロッキングペア ({_pn(proposer_names,p)}, {_rn(receiver_names,r)}): "
                    f"{_pn(proposer_names,p)} は {_rn(receiver_names,r)} を希望し、"
                    f"{_rn(receiver_names,r)} は最悪マッチ {_pn(proposer_names,worst_q)} より {_pn(proposer_names,p)} を優先する"
                )

    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【ブロッキングペアなし】{result}")
    return result


def check_stability(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    capacities: list[int] | None = None,
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    安定性（Stability）を検証する。

    定義:
      安定性 = 個人合理性（IR） + ブロッキングペアなし

    計算量: O(P + R) + O(P × R)
    """
    ir = check_individual_rationality(
        proposer_prefs, receiver_prefs,
        proposer_match, receiver_match,
        proposer_names, receiver_names, verbose=False,
    )
    nbp = check_no_blocking_pair(
        proposer_prefs, receiver_prefs,
        proposer_match, receiver_match,
        capacities, proposer_names, receiver_names, verbose=False,
    )

    violations = ir.violations + nbp.violations
    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【安定性】{result}")
    return result


def check_weak_stability(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    capacities: list[int] | None = None,
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    弱安定性（Weak Stability）を検証する。

    定義:
      弱安定性 = 個人合理性（IR） + 強ブロッキングペアなし

    強ブロッキングペアの条件:
      (1) 提案者 p が受入者 r を現在の相手よりも厳密に好む
      (2) 受入者 r が定員満杯かつ p を現在の最悪マッチ相手より厳密に好む
          ※ 空き定員のみでは強ブロッキングとみなさない（← 安定性との最大の違い）

    安定性との違い:
      安定性  : 空き定員があれば受け入れ可能な p との (p, r) ペアをブロッキングとする
      弱安定性: 定員満杯で双方が厳密に改善できるペアのみをブロッキングとする

    計算量: O(P + R) + O(P × R)
    """
    P = len(proposer_match)
    R = len(receiver_match)

    if capacities is None:
        capacities = [1] * R

    ir = check_individual_rationality(
        proposer_prefs, receiver_prefs,
        proposer_match, receiver_match,
        proposer_names, receiver_names, verbose=False,
    )

    p_rank = _build_rank(proposer_prefs, R)
    r_rank = _build_rank(receiver_prefs, P)

    violations: list[str] = list(ir.violations)

    for p in range(P):
        current_r = proposer_match[p]

        for r in range(R):
            # r が p の選好リストにない → p は r を受け入れ不可能
            if (r + 1) not in proposer_prefs[p]:
                continue

            # 条件 (1): p が r を厳密に好む
            if not _prefers(p_rank, p, r, current_r, R):
                continue

            # p が r の優先順位リストにない → r は p を受け入れ不可能
            if (p + 1) not in receiver_prefs[r]:
                continue

            # 空き定員がある場合は強ブロッキングとしない（弱安定性の核心）
            if len(receiver_match[r]) < capacities[r]:
                continue  # ← 安定性の場合はブロッキングペアが成立する

            # 条件 (2): 定員満杯かつ r が p を最悪マッチ相手より厳密に好む
            worst_q = max(receiver_match[r], key=lambda q: r_rank[r][q])
            if _prefers(r_rank, r, p, worst_q, P):
                violations.append(
                    f"強ブロッキングペア ({_pn(proposer_names,p)}, {_rn(receiver_names,r)}): "
                    f"{_pn(proposer_names,p)} は {_rn(receiver_names,r)} を希望し（定員満杯）、"
                    f"{_rn(receiver_names,r)} は最悪マッチ {_pn(proposer_names,worst_q)} より {_pn(proposer_names,p)} を厳密に優先する"
                )

    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【弱安定性】{result}")
    return result


def check_fairness(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    公平性（Fairness）= 正当な羨望を持つ提案者がいないことを検証する。

    定義:
      以下の2条件を同時に満たす提案者 i と提案者 j のペアが存在しない時、マッチング μ は公平である。
        ・(1) μ(j) ≻_i μ(i) ：提案者 i が、提案者 j のマッチング相手 s=μ(j) を自分の現在の相手 μ(i) より好む
        ・(2) i ≻_s j       ：受入者 s=μ(j) も、j より i を優先する
      上記を同時に満たす i を「受入者 j に対し正当な羨望を持つ提案者」と呼ぶ。

    計算量: O(P² × R) → 提案者数が多い場合は注意
    """
    P = len(proposer_match)
    R = len(receiver_match)

    p_rank = _build_rank(proposer_prefs, R)
    r_rank = _build_rank(receiver_prefs, P)

    violations: list[str] = []

    for i in range(P):
        current_i = proposer_match[i]  # i の現在の受入者（-1 = 未マッチ）

        for j in range(P):
            if i == j:
                continue
            s = proposer_match[j]   # j の配属先受入者（0-index）
            if s == -1:
                continue  # j が未マッチなら羨望の対象にならない

            # i が s を選好リストに持たない → i は s を受け入れ不可能 → 羨望の対象外
            if (s + 1) not in proposer_prefs[i]:
                continue

            # 条件 (1): i が s=μ(j) を μ(i) より好む
            if not _prefers(p_rank, i, s, current_i, R):
                continue

            # 条件 (2): 受入者 s が j より i を優先する（i ≻_s j）
            # ※ i が s の優先順位リストにない（受け入れ不可能）なら条件不成立
            if (i + 1) not in receiver_prefs[s]:
                continue
            if _prefers(r_rank, s, i, j, P):
                current_label = "未マッチ" if current_i == -1 else _rn(receiver_names,current_i)
                violations.append(
                    f"正当な羨望: {_pn(proposer_names,i)}（現在: {current_label}）が {_pn(proposer_names,j)}（→{_rn(receiver_names,s)}）を羨む"
                    f" — {_rn(receiver_names,s)} も {_pn(proposer_names,j)} より {_pn(proposer_names,i)} を優先"
                )

    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【公平性（正当な羨望なし）】{result}")
    return result


def check_efficiency(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    capacities: list[int] | None = None,
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> CheckResult:
    """
    効率性（Efficiency）= 無駄のなさを検証する。

    定義:
      次の条件を満たす提案者 i と受入者 s のペア (i, s) ∈ I × S が存在しない時、マッチング μ には無駄がない（効率的である）。
        ・(1) s ≻_i μ(i)        ：提案者 i が受入者 s を現在の相手より好む
        ・(2) μ(s) ∪ {i} ∈ F_s ：受入者 s の現在のマッチングに i を加えても実行可能（= 定員に空きがある）
      「受入側の定員に空きがあるにも関わらず応募を希望する提案者を受け入れられない事態が生じないこと」を要求する。

    計算量: O(P × R)
    """
    P = len(proposer_match)
    R = len(receiver_match)

    if capacities is None:
        capacities = [1] * R

    p_rank = _build_rank(proposer_prefs, R)

    violations: list[str] = []

    for i in range(P):
        current_i = proposer_match[i]

        for r in range(R):
            if proposer_match[i] == r:
                continue  # 既に r にマッチ済み

            # 条件 (1): i が r を μ(i) より好む（i が r を選好リストに持つ）
            if (r + 1) not in proposer_prefs[i]:
                continue  # i は r を受け入れ不可能
            if not _prefers(p_rank, i, r, current_i, R):
                continue

            # 受入者 r が i を受け入れ可能かどうか（r の優先順位リストに i が含まれる）
            if (i + 1) not in receiver_prefs[r]:
                continue  # r は i を受け入れ不可能

            # 条件 (2): μ(r) ∪ {i} ∈ F_r（定員に空きがある）
            if len(receiver_match[r]) < capacities[r]:
                current_label = "未マッチ" if current_i == -1 else _rn(receiver_names,current_i)
                violations.append(
                    f"効率性違反（無駄な空き）: {_rn(receiver_names,r)} に空き定員があるが"
                    f" {_pn(proposer_names,i)}（現在: {current_label}）が入れない"
                )

    result = CheckResult(passed=not violations, violations=violations)
    if verbose:
        print(f"【効率性（無駄なし）】{result}")
    return result


# ─────────────────────────────────────────────
# 一括チェック
# ─────────────────────────────────────────────

def check_all(
    proposer_prefs: list[list[int]],
    receiver_prefs: list[list[int]],
    proposer_match: list[int],
    receiver_match: list[list[int]],
    capacities: list[int] | None = None,
    proposer_names: list[str] | None = None,
    receiver_names: list[str] | None = None,
    verbose: bool = True,
) -> dict[str, CheckResult]:
    """
    マッチング結果の性質検証を一括で行う。
    """
    if verbose:
        print("=" * 44)
        print("  マッチング結果の性質検証")
        print("=" * 44)

    results = {
        # 個人合理性
        "individual_rationality": check_individual_rationality(
            proposer_prefs, receiver_prefs,
            proposer_match, receiver_match,
            proposer_names, receiver_names, verbose,
        ),
        # ブロッキングペアが存在しない
        "no_blocking_pair": check_no_blocking_pair(
            proposer_prefs, receiver_prefs,
            proposer_match, receiver_match,
            capacities, proposer_names, receiver_names, verbose,
        ),
        # 安定性
        "stability": check_stability(
            proposer_prefs, receiver_prefs,
            proposer_match, receiver_match,
            capacities, proposer_names, receiver_names, verbose,
        ),
        # 弱安定性
        "weak_stability": check_weak_stability(
            proposer_prefs, receiver_prefs,
            proposer_match, receiver_match,
            capacities, proposer_names, receiver_names, verbose,
        ),
        # 効率性
        "efficiency": check_efficiency(
            proposer_prefs, receiver_prefs,
            proposer_match, receiver_match,
            capacities, proposer_names, receiver_names, verbose,
        ),
    }

    if verbose:
        print("=" * 44)

    return results

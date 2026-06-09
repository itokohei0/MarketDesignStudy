"""
CA アルゴリズムの実行例

ca_algorithm.py のアルゴリズムを6パターンで動作確認する。
  例1: 学生と大学のマッチング（定員制約のみ — DA と同じ結果になることを確認）
  例2: 予算制約（保育園マッチング）
  例3: 回避制約（同一課への配属禁止ペア）
"""

from ca_algorithm import (
    Input,
    capacity_constraint,
    budget_constraint,
    collision_avoidance_constraint,
    cutoff_adjustment,
)
from matching_check import check_all, check_individual_rationality, check_fairness, check_stability, check_weak_stability


def example1(verbose=True):
    """例1: 学生と大学のマッチング（定員制約のみ）— DA と同じ結果になることを確認"""
    print("=" * 65)
    print("例1: 学生と大学の CA マッチング（定員制約のみ）")
    print("=" * 65)
    print()

    data = Input(
        proposer_prefs=[
            [1, 2, 3, 4],   # 田中: 東工大 > 早稲田 > 慶應 > 明治
            [1, 3, 2, 4],   # 鈴木: 東工大 > 慶應 > 早稲田 > 明治
            [2, 1, 3, 4],   # 佐藤: 早稲田 > 東工大 > 慶應 > 明治
            [3, 2, 1, 4],   # 高橋: 慶應 > 早稲田 > 東工大 > 明治
        ],
        receiver_prefs=[
            [2, 1, 3, 4],   # 東工大: 鈴木 > 田中 > 佐藤 > 高橋
            [1, 2, 4, 3],   # 早稲田: 田中 > 鈴木 > 高橋 > 佐藤
            [4, 3, 1, 2],   # 慶應:   高橋 > 佐藤 > 田中 > 鈴木
            [3, 4, 2, 1],   # 明治:   佐藤 > 高橋 > 鈴木 > 田中
        ],
        constraints=[
            capacity_constraint(1),
            capacity_constraint(1),
            capacity_constraint(1),
            capacity_constraint(1),
        ],
        proposer_names=["田中", "鈴木", "佐藤", "高橋"],
        receiver_names=["東工大", "早稲田", "慶應", "明治"],
    )

    result = cutoff_adjustment(data)
    check_all(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=[1, 1, 1, 1],
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )


def example2(verbose=True):
    """
    例2: 予算制約による保育園マッチング
    ※ CA は定員制約ではなく予算制約を直接扱えるため、「誰を入れるか」という構成を考慮した最適配分を行う
    """
    print("=" * 65)
    print("例2: 予算制約による保育園マッチング")
    print("=" * 65)
    print()

    child_names = ["みらい", "はるか", "ゆうと", "みさき", "けんた"]
    # コスト（CA アルゴリズムは 0-indexed 提案者番号を使うため 0-indexed で定義）
    costs = {
        0: 1/3,  # みらい（0歳）
        1: 1/3,  # はるか（0歳）
        2: 1/6,  # ゆうと（1歳）
        3: 1/6,  # みさき（1歳）
        4: 1/6,  # けんた（1歳）
    }

    print("【児童と年齢コスト】")
    for i, name in enumerate(child_names):
        print(f"  {name}: コスト {costs[i]:.3f}")
    print(f"  保育士1人の予算: 1.0人分")
    print()

    data = Input(
        proposer_prefs=[[1]] * 5,              # 全員がひまわり保育園のみ
        receiver_prefs=[[1, 2, 3, 4, 5]],      # ひまわり保育園: みらい>はるか>...>けんた
        constraints=[budget_constraint(costs, budget=1.0)],
        proposer_names=child_names,
        receiver_names=["ひまわり保育園"],
    )

    result = cutoff_adjustment(data, verbose=verbose)

    # 予算制約は Callable であり整数の capacities で表現できないため、
    # 個人合理性・公平性のみ check 関数で検証し、
    # 効率性（無駄なし）は制約関数で直接確認する。
    check_individual_rationality(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_fairness(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    print()

    # 入園した児童のコスト合計を表示
    matched = sorted(result.receiver_match[0])
    total_cost = sum(costs[p] for p in matched)
    names_str = "、".join(data.p_name(p) for p in matched)
    print(f"【配分結果】{names_str}（コスト合計: {total_cost:.3f} / 予算: 1.0）")
    print()


def example3(verbose=True):
    """例3: 回避制約（同一クラスへの配属禁止ペア4組）"""
    print("=" * 65)
    print("例3: 回避制約（同一クラスへの配属禁止ペア）")
    print("=" * 65)
    print()

    # 同一クラスに配属してはならないペア（0-indexed）
    conflict_pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]

    print("【配属禁止ペア】（同じクラスに配属してはならない）")
    pair_labels = [("学生1", "学生2"), ("学生3", "学生4"),
                   ("学生5", "学生6"), ("学生7", "学生8")]
    reasons = ["前校のトラブル", "競合プロジェクト", "学業上の利益相反", "親族関係"]
    for (a, b), reason in zip(pair_labels, reasons):
        print(f"  ({a}, {b}) : {reason}")
    print()

    data = Input(
        proposer_prefs=[
            [1, 2, 3, 4],   # 学生1: クラスA > クラスB > クラスC > クラスD
            [1, 3, 2, 4],   # 学生2: クラスA > クラスC > クラスB > クラスD  ← 学生1と第1志望が衝突
            [2, 1, 3, 4],   # 学生3: クラスB > クラスA > クラスC > クラスD
            [2, 4, 3, 1],   # 学生4: クラスB > クラスD > クラスC > クラスA  ← 学生3と第1志望が衝突
            [3, 2, 1, 4],   # 学生5: クラスC > クラスB > クラスA > クラスD
            [3, 4, 2, 1],   # 学生6: クラスC > クラスD > クラスB > クラスA  ← 学生5と第1志望が衝突
            [4, 1, 3, 2],   # 学生7: クラスD > クラスA > クラスC > クラスB
            [4, 2, 1, 3],   # 学生8: クラスD > クラスB > クラスA > クラスC  ← 学生7と第1志望が衝突
        ],
        receiver_prefs=[
            [1, 3, 5, 7, 6, 4, 8, 2],  # クラスA: 学生2 が最下位（禁止ペアの下位方）
            [3, 1, 5, 7, 6, 2, 8, 4],  # クラスB: 学生4 が最下位
            [5, 3, 1, 7, 2, 8, 4, 6],  # クラスC: 学生6 が最下位
            [7, 5, 3, 1, 4, 2, 6, 8],  # クラスD: 学生8 が最下位
        ],
        constraints=[
            collision_avoidance_constraint(conflict_pairs),  # クラスA
            collision_avoidance_constraint(conflict_pairs),  # クラスB
            collision_avoidance_constraint(conflict_pairs),  # クラスC
            collision_avoidance_constraint(conflict_pairs),  # クラスD
        ],
        proposer_names=["学生1","学生2","学生3","学生4","学生5","学生6","学生7","学生8"],
        receiver_names=["クラスA","クラスB","クラスC","クラスD"],
    )

    result = cutoff_adjustment(data, verbose=verbose)

    check_individual_rationality(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_weak_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_fairness(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    print()

    print("【配属禁止ペアの分離確認】")
    pair_separated = True
    for a, b in conflict_pairs:
        ra = result.proposer_match[a]
        rb = result.proposer_match[b]
        same = (ra == rb and ra != -1)
        status = "❌ 同一クラスに配属（制約違反）" if same else "✅ 別々のクラスに配属"
        print(f"  ({data.p_name(a)}, {data.p_name(b)}): "
              f"{data.r_name(ra) if ra != -1 else '未配分'} / "
              f"{data.r_name(rb) if rb != -1 else '未配分'} → {status}")
        if same:
            pair_separated = False
    print()


if __name__ == "__main__":
    example1()
    print("\n\n")
    example2()
    print("\n\n")
    example3()

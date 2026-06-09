"""
FDA アルゴリズムの実行例

fda_algorithm.py のアルゴリズムを3パターンで動作確認する。
  例1: 安定性✅ かつ 弱安定性✅（地域上限が非binding → 全員マッチ）
  例2: 安定性❌ かつ 弱安定性✅（地域上限が binding → 未マッチ発生）
  例3: 安定性❌ かつ 弱安定性✅（地域β上限が binding → 基幹・製品開発それぞれ1ペアずつブロッキングペア発生）
"""

from fda_algorithm import Input, flexible_deferred_acceptance
from matching_check import check_individual_rationality, check_stability, check_weak_stability

def example1(verbose=True):
    """地域上限が考慮不要の研修医マッチング（安定性✅ かつ 弱安定性✅）"""
    print("=" * 65)
    print("例1: 地域上限が考慮不要の研修医マッチング（安定性✅ かつ 弱安定性✅）")
    print("=" * 65)
    print()

    resident_names = ["花田", "石橋", "坂本", "岡田", "池田",
                      "丸山", "福島", "今井", "谷口", "村山"]

    data = Input(
        proposer_prefs=[[1]] * 3 + [[2]] * 7,   # 花田〜坂本→北部、岡田〜村山→南部のみ
        receiver_prefs=[
            list(range(1, 11)),   # 北部医療センター: 花田>石橋>...>村山
            list(range(1, 11)),   # 南部医療センター: 花田>石橋>...>村山
        ],
        capacities=[3, 5],        # 目標定員
        max_caps=[10, 10],        # 設置上限
        regions=[0, 0],           # 両病院とも地域α
        regional_caps=[10],       # 地域αの上限
        nomination_order=[0, 1],
        proposer_names=resident_names,
        receiver_names=["北部医療センター", "南部医療センター"],
    )

    result = flexible_deferred_acceptance(data, verbose=verbose)
    check_individual_rationality(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_weak_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )


def example2(verbose=True):
    """地域上限付き研修医マッチング（安定性❌ かつ 弱安定性✅）"""
    print("=" * 65)
    print("例2: 地域上限付き研修医マッチング（安定性❌ かつ 弱安定性✅）")
    print("=" * 65)
    print()

    data = Input(
        proposer_prefs=[
            [1, 2],   # 西村: 東病院 > 西病院
            [1, 2],   # 川上: 東病院 > 西病院
            [2, 1],   # 北川: 西病院 > 東病院
            [2, 1],   # 南田: 西病院 > 東病院
        ],
        receiver_prefs=[
            [1, 2, 3, 4],   # 東病院: 西村 > 川上 > 北川 > 南田
            [3, 4, 1, 2],   # 西病院: 北川 > 南田 > 西村 > 川上
        ],
        capacities=[1, 1],     # 目標定員（レギュラーフェーズの閾値）
        max_caps=[3, 3],       # 設置上限（物理的な最大）
        regions=[0, 0],        # 両病院とも地域α
        regional_caps=[2],     # 地域α全体の上限 = 2人
        nomination_order=[0, 1],
        proposer_names=["西村", "川上", "北川", "南田"],
        receiver_names=["東病院", "西病院"],
    )

    result = flexible_deferred_acceptance(data, verbose=verbose)
    print("─" * 65)
    print("【性質の検証】capacities = max_caps（設置上限）で判定")
    print("─" * 65)
    check_individual_rationality(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_weak_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )


def example3(verbose=True):
    """部署配属18社員・6部署・3地域（基幹・製品開発それぞれ安定性❌ かつ 弱安定性✅）"""
    print("=" * 65)
    print("例3: 部署配属18社員・6部署・3地域")
    print("     （基幹・製品開発それぞれ1ペアずつブロッキングペア発生）")
    print("=" * 65)
    print()

    employee_names = [
        "田中", "鈴木", "佐藤",           # 1-3:  営業1課志望（地域α）
        "高橋", "渡辺", "伊藤", "山本", "中村",  # 4-8:  基幹システム課志望（地域β）
        "加藤", "吉田", "山田", "佐々木", "松本", # 9-13: 製品開発課志望（地域β）
        "井上", "木村", "中山",           # 14-16: 経営企画課志望（地域γ）
        "林",                            # 17:   商品企画課志望（地域γ）
        "清水",                          # 18:   マーケティング課志望（地域γ）
    ]

    data = Input(
        proposer_prefs=(
            [[1, 2, 3, 4, 5, 6]] * 3 +   # 田中・鈴木・佐藤: 営業1課 > 基幹 > 製品開発 > 経営企画 > 商品企画 > マーケ
            [[2, 5, 6, 4, 3, 1]] * 5 +   # 高橋〜中村:   基幹 > 商品企画 > マーケ > 経営企画 > 製品開発 > 営業1課
            [[3, 5, 6, 4, 2, 1]] * 5 +   # 加藤〜松本:   製品開発 > 商品企画 > マーケ > 経営企画 > 基幹 > 営業1課
            [[4, 5, 6, 1, 2, 3]] * 3 +   # 井上・木村・中山: 経営企画 > 商品企画 > マーケ > 営業1課 > 基幹 > 製品開発
            [[5, 6, 4, 1, 2, 3]] * 1 +   # 林:          商品企画 > マーケ > 経営企画 > 営業1課 > 基幹 > 製品開発
            [[6, 5, 4, 1, 2, 3]] * 1     # 清水:        マーケ > 商品企画 > 経営企画 > 営業1課 > 基幹 > 製品開発
        ),
        receiver_prefs=[
            # 営業1課: 田中 > 鈴木 > 佐藤 > 以降
            list(range(1, 19)),
            # 基幹システム課: 高橋 > 渡辺 > 伊藤 > 山本 > 中村 > 以降
            [4, 5, 6, 7, 8, 1, 2, 3, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            # 製品開発課: 加藤 > 吉田 > 山田 > 佐々木 > 松本 > 高橋 > 以降
            [9, 10, 11, 12, 13, 4, 5, 6, 7, 8, 1, 2, 3, 14, 15, 16, 17, 18],
            # 経営企画課: 井上 > 木村 > 中山 > 以降
            [14, 15, 16, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18],
            # 商品企画課: 林 > 以降
            [17, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18],
            # マーケティング課: 清水 > 以降
            [18, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        ],
        capacities=[2, 4, 4, 2, 1, 1],   # 目標上限（β合計=8=地域上限、レギュラーフェーズで満杯）
        max_caps=[3, 5, 5, 3, 2, 2],      # 設置上限（設置可能な最大）
        regions=[0, 1, 1, 2, 2, 2],       # 地域α=0, β=1, γ=2
        regional_caps=[3, 8, 7],           # 各地域の上限
        nomination_order=[0, 1, 2, 3, 4, 5],  # 対称的な指名順序
        proposer_names=employee_names,
        receiver_names=["営業1課", "基幹システム課", "製品開発課", "経営企画課", "商品企画課", "マーケティング課"],
    )

    result = flexible_deferred_acceptance(data, verbose=verbose)
    print("─" * 65)
    print("【性質の検証】capacities = max_caps（設置上限）で判定")
    print("─" * 65)
    check_individual_rationality(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )
    check_weak_stability(
        data.proposer_prefs, data.receiver_prefs,
        result.proposer_match, result.receiver_match,
        capacities=data.max_caps,
        proposer_names=data.proposer_names,
        receiver_names=data.receiver_names,
    )


if __name__ == "__main__":
    example1()
    print("\n\n")
    example2()
    print("\n\n")
    example3()

"""
DA アルゴリズムの実行例

da_many_to_one.py のアルゴリズムを3パターンで動作確認する。
  例1: 学生と大学の1対1マッチング
  例2: 研修医と病院の多対1マッチング
  例3: 研修医と病院の多対1マッチング（未マッチあり）
  例4: 学生と大学の多対1マッチング（受入者側に未充足が発生するケース）
"""

from da_algorithm import Input, deferred_acceptance
from matching_check import check_individual_rationality, check_stability

def example1(verbose=True):
    """学生と大学の1対1マッチング"""
    print("=" * 55)
    print("例1: 学生と大学の1対1マッチング")
    print("=" * 55)
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
        capacities=[1,1,1,1],
        proposer_names=["田中", "鈴木", "佐藤", "高橋"],
        receiver_names=["東工大", "早稲田", "慶應", "明治"],
    )

    result = deferred_acceptance(data, verbose=verbose)
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

def example2(verbose=True):
    """研修医と病院の多対1マッチング"""
    print("=" * 60)
    print("例2: 研修医と病院の多対1マッチング")
    print("=" * 60)
    print()

    data = Input(
        proposer_prefs=[
            [1, 2, 3],   # 田村: 東大病院 > 慶應病院 > 聖路加
            [1, 3, 2],   # 中川: 東大病院 > 聖路加 > 慶應病院
            [1, 2, 3],   # 浜田: 東大病院 > 慶應病院 > 聖路加
            [3, 2, 1],   # 安田: 聖路加 > 慶應病院 > 東大病院
            [3, 1, 2],   # 橋本: 聖路加 > 東大病院 > 慶應病院
            [2, 3, 1],   # 本田: 慶應病院 > 聖路加 > 東大病院
        ],
        receiver_prefs=[
            [1, 2, 3, 4, 5, 6],   # 東大病院（定員2）: 田村>中川>浜田>安田>橋本>本田
            [3, 1, 6, 2, 5, 4],   # 慶應病院（定員2）: 浜田>田村>本田>中川>橋本>安田
            [5, 6, 4, 3, 2, 1],   # 聖路加（定員2）  : 橋本>本田>安田>浜田>中川>田村
        ],
        capacities=[2, 2, 2],
        proposer_names=["田村", "中川", "浜田", "安田", "橋本", "本田"],
        receiver_names=["東大病院", "慶應病院", "聖路加"],
    )

    result = deferred_acceptance(data, verbose=verbose)
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


def example3(verbose=True):
    """研修医と病院の多対1マッチング（未マッチあり）"""
    print("=" * 60)
    print("例3: 研修医と病院の多対1マッチング（未マッチあり）")
    print("=" * 60)
    print()

    resident_names = ["花田", "石橋", "坂本", "岡田", "池田",
                      "丸山", "福島", "今井", "谷口", "村山"]

    data = Input(
        proposer_prefs=[[1]] * 3 + [[2]] * 7,   # 花田〜坂本→北部、岡田〜村山→南部のみ
        receiver_prefs=[
            list(range(1, 11)),   # 北部医療センター: 花田>石橋>...>村山
            list(range(1, 11)),   # 南部医療センター: 花田>石橋>...>村山
        ],
        capacities=[3, 5],
        proposer_names=resident_names,
        receiver_names=["北部医療センター", "南部医療センター"],
    )

    result = deferred_acceptance(data, verbose=verbose)
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


def example4(verbose=True):
    """学生と大学の多対1マッチング（受入者側に未充足が発生するケース）"""
    print("=" * 60)
    print("例4: 学生と大学の多対1マッチング（受入者側に未充足が発生するケース）")
    print("=" * 60)
    print()

    data = Input(
        proposer_prefs=[
            [1, 2, 3],   # 田中: 東工大 > 早稲田 > 慶應
            [1, 2, 3],   # 鈴木: 東工大 > 早稲田 > 慶應
            [2, 1, 3],   # 佐藤: 早稲田 > 東工大 > 慶應
            [2, 1, 3],   # 高橋: 早稲田 > 東工大 > 慶應
        ],
        receiver_prefs=[
            [1, 2, 3, 4],   # 東工大（定員2）: 田中>鈴木>佐藤>高橋
            [3, 4, 1, 2],   # 早稲田（定員2）: 佐藤>高橋>田中>鈴木
            [1, 2, 3, 4],   # 慶應（定員2）  : 田中>鈴木>佐藤>高橋
        ],
        capacities=[2, 2, 2],
        proposer_names=["田中", "鈴木", "佐藤", "高橋"],
        receiver_names=["東工大", "早稲田", "慶應"],
    )

    result = deferred_acceptance(data, verbose=verbose)
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


if __name__ == "__main__":
    example1(verbose=True)
    print("\n\n")
    example2(verbose=True)
    print("\n\n")
    example3(verbose=True)
    print("\n\n")
    example4(verbose=True)

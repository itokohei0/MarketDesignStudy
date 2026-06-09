"""
ボーエンメカニズム（Bowen Mechanism）

費用を均等割（q_i = 1/n）で分担し、各プレイヤーが望む供給水準を表明させ、
コンドルセ方式（多数決）で供給量を決定するメカニズム。
全員の選好が単峰的なとき、中位投票者定理より中央値 G_m がコンドルセ勝者となる。

満たす性質:
  ボーエン＝サミュエルソン条件 : × （限界便益が正規分布の場合のみ成立）
  予算均衡条件                 : ⚫
  個人合理性                   : × （均等負担が不利なプレイヤーが生じる場合あり）
  耐戦略性                     : ⚫ （選好が単峰的なとき成立）

前提:
  便益関数  v_i(G) = G - 0.5 * a_i * G^2
  供給費用  c(G)   = G
"""

import statistics

# ===== 定数 =====
SEPARATOR = "=" * 50


# ===== 入力設定 =====
def input_data() -> tuple:
    """パラメータを設定する"""
    N = 3                          # プレイヤー数
    a = [1, 2, 3]                 # 便益パラメータ a_i（a_3が大きく，強制負担でIR違反が生じる）
    return N, a


# ===== 供給水準の決定 =====
def determine_supply(N: int, a: list) -> tuple:
    """コンドルセ方式（中位投票者定理）により公共財の供給水準を決定する

    各プレイヤーの最適化条件 v'_i(G_i) = q_i より G_i = (1 - q_i) / a_i
    中位投票者定理: 供給水準の中央値がコンドルセ勝者となる
    """
    q = [1 / N] * N                        # 均等割の費用負担割合
    g_reported = [(1 - q[i]) / a[i] for i in range(N)]  # 各プレイヤーの表明水準
    G = statistics.median(g_reported)      # 多数決（中央値）で決定
    return G, q, g_reported


# ===== 費用負担の計算 =====
def calculate_burden(N: int, q: list, G: float) -> list:
    """各プレイヤーの費用負担額 x_i = q_i * c(G) = q_i * G を計算する"""
    return [q[i] * G for i in range(N)]


# ===== 利得の計算 =====
def calculate_payoff(N: int, a: list, G: float, x: list) -> list:
    """各プレイヤーの利得 u_i = v_i(G) - x_i を計算する
    v_i(G) = G - 0.5 * a_i * G^2
    """
    return [G - 0.5 * a[i] * G**2 - x[i] for i in range(N)]


# ===== 条件の確認 =====
def check_conditions(N: int, G: float, burden: list, payoff: list,
                     endowment: list, c_G: float) -> None:
    """予算均衡条件と個人合理性を数値的に確認する"""
    budget_ok = abs(sum(burden) - c_G) < 1e-9
    ir_flags  = [payoff[i] >= endowment[i] for i in range(N)]
    ir_ok     = all(ir_flags)

    print("【条件の確認】")
    print(f"  予算均衡条件 : {'⚫ 成立' if budget_ok else '× 不成立'}"
          f"  （Σx_i = {sum(burden):.4f}, c(G) = {c_G:.4f}）")
    print(f"  個人合理性   : {'⚫ 成立' if ir_ok else '× 不成立'}"
          f"  ※パラメータによっては不成立になる場合があります")
    for i in range(N):
        sign = "≥" if ir_flags[i] else "<"
        mark = "⚫" if ir_flags[i] else "×"
        print(f"    プレイヤー {i+1}: u_{i+1} = {payoff[i]:.4f} "
              f"{sign} 参加前 = {endowment[i]:.4f}  {mark}")


# ===== メイン =====
def main() -> None:
    print(SEPARATOR)
    print("  ボーエンメカニズム（Bowen Mechanism）")
    print(SEPARATOR + "\n")

    # 1. 入力情報
    N, a = input_data()
    print("【入力情報】")
    print(f"  プレイヤー数 N      : {N}")
    print(f"  便益パラメータ a_i  : {a}")
    print(f"  費用負担割合 q_i    : 1/N = {1/N:.4f}（全員均等割）")
    print(f"  便益関数 v_i(G)     : G - 0.5 * a_i * G^2")
    print(f"  供給費用 c(G)       : G\n")

    # 2. 公共財供給水準の決定（コンドルセ方式）
    G, q, g_reported = determine_supply(N, a)
    print("【公共財供給水準】  G_i = (1 - q_i) / a_i  →  G* = 中央値")
    for i in range(N):
        print(f"  プレイヤー {i+1} の表明水準 G_{i+1} = {g_reported[i]:.4f}")
    print(f"  G* = 中央値（コンドルセ勝者） = {G:.4f}\n")

    # 3. 費用負担の計算
    burden = calculate_burden(N, q, G)
    print("【費用負担】  x_i = q_i × G* = (1/N) × G*")
    for i in range(N):
        print(f"  プレイヤー {i+1}: x_{i+1} = {burden[i]:.4f}")
    print()

    # 4. 利得の計算
    payoff = calculate_payoff(N, a, G, burden)
    print("【利得】  u_i = v_i(G*) - x_i")
    for i in range(N):
        vi = G - 0.5 * a[i] * G**2
        print(f"  プレイヤー {i+1}: v_{i+1}(G*) = {vi:.4f},  u_{i+1} = {payoff[i]:.4f}")
    print()

    # 5. 条件の確認（参加前の利得 = G=0 時の便益 = 0）
    check_conditions(N, G, burden, payoff, endowment=[0.0]*N, c_G=G)


if __name__ == "__main__":
    main()

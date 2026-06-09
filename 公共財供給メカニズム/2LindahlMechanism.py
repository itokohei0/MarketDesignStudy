"""
リンダールメカニズム（Lindahl Mechanism）

政府が各プレイヤーに個別の費用負担割合 q_i を提示し、
全員が同一の供給水準 G_i に合意するまで繰り返し調整するメカニズム。

満たす性質:
  ボーエン＝サミュエルソン条件 : ⚫
  予算均衡条件                 : ⚫
  個人合理性                   : ⚫
  耐戦略性                     : × （虚偽申告で利得を改善できる）

前提:
  便益関数  v_i(G) = G - 0.5 * a_i * G^2
  供給費用  c(G)   = G
"""

# ===== 定数 =====
SEPARATOR = "=" * 50


# ===== 入力設定 =====
def input_data() -> tuple:
    """パラメータを設定する"""
    N = 3                          # プレイヤー数
    a = [1, 2, 10]                  # 便益パラメータ a_i（値が大きいほど限界便益が急減）
    return N, a


# ===== 供給水準の決定 =====
def determine_supply(N: int, a: list) -> float:
    """リンダール均衡における公共財の供給水準 G* = (N-1) / Σa_i を計算する"""
    return (N - 1) / sum(a)


# ===== 費用負担の計算 =====
def calculate_burden(N: int, a: list, G: float) -> tuple:
    """各プレイヤーの費用負担額 x_i = q_i * c(G) = q_i * G を計算する
    リンダール均衡の費用負担割合: q_i* = 1 - a_i * G*
    """
    q = [1 - a[i] * G for i in range(N)]
    x = [q[i] * G for i in range(N)]
    return x, q


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
    print(f"  個人合理性   : {'⚫ 成立' if ir_ok else '× 不成立'}")
    for i in range(N):
        sign = "≥" if ir_flags[i] else "<"
        mark = "⚫" if ir_flags[i] else "×"
        print(f"    プレイヤー {i+1}: u_{i+1} = {payoff[i]:.4f} "
              f"{sign} 参加前 = {endowment[i]:.4f}  {mark}")


# ===== メイン =====
def main() -> None:
    print(SEPARATOR)
    print("  リンダールメカニズム（Lindahl Mechanism）")
    print(SEPARATOR + "\n")

    # 1. 入力情報
    N, a = input_data()
    print("【入力情報】")
    print(f"  プレイヤー数 N      : {N}")
    print(f"  便益パラメータ a_i  : {a}")
    print(f"  便益関数 v_i(G)     : G - 0.5 * a_i * G^2")
    print(f"  供給費用 c(G)       : G\n")

    # 2. 公共財供給水準の決定（リンダール均衡）
    G = determine_supply(N, a)
    print("【公共財供給水準】")
    print(f"  G* = (N-1) / Σa_i = {N-1} / {sum(a)} = {G:.4f}\n")

    # 3. 費用負担の計算
    burden, q = calculate_burden(N, a, G)
    print("【費用負担】  x_i = q_i* × G*  （q_i* = 1 - a_i × G*）")
    for i in range(N):
        print(f"  プレイヤー {i+1}: q_{i+1}* = {q[i]:.4f},  x_{i+1} = {burden[i]:.4f}")
    print(f"  費用負担割合の合計 Σq_i = {sum(q):.4f}  （≒ 1 を確認）\n")

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

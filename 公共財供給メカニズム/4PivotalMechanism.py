"""
ピボタルメカニズム（Pivotal Mechanism）

グローブスメカニズムの特殊ケース（h(w_{-i}) = 0）。
公共財を「供給する/しない」の2択として、表明評価値の合計で可否を決定し、
自分の申告が決定を左右した（ピボタルになった）プレイヤーのみにクラーク税を課す。

満たす性質:
  ボーエン＝サミュエルソン条件 : ⚫
  予算均衡条件                 : × （クラーク税の余剰が生じる）
  個人合理性                   : × （クラーク税により損をするプレイヤーが生じる）
  耐戦略性                     : ⚫ （正直申告が支配戦略）
"""

# ===== 定数 =====
SEPARATOR = "=" * 50


# ===== 入力設定 =====
def input_data() -> tuple:
    """パラメータを設定する"""
    N   = 3                        # プレイヤー数
    x_p = [2, 2, 2]                # 各プレイヤーの私的財（初期保有）
    v   = [3, 1, -2]               # 真の便益（負値 = 公共財供給に反対）
    w   = [3, 1, -2]               # 表明する評価値（ここでは真実申告を仮定）
    return N, x_p, v, w


# ===== 供給水準の決定 =====
def determine_supply(w: list) -> int:
    """表明評価値の合計 ≥ 0 なら G=1（供給）、< 0 なら G=0（非供給）"""
    return 1 if sum(w) >= 0 else 0


# ===== 費用負担の計算 =====
def calculate_burden(N: int, w: list) -> list:
    """クラーク税（ピボタル税）t_i を計算する

    自分の申告が供給の可否を変えた場合のみ |Σ_{j≠i} w_j| を課税する。
    条件: (Σw_i) × (Σ_{j≠i} w_j) < 0  ← 自分の参加で符号が逆転する場合
    """
    total = sum(w)
    t = [0] * N
    for i in range(N):
        sum_without_i = total - w[i]
        if total * sum_without_i < 0:      # 自分がピボタル（結果を左右する）
            t[i] = abs(sum_without_i)
    return t


# ===== 利得の計算 =====
def calculate_payoff(N: int, x_p: list, v: list, G: int, t: list) -> list:
    """各プレイヤーの利得 u_i = x_p_i + v_i * G - t_i を計算する"""
    return [x_p[i] + v[i] * G - t[i] for i in range(N)]


# ===== 条件の確認 =====
def check_conditions(N: int, G: float, burden: list, payoff: list,
                     endowment: list, c_G: float) -> None:
    """予算均衡条件と個人合理性を数値的に確認する"""
    budget_ok = abs(sum(burden) - c_G) < 1e-9
    ir_flags  = [payoff[i] >= endowment[i] for i in range(N)]
    ir_ok     = all(ir_flags)

    print("【条件の確認】")
    print(f"  予算均衡条件 : {'⚫ 成立' if budget_ok else '× 不成立'}"
          f"  （Σt_i = {sum(burden):.4f}, c(G) = {c_G:.4f}）")
    print(f"  個人合理性   : {'⚫ 成立' if ir_ok else '× 不成立'}")
    for i in range(N):
        sign = "≥" if ir_flags[i] else "<"
        mark = "⚫" if ir_flags[i] else "×"
        print(f"    プレイヤー {i+1}: u_{i+1} = {payoff[i]:.4f} "
              f"{sign} x_p_{i+1} = {endowment[i]:.4f}  {mark}")


# ===== メイン =====
def main() -> None:
    print(SEPARATOR)
    print("  ピボタルメカニズム（Pivotal Mechanism）")
    print(SEPARATOR + "\n")

    # 1. 入力情報
    N, x_p, v, w = input_data()
    print("【入力情報】")
    print(f"  プレイヤー数 N      : {N}")
    print(f"  私的財（初期保有）  : {x_p}")
    print(f"  真の便益 v_i        : {v}")
    print(f"  表明する評価値 w_i  : {w}  （真実申告: w_i = v_i）\n")

    # 2. 公共財供給水準の決定
    G = determine_supply(w)
    print("【公共財供給水準】")
    print(f"  Σw_i = {sum(w)}  →  {'G = 1（供給）' if G == 1 else 'G = 0（非供給）'}\n")

    # 3. 費用負担の計算（クラーク税）
    burden = calculate_burden(N, w)
    print("【費用負担（クラーク税）】")
    for i in range(N):
        s_i = sum(w) - w[i]
        pivotal = (sum(w) * s_i < 0)
        label = "ピボタル → 課税" if pivotal else "非ピボタル → 非課税"
        print(f"  プレイヤー {i+1}: Σ_{{j≠{i+1}}} w_j = {s_i:+d},  "
              f"t_{i+1} = {burden[i]}  （{label}）")
    print()

    # 4. 利得の計算
    payoff = calculate_payoff(N, x_p, v, G, burden)
    print("【利得】  u_i = x_p_i + v_i × G - t_i")
    for i in range(N):
        print(f"  プレイヤー {i+1}: u_{i+1} = {x_p[i]} + {v[i]}×{G} - {burden[i]} = {payoff[i]:.4f}")
    print()

    # 5. 条件の確認（c(G) = 0 に基準化、初期保有 x_p_i と比較）
    check_conditions(N, G, burden, payoff, endowment=list(map(float, x_p)), c_G=0.0)


if __name__ == "__main__":
    main()

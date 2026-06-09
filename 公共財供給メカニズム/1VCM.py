"""
公共財自発的供給メカニズム（VCM: Voluntary Contribution Mechanism）

各プレイヤーが自発的に公共財へ貢献額を決定するメカニズム。
ただ乗り問題の検証に広く用いられる経済実験の枠組み。

満たす性質:
  ボーエン＝サミュエルソン条件 : ×
  予算均衡条件                 : ⚫
  個人合理性                   : × （貢献額が便益を上回るプレイヤーが生じる）
  耐戦略性                     : × （貢献額ゼロが個人的な支配戦略）
"""

# ===== 定数 =====
SEPARATOR = "=" * 50


# ===== 入力設定 =====
def input_data() -> tuple:
    """パラメータを設定する"""
    N = 3                          # プレイヤー数
    w = [3, 3, 3]                  # 各プレイヤーの初期保有
    x = [0, 1, 2]                  # 各プレイヤーの貢献額（公共財への拠出）
    alpha = 0.6                    # 限界便益 α（1/N < α < 1 を満たす）
    return N, w, x, alpha


# ===== 供給水準の決定 =====
def determine_supply(x: list) -> float:
    """公共財の供給水準 G = Σx_i を決定する（予算均衡条件: c(G) = G）"""
    return sum(x)


# ===== 費用負担の計算 =====
def calculate_burden(x: list) -> list:
    """各プレイヤーの費用負担額（＝貢献額）を返す"""
    return list(x)


# ===== 利得の計算 =====
def calculate_payoff(N: int, w: list, x: list, alpha: float, G: float) -> list:
    """各プレイヤーの利得 u_i = w_i - x_i + α*G を計算する"""
    return [w[i] - x[i] + alpha * G for i in range(N)]


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
              f"{sign} w_{i+1} = {endowment[i]:.4f}  {mark}")


# ===== メイン =====
def main() -> None:
    print(SEPARATOR)
    print("  公共財自発的供給メカニズム（VCM）")
    print(SEPARATOR + "\n")

    # 1. 入力情報
    N, w, x, alpha = input_data()
    print("【入力情報】")
    print(f"  プレイヤー数 N  : {N}")
    print(f"  初期保有 w_i    : {w}")
    print(f"  貢献額 x_i      : {x}")
    print(f"  限界便益 α      : {alpha}  （1/N={1/N:.2f} < α < 1）\n")

    # 2. 公共財供給水準の決定
    G = determine_supply(x)
    print("【公共財供給水準】")
    print(f"  G = Σx_i = {G}\n")

    # 3. 費用負担（VCMでは貢献額がそのまま費用負担）
    burden = calculate_burden(x)
    print("【費用負担（貢献額）】")
    for i in range(N):
        print(f"  プレイヤー {i+1}: x_{i+1} = {burden[i]}")
    print()

    # 4. 利得の計算
    payoff = calculate_payoff(N, w, x, alpha, G)
    print("【利得】  u_i = w_i - x_i + α*G  （α*G = {:.4f}）".format(alpha * G))
    for i in range(N):
        print(f"  プレイヤー {i+1}: u_{i+1} = {w[i]} - {x[i]} + {alpha*G:.4f} = {payoff[i]:.4f}")
    print()

    # 5. 条件の確認
    check_conditions(N, G, burden, payoff, endowment=w, c_G=G)


if __name__ == "__main__":
    main()

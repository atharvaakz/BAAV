"""Three- and five-step DuPont decomposition."""


def dupont_3(net_income, revenue, total_assets, equity):
    margin = net_income / revenue
    turnover = revenue / total_assets
    leverage = total_assets / equity
    return {"net_margin": margin, "asset_turnover": turnover,
            "equity_multiplier": leverage, "roe": margin * turnover * leverage}


def dupont_5(net_income, pretax_income, ebit, revenue, total_assets, equity):
    tax_burden = net_income / pretax_income
    interest_burden = pretax_income / ebit
    ebit_margin = ebit / revenue
    turnover = revenue / total_assets
    leverage = total_assets / equity
    return {"tax_burden": tax_burden, "interest_burden": interest_burden,
            "ebit_margin": ebit_margin, "asset_turnover": turnover,
            "equity_multiplier": leverage,
            "roe": tax_burden * interest_burden * ebit_margin * turnover * leverage}

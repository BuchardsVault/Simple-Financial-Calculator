from flask import Flask, render_template, redirect, url_for, request
from math import pow
import calendar, datetime

app = Flask(__name__)

# -------------------
# Helpers
# -------------------
def pmt(P, annual_rate, n_months):
    r = annual_rate / 100 / 12
    if r == 0:
        return P / n_months
    return P * r / (1 - pow(1 + r, -n_months))

def retirement(cb, cs, cp, mp, ml, ar, sg, inf, ca, ra, le):
    """
    Simulate year‐by‐year contributions & growth.
    Returns:
      final_balance,
      total_employee_contributions,
      total_employer_match,
      total_investment_returns
    """
    yrs = ra - ca
    B, S = cb, cs
    total_emp = 0.0
    total_match = 0.0

    for _ in range(yrs):
        cont  = S * (cp / 100)
        match = min(S * (mp / 100), S * (ml / 100))
        total_emp   += cont
        total_match += match

        B = B * (1 + ar / 100) + cont + match
        S = S * (1 + sg / 100)

    total_returns = B - total_emp - total_match
    return B, total_emp, total_match, total_returns

# -------------------
# Default form values
# -------------------
d401k = {
    "current_age":       "30",
    "current_salary":    "75000",
    "current_balance":   "35000",
    "contrib_pct":       "10",
    "match_pct":         "50",
    "match_limit_pct":   "3",
    "retire_age":        "65",
    "life_exp":          "85",
    "salary_growth":     "3",
    "annual_return":     "6",
    "inflation":         "3",
}

dsalary = {
    "salary_amt":   "50",
    "salary_freq":  "hour",
    "hours_week":   "40",
    "days_week":    "5",
}

dauto = {
    "price":        "50000",
    "term":         "60",
    "rate":         "5",
    "incentives":   "0",
    "down":         "10000",
    "trade_val":    "0",
    "trade_owed":   "0",
    "sales_tax":    "7.25",
    "fees":         "2800",
}

dmort = {
    "price":         "400000",
    "down_mode":     "percent",
    "down_value":    "20",
    "term_years":    "30",
    "rate":          "6.652",
    "start_month":   "May",
    "start_day":     "1",
    "start_year":    "2025",
    "include_costs": "yes",
    "tax_pct":       "1.2",
    "insurance":     "1500",
    "pmi":           "0",
    "hoa":           "0",
    "other_costs":   "4000",
}

# -------------------
# Routes
# -------------------

@app.route("/")
def home():
    return redirect(url_for("page_401k"))


@app.route("/401k", methods=["GET", "POST"])
def page_401k():
    data = d401k.copy()
    result = error = None

    if request.method == "POST":
        # pull form inputs
        for k in data:
            data[k] = request.form.get(k, data[k]).strip()

        try:
            # parse numeric values
            ca = int(data["current_age"])
            ra = int(data["retire_age"])
            le = int(data["life_exp"])
            cs = float(data["current_salary"])
            cb = float(data["current_balance"])
            cp = float(data["contrib_pct"])
            mp = float(data["match_pct"])
            ml = float(data["match_limit_pct"])
            sg = float(data["salary_growth"])
            ar = float(data["annual_return"])
            inf= float(data["inflation"])

            # compute breakdown
            nest, emp, match, returns = retirement(
                cb, cs, cp, mp, ml, ar, sg, inf, ca, ra, le
            )

            # present‐value discounting at inflation
            yrs = ra - ca
            pv_factor = 1 / pow(1 + inf / 100, yrs)
            nest_pv = nest * pv_factor

            result = {
                "nest":     f"${nest:,.0f}",
                "pv":       f"${nest_pv:,.0f}",
                "emp_cont": f"${emp:,.0f}",
                "match":    f"${match:,.0f}",
                "returns":  f"${returns:,.0f}",
                "retire_age": ra,
            }
        except:
            error = "Please enter valid numeric values."

    return render_template("401k.html",
                           data=data,
                           result=result,
                           error=error)


@app.route("/salary", methods=["GET", "POST"])
def page_salary():
    data = dsalary.copy()
    table = error = None

    if request.method == "POST":
        for k in data:
            data[k] = request.form.get(k, data[k]).strip()

        try:
            amt = float(data["salary_amt"])
            hw  = float(data["hours_week"])
            dw  = float(data["days_week"])
            freq = data["salary_freq"]

            # convert to hourly
            if freq == "hour":
                hr = amt
            elif freq == "day":
                hr = amt / (hw / dw)
            elif freq == "week":
                hr = amt / hw
            elif freq == "month":
                hr = (amt * 12) / (52 * hw)
            else:  # year
                hr = amt / (52 * hw)

            cadences = [
                ("Hourly",   1),
                ("Daily",    hw/dw),
                ("Weekly",   hw),
                ("Monthly",  hw*52/12),
                ("Annual",   hw*52),
            ]

            # no holidays/vacation → adjusted == unadjusted
            table = [
                {
                    "label": lbl,
                    "unadj": hr * hrs,
                    "adj":   hr * hrs
                }
                for lbl, hrs in cadences
            ]

        except:
            error = "Please enter valid salary numbers."

    return render_template("salary.html",
                           data=data,
                           table=table,
                           error=error)


@app.route("/auto", methods=["GET", "POST"])
def page_auto():
    data = dauto.copy()
    result = error = None

    if request.method == "POST":
        for k in data:
            data[k] = request.form.get(k, data[k]).strip()

        try:
            P       = float(data["price"])
            term    = int(data["term"])
            r       = float(data["rate"])
            inc     = float(data["incentives"])
            down    = float(data["down"])
            tv      = float(data["trade_val"])
            towed   = float(data["trade_owed"])
            st      = float(data["sales_tax"])
            fees    = float(data["fees"])

            net     = P - inc - down - tv + towed
            tax_amt = P * st / 100
            loan    = net + tax_amt + fees
            upfront = down + inc + tv - towed

            m       = pmt(loan, r, term)
            tp      = m * term
            ti      = tp - loan
            tc      = P + ti + fees

            result = {
                "loan":     f"${loan:,.2f}",
                "tax":      f"${tax_amt:,.2f}",
                "up":       f"${upfront:,.2f}",
                "pay":      f"${tp:,.2f}",
                "interest": f"${ti:,.2f}",
                "cost":     f"${tc:,.2f}",
                "monthly":  f"${m:,.2f}"
            }
        except:
            error = "Please enter valid auto‑loan values."

    return render_template("auto.html",
                           data=data,
                           result=result,
                           error=error)


if __name__=="__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    # listen on 0.0.0.0 so external requests reach your app
    app.run(host="0.0.0.0", port=port, debug=True)

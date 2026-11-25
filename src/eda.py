"""Exploratory data analysis -> figures in reports/figures + printed key numbers.

Usage:  python -m src.eda
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import FIG_DIR, MONTH_TO_NUM, TARGET
from src.train import load_clean_data

sns.set_theme(style="whitegrid", context="notebook")
MONTH_ORDER = list(MONTH_TO_NUM)


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=130, bbox_inches="tight")
    plt.close(fig)


def rate_bar(df, col, name, title, order=None, min_n=0, top=None, rotate=False):
    g = df.groupby(col)[TARGET].agg(rate="mean", n="size").reset_index()
    g = g[g["n"] >= min_n]
    if top:
        g = g.sort_values("n", ascending=False).head(top)
    if order:
        g[col] = pd.Categorical(g[col], order, ordered=True)
    g = g.sort_values(col if order else "rate", ascending=bool(order))
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    sns.barplot(data=g, x=col, y="rate", color="#4c72b0", ax=ax)
    ax.axhline(df[TARGET].mean(), color="crimson", ls="--", lw=1, label="Overall rate")
    for i, (r, n) in enumerate(zip(g["rate"], g["n"])):
        ax.text(i, r + 0.01, f"{r:.0%}\n(n={n:,})", ha="center", fontsize=7)
    ax.set(title=title, ylabel="Cancellation rate", xlabel="", ylim=(0, min(1.1, g["rate"].max() + 0.15)))
    if rotate:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend()
    save(fig, name)


def main():
    df = load_clean_data()
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["arrival_month"] = df["arrival_date"].dt.month_name()
    df["year_month"] = df["arrival_date"].dt.to_period("M").dt.to_timestamp()
    df["lead_bucket"] = pd.cut(
        df["lead_time"], [-1, 7, 30, 90, 180, 365, 10_000],
        labels=["0-7d", "8-30d", "31-90d", "91-180d", "181-365d", ">365d"])
    df["any_special_request"] = (df["total_of_special_requests"] > 0).map({True: "Yes", False: "No"})
    df["prev_cancel"] = (df["previous_cancellations"] > 0).map({True: "Has prior cancellation", False: "None"})

    print(f"Overall cancellation rate: {df[TARGET].mean():.1%}")

    # 1. Target balance by hotel
    rate_bar(df, "hotel", "eda_cancel_by_hotel.png", "Cancellation rate by hotel")
    # 2. Seasonality
    rate_bar(df, "arrival_month", "eda_cancel_by_month.png", "Cancellation rate by arrival month",
             order=MONTH_ORDER, rotate=True)
    # 3. Lead time
    rate_bar(df, "lead_bucket", "eda_cancel_by_lead_time.png", "Longer lead time -> more cancellations",
             order=list(df["lead_bucket"].cat.categories))
    # 4. Deposit type (data quirk worth flagging)
    rate_bar(df, "deposit_type", "eda_cancel_by_deposit.png", "Cancellation rate by deposit type")
    # 5. Market segment
    rate_bar(df, "market_segment", "eda_cancel_by_segment.png", "Cancellation rate by market segment",
             min_n=100, rotate=True)
    # 6. Country (top-12 by volume)
    rate_bar(df, "country", "eda_cancel_by_country.png", "Cancellation rate - top 12 countries by volume", top=12)
    # 7. Special requests
    rate_bar(df, "any_special_request", "eda_cancel_by_special_requests.png",
             "Guests with special requests rarely cancel")

    # 8. Monthly volume & rate timeline
    m = df.groupby("year_month").agg(bookings=(TARGET, "size"), rate=(TARGET, "mean")).reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(m["year_month"], m["bookings"], width=20, color="#c9d6ea", label="Bookings")
    ax.set_ylabel("Bookings (arrival month)")
    ax2 = ax.twinx()
    ax2.plot(m["year_month"], m["rate"], color="crimson", marker="o", label="Cancellation rate")
    ax2.set_ylabel("Cancellation rate")
    ax2.set_ylim(0, 0.7)
    ax.grid(axis="x", visible=False)
    ax2.grid(False)
    ax.set_title("Monthly bookings and cancellation rate (drift motivates the time-based split)")
    save(fig, "eda_timeline.png")

    # 9. ADR by month & hotel
    adr = df[(df["adr"] > 0) & (df["adr"] < 1000) & (df[TARGET] == 0)]
    pivot = adr.groupby(["arrival_month", "hotel"])["adr"].mean().unstack().reindex(MONTH_ORDER)
    fig, ax = plt.subplots(figsize=(8, 4.3))
    pivot.plot(marker="o", ax=ax)
    ax.set(title="Average daily rate (ADR) by month - realised stays", ylabel="ADR (EUR)", xlabel="")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    save(fig, "eda_adr_by_month.png")

    # 10. Correlation of numeric features with target
    num = df[["lead_time", "total_nights", "adults", "children", "adr", "booking_changes",
              "previous_cancellations", "previous_bookings_not_canceled", "is_repeated_guest",
              "required_car_parking_spaces", "total_of_special_requests", TARGET]]
    corr = num.corr()[TARGET].drop(TARGET).sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    corr.plot.barh(color=["#c44e52" if v > 0 else "#4c72b0" for v in corr], ax=ax)
    ax.set(title="Correlation with cancellation (Pearson)", xlabel="Correlation")
    save(fig, "eda_correlation.png")

    # Key numbers
    print("\nKey numbers")
    print(df.groupby("hotel")[TARGET].mean().round(3).to_string())
    print(df.groupby("deposit_type")[TARGET].agg(["mean", "size"]).round(3).to_string())
    print(df.groupby("lead_bucket", observed=True)[TARGET].mean().round(3).to_string())
    print(df.groupby("any_special_request")[TARGET].mean().round(3).to_string())
    print(df.groupby("prev_cancel")[TARGET].mean().round(3).to_string())


if __name__ == "__main__":
    main()

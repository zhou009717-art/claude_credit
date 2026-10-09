"""
台股加權指數 20 年走勢與半導體週期
資料來源：Yahoo Finance（^TWII 台股加權指數、^SOX 費城半導體指數）

用法：
    python3 scripts/taiex_semiconductor_cycle.py

輸出：
    output/taiex_semiconductor_cycle.png
    output/taiex_semiconductor_cycle.pdf
"""

import datetime as dt
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

START = "2000-01-01"
END = dt.date.today().isoformat()

OUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUT_DIR.mkdir(exist_ok=True)

matplotlib.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "Noto Sans CJK SC", "WenQuanYi Zen Hei"]
matplotlib.rcParams["axes.unicode_minus"] = False

TWII_COLOR = "#2255a4"
SOX_COLOR = "#e07b39"
CRASH_COLOR = "#c0392b"
DRIVER_COLOR = "#1b7a3d"


def fetch_close(ticker: str) -> pd.Series:
    df = yf.download(ticker, start=START, end=END, auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError(f"{ticker} 抓不到資料，請確認網路存取是否已開放。")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.name = ticker
    return close.dropna()


def nearest(series: pd.Series, date: str) -> tuple[pd.Timestamp, float]:
    """回傳離指定日期最近（含之後）那個交易日的 (日期, 收盤價)。"""
    target = pd.Timestamp(date)
    idx = series.index[series.index >= target]
    ts = idx[0] if len(idx) else series.index[-1]
    return ts, float(series.loc[ts])


def extremum(series: pd.Series, start: str, end: str, kind: str) -> tuple[pd.Timestamp, float]:
    window = series.loc[start:end]
    ts = window.idxmax() if kind == "max" else window.idxmin()
    return ts, float(window.loc[ts])


def main() -> None:
    twii = fetch_close("^TWII")
    sox = fetch_close("^SOX")

    # -----------------------------------------------------------------
    # 事件標記：歷史低潮用區間內實際高/低點抓取，近期里程碑用最近交易日實際收盤價
    # （數值皆來自抓到的真實資料，不手動硬編碼點位）
    # -----------------------------------------------------------------
    events = []

    ts, val = extremum(twii, "2000-01-01", "2000-06-30", "max")
    events.append((ts, val, f".com 泡沫前高點\n{val:,.0f}", CRASH_COLOR, "top"))

    ts, val = extremum(twii, "2008-09-01", "2009-01-31", "min")
    events.append((ts, val, f"金融海嘯低點\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = extremum(twii, "2015-07-01", "2016-02-29", "min")
    events.append((ts, val, f"陸股熔斷\n半導體下行\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = extremum(twii, "2018-10-01", "2019-01-31", "min")
    events.append((ts, val, f"中美貿易戰\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = extremum(twii, "2020-02-15", "2020-03-31", "min")
    events.append((ts, val, f"COVID-19 崩盤\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = extremum(twii, "2022-09-01", "2022-11-15", "min")
    events.append((ts, val, f"Fed 急升息\n記憶體去庫存\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = nearest(twii, "2023-05-01")
    events.append((ts, val, f"AI 熱潮啟動\nCoWoS 擴產\n{val:,.0f}", DRIVER_COLOR, "top"))

    ts, val = nearest(twii, "2024-07-11")
    events.append((ts, val, f"首度站上 2.4 萬點\n{val:,.0f}", DRIVER_COLOR, "top"))

    ts, val = nearest(twii, "2025-02-03")
    events.append((ts, val, f"DeepSeek + 關稅衝擊\n單日重挫\n{val:,.0f}", CRASH_COLOR, "bottom"))

    ts, val = nearest(twii, "2025-12-31")
    events.append((ts, val, f"首度站上 2.9 萬點\n{val:,.0f}", DRIVER_COLOR, "top"))

    events.sort(key=lambda e: e[0])

    # -----------------------------------------------------------------
    # 繪圖
    # -----------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=150)
    ax2 = ax1.twinx()

    ax1.plot(twii.index, twii.values, color=TWII_COLOR, linewidth=1.1, label="台股加權指數 (TAIEX, 左軸)")
    ax2.plot(sox.index, sox.values, color=SOX_COLOR, linewidth=1.0, alpha=0.75, label="費城半導體指數 (SOX, 右軸)")

    ax1.set_ylabel("台股加權指數 (點)", color=TWII_COLOR, fontsize=12)
    ax2.set_ylabel("費城半導體指數 SOX (點)", color=SOX_COLOR, fontsize=12)
    ax1.tick_params(axis="y", colors=TWII_COLOR)
    ax2.tick_params(axis="y", colors=SOX_COLOR)

    ax1.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    # 事件標記：垂直虛線 + 交錯上下的文字標籤，避免互相重疊
    ymin, ymax = ax1.get_ylim()
    for ts, val, label, color, pos in events:
        ax1.axvline(ts, color=color, linestyle=(0, (4, 3)), linewidth=0.8, alpha=0.55, zorder=1)
        y = ymax * 0.93 if pos == "top" else ymax * 0.05
        va = "top" if pos == "top" else "bottom"
        ax1.annotate(
            label,
            xy=(ts, y),
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=8.5,
            color=color,
            linespacing=1.3,
        )

    # 右側標出兩條線的最新數值
    last_twii = twii.iloc[-1]
    last_sox = sox.iloc[-1]
    ax1.annotate(
        f"{last_twii:,.0f}",
        xy=(twii.index[-1], last_twii),
        xytext=(8, 0),
        textcoords="offset points",
        color=TWII_COLOR,
        fontsize=10,
        fontweight="bold",
        va="center",
    )
    ax2.annotate(
        f"{last_sox:,.0f}",
        xy=(sox.index[-1], last_sox),
        xytext=(8, -12),
        textcoords="offset points",
        color=SOX_COLOR,
        fontsize=10,
        fontweight="bold",
        va="center",
    )

    # 軸線與格線樣式
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.grid(True, which="major", axis="both", linestyle=":", linewidth=0.6, color="#999999", alpha=0.5)
    for spine in ("top", "right"):
        ax1.spines[spine].set_visible(False)
        ax2.spines[spine].set_visible(False)

    fig.suptitle("台股加權指數 20 年走勢與半導體週期 (2000–2026)", fontsize=18, fontweight="bold", x=0.08, ha="left")
    ax1.set_title(
        "台股加權指數（TAIEX）對照費城半導體指數（SOX），標記重大景氣與產業事件對走勢的影響",
        fontsize=11,
        color="#555555",
        loc="left",
        pad=12,
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False, fontsize=10)

    fig.text(
        0.08, 0.01,
        f"資料來源：Yahoo Finance（^TWII、^SOX），擷取日期：{dt.date.today().isoformat()}",
        fontsize=8.5,
        color="#777777",
    )

    fig.tight_layout(rect=(0.03, 0.03, 0.97, 0.95))

    png_path = OUT_DIR / "taiex_semiconductor_cycle.png"
    pdf_path = OUT_DIR / "taiex_semiconductor_cycle.pdf"
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    print(f"saved: {png_path}")
    print(f"saved: {pdf_path}")


if __name__ == "__main__":
    main()

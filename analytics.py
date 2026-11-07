"""
Модуль аналитики: считает статистику по обращениям и строит графики Plotly.
"""
import pandas as pd
import plotly.express as px
import plotly.io as pio

from database import get_connection


def load_appeals_df() -> pd.DataFrame:
    """Загружает все обращения в DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, created_at, text, category, user_name, status FROM appeals",
        conn,
    )
    conn.close()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    return df


def kpi_stats() -> dict:
    """Считает ключевые показатели (KPI)."""
    df = load_appeals_df()
    if df.empty:
        return {
            "total": 0,
            "last_7_days": 0,
            "top_category": "—",
            "resolved_share": 0,
        }

    total = len(df)
    last_7 = df[df["created_at"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
    top_category = (
        df["category"].value_counts().idxmax() if not df["category"].isna().all() else "—"
    )
    resolved = df[df["status"].isin(["resolved", "closed"])]
    resolved_share = round(len(resolved) / total * 100, 1) if total else 0

    return {
        "total": total,
        "last_7_days": len(last_7),
        "top_category": top_category,
        "resolved_share": resolved_share,
    }


def chart_categories() -> str:
    """Круговая диаграмма: распределение по категориям. Возвращает HTML."""
    df = load_appeals_df()
    if df.empty:
        return "<p class='text-muted'>Нет данных для отображения</p>"

    counts = df["category"].value_counts().reset_index()
    counts.columns = ["Категория", "Количество"]

    fig = px.pie(
        counts,
        names="Категория",
        values="Количество",
        title="Распределение обращений по категориям",
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=450, margin=dict(t=60, b=20, l=20, r=20))

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def chart_dynamics(days: int = 30) -> str:
    """Столбчатая диаграмма: динамика по дням. Возвращает HTML."""
    df = load_appeals_df()
    if df.empty:
        return "<p class='text-muted'>Нет данных для отображения</p>"

    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days - 1)
    recent = df[df["created_at"] >= cutoff]

    by_day = (
        recent.groupby("date")
        .size()
        .reset_index(name="Количество")
    )
    by_day["date"] = pd.to_datetime(by_day["date"])

    full_range = pd.date_range(cutoff, pd.Timestamp.now().normalize(), freq="D")
    by_day = (
        by_day.set_index("date")
        .reindex(full_range, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )

    fig = px.bar(
        by_day,
        x="date",
        y="Количество",
        title=f"Динамика обращений за последние {days} дней",
    )
    fig.update_layout(
        height=400,
        margin=dict(t=60, b=40, l=20, r=20),
        xaxis_title="Дата",
        yaxis_title="Количество обращений",
    )
    fig.update_xaxes(tickformat="%d.%m")

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def chart_top_problems(limit: int = 10) -> str:
    """Горизонтальная диаграмма: топ самых частых текстов обращений."""
    df = load_appeals_df()
    if df.empty:
        return "<p class='text-muted'>Нет данных для отображения</p>"

    top = df["text"].value_counts().head(limit).reset_index()
    top.columns = ["Проблема", "Количество"]

    top["Проблема"] = top["Проблема"].apply(
        lambda s: s if len(s) <= 60 else s[:57] + "..."
    )

    fig = px.bar(
        top,
        x="Количество",
        y="Проблема",
        orientation="h",
        title=f"Топ-{limit} самых частых проблем пользователей",
    )
    fig.update_layout(
        height=420,
        margin=dict(t=60, b=20, l=20, r=20),
        yaxis=dict(autorange="reversed"),
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
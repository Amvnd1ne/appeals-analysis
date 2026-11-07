"""
Главный файл веб-приложения «Анализ обращений пользователей».
Запуск: python app.py
"""
import csv
import io

from flask import Flask, render_template, request, Response, jsonify

import analytics
from database import get_connection, init_db

app = Flask(__name__)


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT * FROM appeals WHERE 1=1"
    params = []
    if q:
        sql += " AND text LIKE ?"
        params.append(f"%{q}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC LIMIT 200"
    cur.execute(sql, params)
    appeals = cur.fetchall()
    cur.execute("SELECT name FROM categories ORDER BY name")
    categories = cur.fetchall()
    conn.close()
    return render_template(
        "index.html",
        appeals=appeals,
        categories=categories,
        total=len(appeals),
        q=q,
        category=category,
    )


@app.route("/appeal/<int:appeal_id>")
def appeal_detail(appeal_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
    appeal = cur.fetchone()
    conn.close()
    if not appeal:
        return "Обращение не найдено", 404
    return render_template("appeal.html", appeal=appeal)


@app.route("/stats")
def stats():
    return render_template(
        "stats.html",
        kpi=analytics.kpi_stats(),
        chart_categories=analytics.chart_categories(),
        chart_dynamics=analytics.chart_dynamics(),
        chart_top_problems=analytics.chart_top_problems(),
    )


@app.route("/export/csv")
def export_csv():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, created_at, text, category, user_name, status "
        "FROM appeals ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Дата", "Текст", "Категория", "Пользователь", "Статус"])
    for r in rows:
        writer.writerow([r["id"], r["created_at"], r["text"], r["category"], r["user_name"], r["status"]])
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=appeals.csv"},
    )


@app.route("/api/stats")
def api_stats():
    df = analytics.load_appeals_df()
    if df.empty:
        return jsonify({"total": 0, "by_category": {}, "by_status": {}})
    return jsonify({
        "total": int(len(df)),
        "by_category": df["category"].value_counts().to_dict(),
        "by_status": df["status"].value_counts().to_dict(),
        "last_7_days": analytics.kpi_stats()["last_7_days"],
    })


@app.route("/api/appeals")
def api_appeals():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    limit = int(request.args.get("limit", 100))
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT * FROM appeals WHERE 1=1"
    params = []
    if q:
        sql += " AND text LIKE ?"
        params.append(f"%{q}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"count": len(rows), "appeals": rows})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

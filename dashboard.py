import os
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# Edit these three lines with your own details
# ---------------------------------------------------------------
PROJECT_TITLE = "Face Recognition Attendance System"
COLLEGE_NAME = "RCEW.Jaipur"
DEVELOPED_BY = "Bhoomi bansal"

CSV_FILE = "attendance.csv"
FACES_DIR = "known_faces"

GREEN = "#22c55e"
RED = "#ef4444"
INDIGO = "#4f46e5"

STYLE = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #06b6d4 100%);
    padding: 28px 32px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1.2;
    color: white;
}
.hero-sub {
    font-size: 1.05rem;
    margin-top: 6px;
    opacity: 0.92;
    color: white;
}
.hero-tag {
    display: inline-block;
    background: rgba(255, 255, 255, 0.20);
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.82rem;
    margin: 12px 8px 0 0;
    color: white;
}

div[data-testid="stMetric"] {
    background-color: rgba(120, 120, 160, 0.10);
    border: 1px solid rgba(120, 120, 160, 0.25);
    border-left: 5px solid #6366f1;
    padding: 14px 16px;
    border-radius: 12px;
}
</style>
"""


def render_header():
    """Big coloured banner at the top of the page."""
    st.markdown(STYLE, unsafe_allow_html=True)
    today = datetime.now().strftime("%A, %d %B %Y")
    html = (
        '<div class="hero">'
        '<div class="hero-title">📋 ' + PROJECT_TITLE + "</div>"
        '<div class="hero-sub">Automatic attendance using face recognition '
        "with blink-based liveness detection</div>"
        '<span class="hero-tag">🎓 ' + COLLEGE_NAME + "</span>"
        '<span class="hero-tag">👩‍💻 Developed by ' + DEVELOPED_BY + "</span>"
        '<span class="hero-tag">📅 ' + today + "</span>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def load_students():
    """Student names taken from the photos in the known_faces folder."""
    names = []
    if os.path.isdir(FACES_DIR):
        for file in os.listdir(FACES_DIR):
            name = file.split(".")[0].rstrip("0123456789")
            if name != "" and name not in names:
                names.append(name)
    return names


def find_photo(name):
    """Path of the first photo of a student, or None."""
    if os.path.isdir(FACES_DIR):
        for file in sorted(os.listdir(FACES_DIR)):
            if file.split(".")[0].rstrip("0123456789") == name:
                return os.path.join(FACES_DIR, file)
    return None


def load_attendance():
    """Read attendance.csv. Returns None if the file does not exist."""
    if not os.path.exists(CSV_FILE):
        return None

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return df

    df["Name"] = df["Name"].astype(str).str.strip()
    df["Date"] = df["Date"].astype(str).str.strip()
    df["Time"] = df["Time"].astype(str).str.strip()
    df["Day"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["Day"])
    return df


def color_cell(value):
    if value == "P":
        return "background-color: #dcfce7; color: #166534; font-weight: 700; text-align: center"
    return "background-color: #fee2e2; color: #991b1b; font-weight: 700; text-align: center"


def status_colors():
    return alt.Scale(domain=["Good", "Low"], range=[GREEN, RED])


def show_dashboard():
    df = load_attendance()

    if df is None:
        st.warning("No attendance file found yet. Start the attendance camera first.")
        return
    if df.empty:
        st.info("No attendance has been recorded yet.")
        return

    # ---------- Basic numbers ----------
    students = load_students()
    for name in df["Name"].unique():
        if name not in students:
            students.append(name)
    students.sort()

    all_dates = sorted(df["Day"].dt.date.unique())
    total_days = len(all_dates)

    days_present = df.groupby("Name")["Day"].nunique()

    report = pd.DataFrame({"Name": students})
    report["Days Present"] = report["Name"].map(days_present).fillna(0).astype(int)
    report["Days Absent"] = total_days - report["Days Present"]
    report["Attendance %"] = (report["Days Present"] / total_days * 100).round(1)

    # ---------- Filters ----------
    with st.container(border=True):
        f1, f2, f3 = st.columns([2, 2, 1])
        with f1:
            selected_date = st.selectbox(
                "Select date",
                list(reversed(all_dates)),
                format_func=lambda d: d.strftime("%A, %d %b %Y"),
            )
        with f2:
            limit = st.slider("Minimum attendance required (%)", 0, 100, 75)
        with f3:
            st.write("")
            st.write("")
            st.button("Refresh data")

        updated = datetime.fromtimestamp(os.path.getmtime(CSV_FILE))
        st.caption("Data last updated: " + updated.strftime("%d %b %Y, %I:%M %p"))

    report["Status"] = ["Good" if p >= limit else "Low" for p in report["Attendance %"]]

    day_df = df[df["Day"].dt.date == selected_date].sort_values("Time")
    present_names = sorted(day_df["Name"].unique())
    absent_names = [n for n in students if n not in present_names]

    # ---------- Summary cards ----------
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total students", len(students))
    m2.metric("Present (selected date)", len(present_names))
    m3.metric("Absent (selected date)", len(absent_names))
    m4.metric("Average attendance", str(round(report["Attendance %"].mean(), 1)) + "%")
    m5.metric("Days recorded", total_days)

    st.write("")

    tab_overview, tab_daily, tab_student, tab_sheet, tab_records = st.tabs(
        ["Overview", "Daily Attendance", "Student Report", "Attendance Sheet", "All Records"]
    )

    percent_config = {
        "Attendance %": st.column_config.ProgressColumn(
            "Attendance %", min_value=0, max_value=100, format="%.1f%%"
        )
    }

    # ---------- Tab 1: Overview ----------
    with tab_overview:
        st.subheader("Top attendance")
        top = report.sort_values(["Attendance %", "Name"], ascending=[False, True]).head(3)
        medals = ["🥇", "🥈", "🥉"]
        medal_cols = st.columns(3)
        for i in range(len(top)):
            row = top.iloc[i]
            medal_cols[i].metric(medals[i] + " " + row["Name"], str(row["Attendance %"]) + "%")

        st.write("")
        left, right = st.columns(2)

        with left:
            st.subheader("Students present per day")
            daily = df.groupby("Day")["Name"].nunique().reset_index()
            daily.columns = ["Date", "Students Present"]
            line = (
                alt.Chart(daily)
                .mark_line(point=True, color=INDIGO, strokeWidth=3)
                .encode(
                    x=alt.X("Date:T", title=None),
                    y=alt.Y("Students Present:Q", title=None),
                    tooltip=["Date:T", "Students Present:Q"],
                )
                .properties(height=300)
            )
            st.altair_chart(line)

        with right:
            st.subheader("Attendance % by student")
            chart_df = report.rename(columns={"Attendance %": "Percent"})
            bars = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("Name:N", sort="-y", title=None),
                    y=alt.Y("Percent:Q", scale=alt.Scale(domain=[0, 100]), title=None),
                    color=alt.Color("Status:N", scale=status_colors(), legend=None),
                    tooltip=["Name:N", "Percent:Q", "Days Present:Q"],
                )
                .properties(height=300)
            )
            st.altair_chart(bars)

        st.subheader("Attendance report")
        shown = report.copy()
        shown["Status"] = shown["Status"].map({"Good": "✅ Good", "Low": "⚠️ Low"})
        st.dataframe(shown, hide_index=True, column_config=percent_config)

        st.subheader("Students below " + str(limit) + "%")
        low = report[report["Attendance %"] < limit]
        if low.empty:
            st.success("Everyone meets the minimum attendance requirement.")
        else:
            st.dataframe(
                low[["Name", "Days Present", "Days Absent", "Attendance %"]],
                hide_index=True,
                column_config=percent_config,
            )

        st.download_button(
            "Download attendance report (CSV)",
            report.to_csv(index=False),
            "attendance_report.csv",
            "text/csv",
        )

    # ---------- Tab 2: Daily attendance ----------
    with tab_daily:
        st.subheader(selected_date.strftime("%A, %d %B %Y"))
        chart_col, present_col, absent_col = st.columns([1, 1, 1])

        with chart_col:
            pie_df = pd.DataFrame(
                {
                    "Status": ["Present", "Absent"],
                    "Count": [len(present_names), len(absent_names)],
                }
            )
            donut = (
                alt.Chart(pie_df)
                .mark_arc(innerRadius=62)
                .encode(
                    theta="Count:Q",
                    color=alt.Color(
                        "Status:N",
                        scale=alt.Scale(domain=["Present", "Absent"], range=[GREEN, RED]),
                        legend=alt.Legend(orient="bottom", title=None),
                    ),
                    tooltip=["Status:N", "Count:Q"],
                )
                .properties(height=280)
            )
            st.altair_chart(donut)

        with present_col:
            st.markdown("**✅ Present (" + str(len(present_names)) + ")**")
            if day_df.empty:
                st.info("Nobody was marked present on this date.")
            else:
                st.dataframe(day_df[["Name", "Time"]], hide_index=True)

        with absent_col:
            st.markdown("**❌ Absent (" + str(len(absent_names)) + ")**")
            if len(absent_names) == 0:
                st.success("Everyone was present.")
            else:
                st.dataframe(pd.DataFrame({"Name": absent_names}), hide_index=True)

    # ---------- Tab 3: Student report ----------
    with tab_student:
        who = st.selectbox("Select student", students)
        row = report[report["Name"] == who].iloc[0]

        photo_col, info_col = st.columns([1, 3])

        with photo_col:
            photo_path = find_photo(who)
            if photo_path is not None:
                st.image(photo_path, width=170, caption=who)
            else:
                st.info("No photo found.")

        with info_col:
            s1, s2, s3 = st.columns(3)
            s1.metric("Days present", int(row["Days Present"]))
            s2.metric("Days absent", int(row["Days Absent"]))
            s3.metric("Attendance", str(row["Attendance %"]) + "%")

            st.progress(int(round(row["Attendance %"])))

            if row["Attendance %"] < limit:
                st.error(who + " is below the required " + str(limit) + "% attendance.")
            else:
                st.success(who + " meets the required " + str(limit) + "% attendance.")

        student_days = set(df[df["Name"] == who]["Day"].dt.date)
        history = pd.DataFrame(
            {
                "Date": [d.strftime("%A, %d %b %Y") for d in reversed(all_dates)],
                "Status": [
                    "✅ Present" if d in student_days else "❌ Absent"
                    for d in reversed(all_dates)
                ],
            }
        )
        st.subheader("Day-by-day history")
        st.dataframe(history, hide_index=True)

    # ---------- Tab 4: Attendance sheet (P / A for every date) ----------
    with tab_sheet:
        st.subheader("Attendance sheet")
        st.caption("P = Present, A = Absent")

        present_pairs = set(zip(df["Name"], df["Day"].dt.date))
        sheet = pd.DataFrame(
            [["P" if (s, d) in present_pairs else "A" for d in all_dates] for s in students],
            index=students,
            columns=[d.strftime("%d %b %y") for d in all_dates],
        )

        try:
            styler = sheet.style
            mapper = getattr(styler, "map", None)
            if mapper is None:
                mapper = styler.applymap
            st.dataframe(mapper(color_cell))
        except Exception:
            st.dataframe(sheet)

    # ---------- Tab 5: All records ----------
    with tab_records:
        query = st.text_input("Search by name")
        records = df.sort_values(["Day", "Time"], ascending=False)[["Name", "Date", "Time"]]
        if query.strip() != "":
            records = records[
                records["Name"].str.contains(query.strip(), case=False, regex=False)
            ]

        st.write(str(len(records)) + " record(s)")
        st.dataframe(records, hide_index=True)

        st.download_button(
            "Download all records (CSV)",
            records.to_csv(index=False),
            "attendance_records.csv",
            "text/csv",
        )

    st.write("")
    st.caption("Built with Python, OpenCV, face_recognition, pandas and Streamlit.")


if __name__ == "__main__":
    st.set_page_config(page_title="Attendance Dashboard", page_icon="📋", layout="wide")
    render_header()
    show_dashboard()
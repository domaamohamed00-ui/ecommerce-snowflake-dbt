import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st

st.set_page_config(page_title="Executive Analytics v2", page_icon="📊", layout="wide")
BLUE, NAVY = "#29B5E8", "#11567F"

CFG = {"user": "202403486@PUA.EDU.EG", "account": "BMGFCPZ-JG06419",
       "warehouse": "COMPUTE_WH", "database": "ECOMMERCE_DB", "schema": "MARTS"}

st.markdown("""<style>
div[data-testid="stMetric"]{background:#1E222A;border:1px solid #2D3139;
border-left:4px solid #29B5E8;border-radius:8px;padding:15px 20px}
</style>""", unsafe_allow_html=True)

# password: from secrets.toml if it exists, otherwise from the sidebar
try:
    pwd = st.secrets["snowflake"]["password"]
except Exception:
    pwd = st.sidebar.text_input("Snowflake password", type="password")
if not pwd:
    st.info("Enter your Snowflake password in the sidebar.")
    st.stop()


@st.cache_data(ttl=600, show_spinner="Loading from Snowflake...")
def fetch(query, pwd):
    conn = snowflake.connector.connect(password=pwd, **CFG)
    try:
        cur = conn.cursor()
        cur.execute(query)
        df = pd.DataFrame(cur.fetchall(), columns=[c[0].upper() for c in cur.description])
    finally:
        conn.close()
    for c in ("TOTAL_AMOUNT", "TOTAL_REVENUE", "TOTAL_SPENT"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def pick(df, *names):
    return next((n for n in names if n in df.columns), None)


def style(fig, h=400):
    fig.update_layout(template="plotly_dark", height=h, showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=20, t=30, b=10), xaxis_title=None, yaxis_title=None)
    return fig


try:
    d_cat = fetch("SELECT * FROM MART_CATEGORY_SALES", pwd)
    d_cust = fetch("SELECT * FROM MART_CUSTOMER_SUMMARY", pwd)
    d_ord = fetch("SELECT * FROM FCT_ORDERS", pwd)
except Exception as e:
    st.error(f"Snowflake error: {e}")
    st.stop()

DATE = pick(d_ord, "ORDER_DATE")
STATUS = pick(d_ord, "ORDER_STATUS", "STATUS")
CAT = pick(d_ord, "CATEGORY", "PRODUCT_CATEGORY")
if DATE:
    d_ord[DATE] = pd.to_datetime(d_ord[DATE], errors="coerce")

# ---- filters ----
st.sidebar.title("Filters")
df = d_ord.copy()
if DATE and df[DATE].notna().any():
    lo, hi = df[DATE].min().date(), df[DATE].max().date()
    r = st.sidebar.date_input("Order date", (lo, hi), min_value=lo, max_value=hi)
    if len(r) == 2:
        df = df[(df[DATE].dt.date >= r[0]) & (df[DATE].dt.date <= r[1])]
df_status = df
if STATUS:
    opts = sorted(df[STATUS].dropna().unique())
    ch = st.sidebar.multiselect("Order status", opts,
                                default=["completed"] if "completed" in opts else opts)
    if ch:
        df = df[df[STATUS].isin(ch)]
if df.empty:
    st.warning("No orders match these filters.")
    st.stop()

# ---- header + KPIs ----
st.title("E-Commerce Executive Analytics")
st.caption("Dashboard v2 · Snowflake · dbt · Streamlit")
rev, n = df["TOTAL_AMOUNT"].sum(), len(df)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Gross revenue", f"${rev:,.0f}")
k2.metric("Orders", f"{n:,}")
k3.metric("Customers", f"{len(d_cust):,}")
k4.metric("Avg. order value", f"${rev / n:,.0f}")

t1, t2, t3 = st.tabs(["Executive Summary", "Customer Intelligence", "Fact Data Explorer"])

with t1:
    if CAT:
        cat = df.groupby(CAT, as_index=False)["TOTAL_AMOUNT"].sum()
        cat.columns = ["CATEGORY", "TOTAL_REVENUE"]
    else:
        cat = d_cat[["CATEGORY", "TOTAL_REVENUE"]]
    cat = cat.sort_values("TOTAL_REVENUE")
    a, b = st.columns(2)
    with a:
        st.subheader("Revenue by category")
        f = px.bar(cat, x="TOTAL_REVENUE", y="CATEGORY", orientation="h", text_auto=".2s")
        f.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
        st.plotly_chart(style(f), use_container_width=True)
    with b:
        st.subheader("Revenue share")
        f = px.pie(cat, names="CATEGORY", values="TOTAL_REVENUE", hole=0.55,
                   color_discrete_sequence=px.colors.sequential.Blues_r)
        f.update_layout(template="plotly_dark", height=400, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(f, use_container_width=True)
    c, d = st.columns(2)
    with c:
        st.subheader("Revenue over time")
        if DATE and df[DATE].notna().any():
            t = df.dropna(subset=[DATE]).copy()
            t["M"] = t[DATE].dt.to_period("M").dt.to_timestamp()
            t = t.groupby("M", as_index=False)["TOTAL_AMOUNT"].sum()
            f = px.area(t, x="M", y="TOTAL_AMOUNT", markers=True)
            f.update_traces(line_color=NAVY, fillcolor="rgba(41,181,232,.25)")
            st.plotly_chart(style(f, 340), use_container_width=True)
    with d:
        st.subheader("Orders by status")
        if STATUS:
            s = df_status.groupby(STATUS, as_index=False).size().sort_values("size")
            f = px.bar(s, x="size", y=STATUS, orientation="h", text_auto=True)
            f.update_traces(marker_color=NAVY)
            st.plotly_chart(style(f, 340), use_container_width=True)

with t2:
    st.subheader("Top customers by lifetime value")
    top = d_cust.sort_values("TOTAL_SPENT", ascending=False).head(10).sort_values("TOTAL_SPENT")
    f = px.bar(top, x="TOTAL_SPENT", y="CUSTOMER_NAME", orientation="h", text_auto=".2s")
    f.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
    st.plotly_chart(style(f, 420), use_container_width=True)

with t3:
    q = st.text_input("Search records", "")
    out = df
    if q:
        m = df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
        out = df[m]
    st.dataframe(out, use_container_width=True, hide_index=True)
    st.download_button("Export CSV", out.to_csv(index=False).encode("utf-8"),
                       "orders.csv", "text/csv")
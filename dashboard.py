import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(page_title="E-Commerce Analytics", layout="wide")
st.title("📊 E-Commerce Executive Dashboard (Snowflake + dbt)")

st.sidebar.header("🔑 Snowflake Authentication")
password = st.sidebar.text_input("Snowflake Password", type="password")

if not password:
    st.info("👈 Please enter your Snowflake password in the sidebar to connect.")
else:
    try:
        conn = snowflake.connector.connect(
            user="202403486@PUA.EDU.EG",
            password=password,
            account="BMGFCPZ-JG06419",
            warehouse="COMPUTE_WH",
            database="ECOMMERCE_DB",
            schema="MARTS"
        )
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 Revenue by Product Category")
            df_cat = pd.read_sql("SELECT CATEGORY, TOTAL_REVENUE FROM MART_CATEGORY_SALES", conn)
            st.bar_chart(df_cat.set_index("CATEGORY"))
        with col2:
            st.subheader("🏆 Top Spending Customers")
            df_cust = pd.read_sql("SELECT CUSTOMER_NAME, TOTAL_SPENT FROM MART_CUSTOMER_SUMMARY ORDER BY TOTAL_SPENT DESC LIMIT 10", conn)
            st.bar_chart(df_cust.set_index("CUSTOMER_NAME"))
        conn.close()
        st.sidebar.success(" Connected!")
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

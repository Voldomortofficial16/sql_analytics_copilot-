import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
from groq import Groq

# ---------------------------
# PAGE CONFIG
# ---------------------------

st.set_page_config(
    page_title="SQL Analytics Copilot",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI-Powered SQL Analytics Copilot")
st.markdown("Ask business questions in plain English and get SQL-powered insights.")

# ---------------------------
# GROQ API KEY
# ---------------------------

groq_api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password"
)

# ---------------------------
# FILE UPLOAD
# ---------------------------

uploaded_file = st.file_uploader(
    "Upload CSV Dataset",
    type=["csv"]
)

if uploaded_file is not None:

    # ---------------------------
    # LOAD DATA
    # ---------------------------

    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    st.success("Dataset Loaded Successfully ✅")

    with st.expander("Preview Dataset"):
        st.dataframe(df.head())

    # ---------------------------
    # DUCKDB
    # ---------------------------

    con = duckdb.connect()

    con.register(
        "sales_data",
        df
    )

    st.subheader("Dataset Columns")

    st.write(list(df.columns))

    # ---------------------------
    # QUESTION INPUT
    # ---------------------------

    question = st.text_input(
        "Ask a Business Question",
        placeholder="Top 5 states by revenue"
    )

    # ---------------------------
    # GENERATE SQL
    # ---------------------------

    def generate_sql(question):

        client = Groq(
            api_key=groq_api_key
        )

        prompt = f"""
You are a Senior Data Analyst.

Database: DuckDB

Table Name: sales_data

Columns:
{list(df.columns)}

Rules:

1. Return ONLY SQL.
2. Use DuckDB syntax.
3. Never use TOP.
4. Use LIMIT.
5. No markdown.
6. No explanation.
7. Use column names exactly as provided.
8. Use GROUP BY when using SUM, AVG, COUNT.

Question:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    # ---------------------------
    # CLEAN SQL
    # ---------------------------

    def clean_sql(sql):

        sql = sql.replace("```sql", "")
        sql = sql.replace("```", "")

        return sql.strip()

    # ---------------------------
    # EXECUTE BUTTON
    # ---------------------------

    if st.button("Generate Analysis"):

        if not groq_api_key:

            st.error("Please enter Groq API Key")

        elif not question:

            st.error("Please enter a question")

        else:

            try:

                sql_query = generate_sql(question)

                sql_query = clean_sql(sql_query)

                st.subheader("Generated SQL")

                st.code(
                    sql_query,
                    language="sql"
                )

                result = con.execute(
                    sql_query
                ).fetchdf()

                st.subheader("Results")

                st.dataframe(
                    result,
                    use_container_width=True
                )

                # ---------------------------
                # CHARTS
                # ---------------------------

                if len(result.columns) >= 2:

                    first_col = result.columns[0]
                    second_col = result.columns[1]

                    try:

                        fig = px.bar(
                            result,
                            x=first_col,
                            y=second_col,
                            title=f"{second_col} by {first_col}"
                        )

                        st.subheader("Visualization")

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    except:
                        pass

            except Exception as e:

                st.error(f"Error: {e}")

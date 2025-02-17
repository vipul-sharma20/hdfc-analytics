import pandas as pd
import plotly.express as px


def plot_df(categorized_df: pd.DataFrame, statement_type: str = "account") -> None:
    if statement_type == "cc":
        categorized_df["amount"] = categorized_df["amount"].apply(
            lambda x: abs(float(x)) if float(x) < 0 else 0
        )
    else:
        categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(0)

    # Filter out positive amounts
    if statement_type == "cc":
        categorized_df = categorized_df[categorized_df["amount"] > 0]

    # Summarize the data by category
    category_summary = categorized_df.groupby("category")["amount"].sum().reset_index()

    # Plot the pie chart using Plotly
    fig = px.pie(
        category_summary,
        values="amount",
        names="category",
        title="Expenses by Category",
    )
    fig.update_traces(textinfo="percent+label")

    # Show the figure
    fig.show()

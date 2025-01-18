import plotly.express as px
import pandas as pd

def create_pie_chart(data, title="Category-wise Spending"):
    """
    Create a pie chart for category-wise spending.
    """
    df = pd.DataFrame(data=data)
    fig = px.pie(df, names="category", values="amount", title=title)
    return fig

def create_bar_chart(data, title="Monthly Spending"):
    """
    Creates a bar chart for monthly spending trends with distinct colors.
    """
    df = pd.DataFrame(data)
    if len(df) == 1:
        # Add dummy data to create padding 
        df = pd.concat([df, pd.DataFrame({"month": [" "], "amount": [0]})], ignore_index=True)
    fig = px.bar(
        df, 
        x="month", 
        y="amount", 
        title=title, 
        text="amount", 
        color_discrete_sequence=["#1f77b4"]  # Set a distinct color for the bars
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount",
        xaxis=dict(tickmode="linear"),  # Ensure proper spacing for months
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")  # Show values outside bars
    return fig



def create_line_chart(data, title="Spending Over Time"):
    """
    Creates a line chart for spending trends.
    """
    df = pd.DataFrame(data=data)
    fig = px.line(df, x="date", y="amount", title=title, markers=True)
    return fig

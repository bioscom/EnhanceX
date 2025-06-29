from .models import *
from django.db.models import Q, F, Prefetch
from dashboard.forms import *
import traceback
from Fit4.models import *
from reports.models import *
import plotly.express as px
import pandas as pd
from plotly.io import to_html
import json
import plotly.graph_objects as go
import plotly
#import datetime

from decimal import Decimal
from django.utils import timezone


def add_monthly_totals(df, column_prefix):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return df[[f"{month}_{column_prefix}" for month in months]].sum(axis=1)

def convert_decimal_float(df):
    df = df.copy()
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].astype(float)
    return df

def chart_wrapper(func):
    def wrapper(df):
        try:
            chart = func(df)
            return to_html(chart, full_html=False)
        except Exception:
            print(traceback.format_exc())
            return ""
    return wrapper


#@chart_wrapper
def doughnutPlanChart(df):
    doughnut_chart_html = ""
    try:
        df = convert_decimal_float(df)
        numeric_cols = df.select_dtypes(include='number').columns
        df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()
        print(df)
        df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']

        # Select the data points to be plotted
        wrk = df['WorkstreamName']
        Plan = df['Plan']

        data = {'Workstream': wrk, 'Plan': Plan}
        df=pd.DataFrame(data)
        doughnut_chart = px.pie(df, names="Workstream", values="Plan", title=" Plan By Workstream", hole=0.5)
        doughnut_chart.update_traces(text=df["Plan"].apply(lambda x: f"{round(x/1000000, 1):,}M"), textinfo="text")
        s=df["Plan"].sum()/1000000
        doughnut_chart.add_annotation(text=f"{round(s, 1):,}M", x=0.5, y=0.5, showarrow=False, font=dict(size=20, family="Arial", color="black"))
        doughnut_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

        # Convert to HTML
        doughnut_chart_html = to_html(doughnut_chart, full_html=False)
    except Exception as e:
        print(traceback.format_exc())
    return doughnut_chart_html

#@chart_wrapper
def doughnutActualChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Actual': Actual}
    df=pd.DataFrame(data)
    doughnut_chart = px.pie(df, names="Workstream", values="Actual", title="Actual By Workstream", hole=0.5)
    doughnut_chart.update_traces(text=df["Actual"].apply(lambda x: f"{round(x/1000000, 1):,}M"), textinfo="text")
    s=df["Actual"].sum()/1000000
    doughnut_chart.add_annotation(text=f"{round(s, 1):,}M", x=0.5, y=0.5, showarrow=False, font=dict(size=20, family="Arial", color="black"))
    doughnut_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    doughnut_chart_html = to_html(doughnut_chart, full_html=False)

    return doughnut_chart_html

#@chart_wrapper
def VerticalBarChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Workstream"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Workstream", y="Value", color="Category", title="Plan Forecast & Actual By Workstream", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def HorizontalBarChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Workstream"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Value", y="Workstream", color="Category", title="Plan Chart", orientation='h', barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def VerticalBarChartByFunctions(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('functions', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    function = df['functions']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Function': function, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Function"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Function", y="Value", color="Category", title="Plan, Forecast and Actual By Funcions", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def VerticalBarChartByLGates(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('ActualLGate', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    ActualL_Gate = df['ActualLGate']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'ActualL_Gate': ActualL_Gate, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["ActualL_Gate"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"] = df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="ActualL_Gate", y="Value", color="Category", title="Plan By LGate", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def ChartCountByLGates(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('ActualLGate', as_index =False)[numeric_cols].sum()

    #print(df)
    # Select the data points to be plotted
    ActualL_Gate = df['ActualLGate']
    Count = df['initiative_id']

    data = {'ActualL_Gate': ActualL_Gate, 'Count': Count}

    df=pd.DataFrame(data)
    
    grouped_bar_chart = px.bar(df, x="ActualL_Gate", y="Count", title="Count By LGate", barmode="group")
    grouped_bar_chart.update_traces(textposition="auto", text=Count)
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html


def VerticalBarChartByInLast7Days(request):
    # Get today's date
    today = timezone.now()

    # Get data from the last 7 days
    last_7_days = today - timezone.timedelta(days=7)

    queryset=InitiativeImpact.objects.select_related('initiative').annotate(
            Workstream=F('initiative__Workstream'),
            WorkstreamName=F('initiative__Workstream__workstreamname'),
            HashTag=F('initiative__HashTag'),
            functions=F('initiative__functions__title'),
            Year=F('initiative__YYear'),
            overall_status=F('initiative__overall_status'),
            Plan_Relevance=F('initiative__Plan_Relevance'), 
            ActualLGate=F('initiative__actual_Lgate__LGate'),
            enabledby=F('initiative__enabledby')).filter(initiative__Created_Date__gte=last_7_days).values()
    
    if queryset.exists():
        # Convert to Pandas DataFrame
        df=pd.DataFrame(list(queryset))
        df=df.drop(columns=['last_modified_date', 'Created_Date'])
        df.replace(to_replace=[None], value=0, inplace=True)

        df = convert_decimal_float(df)
        numeric_cols = df.select_dtypes(include='number').columns
        df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()
        df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    
        if not df.empty:
            # Create the Plotly figure
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["WorkstreamName"],
                y=df["Plan"],
                text=df["Plan"].apply(lambda x: f"{round(x/1000000, 1):,}M"),
                textposition="auto",
                marker=dict(color="blue")
            ))

            # Format the layout
            fig.update_layout(
                title="Initiatives Created in the Last 7 Days",
                xaxis_title="Workstream",
                yaxis_title="Sum of Plan",
                # height=460, 
                # width=500,
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            # Convert Plotly figure to JSON
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            graph_json = None
        return graph_json
    else:
        graph_json = None
    return graph_json


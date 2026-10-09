import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

st.set_page_config(
        page_title="Barcelona Bicing Analytics",
        layout="wide",
        )

DB_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        }

def get_connection():
    missing = [
            key for key, value in DB_CONFIG.items() if value is None or value == ""
            ]

    if missing:
        raise ValueError(
                "Missing database configuration: " + ", ".join(missing) + ". Check the .env file in the project root,"
                )

    return psycopg.connect(**DB_CONFIG)

@st.cache_data(ttl=60)
def load_network_summary() -> pd.DataFrame:
    query = """
        SELECT
            stations_reporting,
            bikes_available,
            docks_available,
            empty_stations,
            low_availability_stations,
            avg_station_bike_availability_pct,
            latest_ingestion
        FROM public.mart_network_summary
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def load_latest_stations() -> pd.DataFrame:
    query = """
        SELECT
            station_id,
            last_reported,
            ingested_at,
            num_vehicles_available,
            num_docks_available,
            num_vehicles_disabled,
            num_docks_disabled,
            total_capacity,
            bike_availability_pct,
            dock_availability_pct,
            availability_status
        FROM public.mart_station_latest
        ORDER BY station_id
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


@st.cache_data(ttl=60)
def load_historical_availability() -> pd.DataFrame:
    query = """
        SELECT
            time_bucket,
            stations_reporting,
            bikes_available,
            docks_available,
            avg_station_bike_availability_pct
        FROM public.mart_network_availability_5min
        ORDER BY time_bucket
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def format_number(value) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(value):,}"

def format_percentage(value) -> str:
    if pd.isna(value):
        return "-"
    
    return f"{float(value):.2f}"

def prepare_timestamps(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                    df[column],
                    utc=True,
                    errors="coerce",
                    )
    return df

# Header

header_col, refresh_col = st.columns([5, 1])

with header_col:
    st.title("Barcelona Bicing Analytics")
    st.caption(
            "Real-time bike availability and historical network trends \n"
            "Architecture: Kafka, PostgreSQL, dbt and Streamlit."
            )

with refresh_col:
    st.write("")
    st.write("")
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load

try:
    summary_df = load_network_summary()
    stations_df = load_latest_stations()
    history_df = load_historical_availability()

except Exception as exc:
    st.error(
            "The dashboard could not load its data from PostgreSQL."
            )
    st.markdown(
            """ 
            **Check:
            - Docker and PostgreSQL container are running.
            - Project-root '.env' database settings.
            - The dbt models in the target database
            - The database contains `mart_network_summary`,
                `mart_station_latest` and `mart_network_availability_5min`.
            """
            )
    with st.expander("Technical error details"):
        st.exception(exc)

    st.stop()

if summary_df.empty:
    st.warning(
            "The network summary is empty. Run the dbt models and refresh."
            )
    st.stop()

summary = summary_df.iloc[0]

stations_df = prepare_timestamps(
        stations_df,
        ["last_reported", "ingested_at"],
        )

history_df = prepare_timestamps(
        history_df, ["time_bucket"]
        )

latest_ingestion = pd.to_datetime(
        summary["latest_ingestion"], utc=True, errors="coerce",
        )

if pd.notna(latest_ingestion):
    st.caption(
            "Latest database ingestion: "
            f"{latest_ingestion.strftime('%d %b %Y, %H:%M:%S UTC')}"
            "| Dashboard cache: up to 60 seconds"
            )

st.divider()

#Network overview
st.header("Network overview")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("Stations reporting", format_number(summary["stations_reporting"]))
metric2.metric("Bikes available", format_number(summary["bikes_available"]))
metric3.metric("Free docks", format_number(summary["docks_available"]))
metric4.metric("Empty stations", format_number(summary["empty_stations"]))

metric5, metric6, metric7 = st.columns(3)

metric5.metric(
    "Low-availability stations",
    format_number(summary["low_availability_stations"]),
)

metric6.metric(
    "Average bike availability",
    format_percentage(
        summary["avg_station_bike_availability_pct"]
    ),
)

if not stations_df.empty:
    disabled_bikes = stations_df[
        "num_vehicles_disabled"
    ].fillna(0).sum()

    disabled_docks = stations_df[
        "num_docks_disabled"
    ].fillna(0).sum()
else:
    disabled_bikes = 0
    disabled_docks = 0

metric7.metric(
    "Disabled bikes",
    format_number(disabled_bikes),
)

st.caption(
    "Availability percentages are averaged across stations. "
    "They are not the percentage of all network bikes that are available."
)

# Dashboard tabs
overview_tab, trends_tab, stations_tab = st.tabs(
        [
            "Overview",
            "Historical trends",
            "Station explorer",
            ]
        )

# Tab 1: Overview
with overview_tab:
    st.subheader("Station availability distribution")

    if stations_df.empty:
        st.info("No station data is available yet.")
    else:
        status_counts = (
                stations_df["availability_status"]
                .fillna("unknown")
                .value_counts()
                .rename_axis("status")
                .reset_index(name="stations")
                )
        left_col, right_col = st.columns(2)

        with left_col:
            status_order = ["empty", "low", "medium", "high", "unknown"]
            
            status_counts["status"] = pd.Categorical(
                    status_counts["status"],
                    categories=status_order,
                    ordered=True,
                    )
            status_counts = status_counts.sort_values("status")

            status_fig = px.bar(
                    status_counts,
                    x="status",
                    y="stations",
                    title="Stations by availability status",
                    labels={
                        "status": "Availability status",
                        "stations": "Number of stations",
                        },
                    text="stations",
                    )

            status_fig.update_layout(
                    xaxis_title=None,
                    yaxis_title="Number of stations",
                    showlegend=False,
                    )
            status_fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    )
            st.plotly_chart(
                    status_fig,
                    use_container_width=True,
                    )
        with right_col:
            availability_df = stations_df[
                    ["station_id", "bike_availability_pct"]
                    ].dropna()
            availability_df = availability_df.sort_values(
                    "bike_availability_pct"
                    )
            if not availability_df.empty:
                availability_fig = px.histogram(
                        availability_df,
                        x="bike_availability_pct",
                        nbins=20,
                        title="Distribution of bike availability",
                        labels={
                            "bike_availability_pct": "Bike availability (%)",
                            "count": "Number of stations",
                            }
                        )

                availability_fig.update_layout(
                        xaxis_title="Bike availability (%)",
                        yaxis_title="Number of stations",
                        bargap=0.08,
                        )
                st.plotly_chart(
                        availability_fig,
                        use_container_width=True,
                        )

    st.subheader("Stations needing attention")

    if stations_df.empty:
        st.info("No station observations are available.")
    else:
        attention_df = stations_df[
                stations_df["availability_status"].isin(["empty", "low"])
                ].copy()

        attention_df = attention_df.sort_values(
                ["bike_availability_pct", "station_id"],
                ascending=[True, True],
                na_position="last"
                )
        attention_columns = [
                "station_id",
                "num_vehicles_available",
                "num_docks_available",
                "bike_availability_pct",
                "availability_status"
                ]
        st.caption(
                f"{len(attention_df):,} stations are empty or have low availability."
                )

        st.dataframe(
                attention_df[attention_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "station_id": st.column_config.TextColumn("Station ID"),
                    "num_vehicles_available": st.column_config.NumberColumn(
                        "Available bikes",
                        format="%d"
                        ),
                    "num:docks_available": st.column_config.NumberColumn(
                        "Free docks",
                        format="%d"
                        ),
                    "bike_availability_pct": st.column_config.NumberColumn(
                        "Bike availability",
                        format="%.2f%%"
                        ),
                    "availability_status": st.column_config.TextColumn(
                        "Status"
                        )
                    }
                )

# Tab 2: Historical Trends

with trends_tab:
    st.subheader("Network availability over time")

    if history_df.empty:
        st.info(
                "No historical aggregates are available yet."
                "Keep the producer and consumer running, then rebuild the dbt models."
                )
    else:
        history_df = history_df.sort_values("time_bucket")

        st.caption(
                f"{len(history_df):,} five-minute time buckets available."
                "True history becomes more informative as the pipeline collects data."
                )

        #Bikes and free docks
        network_fig = go.Figure()

        network_fig.add_trace(
                go.Scatter(
                    x=history_df["time_bucket"],
                    y=history_df["bikes_available"],
                    mode="lines+markers",
                    name="Available bikes",
                    hovertemplate=(
                        "%{x}<br>"
                        "Available bikes: %{y:,}"
                        "<extra></extra>"
                        )
                    )
                )
        network_fig.add_trace(
                go.Scatter(
                    x=history_df["time_bucket"],
                    y=history_df["docks_available"],
                    mode="lines+markers",
                    name="Free docks",
                    hovertemplate=(
                        "%{x}<br>"
                        "Free docks: %{y:,}"
                        "<extra></extra>"
                        )
                    )
                )
        network_fig.update_layout(
            title="Available bikes and free docks",
            xaxis_title="Time (UTC)",
            yaxis_title="Number of bikes / docks",
            hovermode="x unified",
            legend_title="Metric",
            margin=dict(l=10, r=10, t=50, b=10)
            )
        st.plotly_chart(
            network_fig,
            use_container_width=True
            )

        # Average bike availability
        availability_fig = px.line(
            history_df,
            x="time_bucket",
            y="avg_station_bike_availability_pct",
            markers=True,
            title="Average station bike availability",
            labels={
                "time_bucket": "Time (UTC)",
                "avg_station_bike_availability_pct": (
                    "Average bike availability (%)"
                    )
                }
            )
        availability_fig.update_layout(
            xaxis_title="Time (UTC)",
            yaxis_title="Average availability (%)",
            hovermode="x unified",
            margin=dict(l=10, r=20, t=50, b=10)
            )
        st.plotly_chart(
            availability_fig,
            use_container_width=True
            )

        #Station coverage over time
        coverage_fig = px.line(
                history_df,
                x="time_bucket",
                y="stations_reporting",
                markers=True,
                title="Stations reporting in each time bucket",
                labels={
                    "time_bucket": "Time (UTC)",
                    "stations_reporting": "Stations reporting",
                    }
                )
        coverage_fig.update_layout(
                xaxis_title="Time (UTC)",
                yaxis_title="Stations reporting",
                hovermode="x unified",
                margin=dict(l=10, r=10, t=50, b=10)
                )
        st.plotly_chart(
                coverage_fig,
                use_container_width=True
                )
        with st.expander("View historical aggregate data"):
            st.dataframe(
                    history_df,
                    use_container_width=True,
                    hide_index=True
                    )

# Tab 3: Station explorer

with stations_tab:
    st.subheader("Explore individual stations")

    if stations_df.empty:
        st.warning("No station observations are available yet.")
    else:
        filter_col, search_col = st.columns([1, 2])

        available_statuses = (
            stations_df["availability_status"]
            .dropna()
            .unique()
            .tolist()
        )

        with filter_col:
            selected_status = st.selectbox(
                "Availability status",
                options=["All"] + sorted(available_statuses),
            )

        with search_col:
            search_text = st.text_input(
                "Search station ID",
                placeholder="Enter a station ID",
            )

        filtered_df = stations_df.copy()

        if selected_status != "All":
            filtered_df = filtered_df[
                filtered_df["availability_status"] == selected_status
            ]

        if search_text.strip():
            filtered_df = filtered_df[
                filtered_df["station_id"]
                .astype(str)
                .str.contains(
                    search_text.strip(),
                    case=False,
                    na=False,
                )
            ]

        sort_col, order_col = st.columns([2, 1])

        sort_options = {
            "Available bikes": "num_vehicles_available",
            "Free docks": "num_docks_available",
            "Bike availability (%)": "bike_availability_pct",
            "Last reported": "last_reported",
            "Station ID": "station_id",
        }

        with sort_col:
            sort_label = st.selectbox(
                "Sort stations by",
                options=list(sort_options.keys()),
            )

        with order_col:
            descending = st.checkbox(
                "Descending",
                value=True,
            )

        filtered_df = filtered_df.sort_values(
            sort_options[sort_label],
            ascending=not descending,
            na_position="last",
        )

        st.caption(
            f"{len(filtered_df):,} of {len(stations_df):,} stations match your filters."
        )

        display_columns = [
            "station_id",
            "last_reported",
            "num_vehicles_available",
            "num_docks_available",
            "num_vehicles_disabled",
            "num_docks_disabled",
            "total_capacity",
            "bike_availability_pct",
            "dock_availability_pct",
            "availability_status",
        ]

        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "station_id": st.column_config.TextColumn(
                    "Station ID"
                ),
                "last_reported": st.column_config.DatetimeColumn(
                    "Last reported",
                    format="YYYY-MM-DD HH:mm:ss",
                ),
                "num_vehicles_available": st.column_config.NumberColumn(
                    "Available bikes",
                    format="%d",
                ),
                "num_docks_available": st.column_config.NumberColumn(
                    "Free docks",
                    format="%d",
                ),
                "num_vehicles_disabled": st.column_config.NumberColumn(
                    "Disabled bikes",
                    format="%d",
                ),
                "num_docks_disabled": st.column_config.NumberColumn(
                    "Disabled docks",
                    format="%d",
                ),
                "total_capacity": st.column_config.NumberColumn(
                    "Total capacity",
                    format="%d",
                ),
                "bike_availability_pct": st.column_config.NumberColumn(
                    "Bike availability",
                    format="%.2f%%",
                ),
                "dock_availability_pct": st.column_config.NumberColumn(
                    "Dock availability",
                    format="%.2f%%",
                ),
                "availability_status": st.column_config.TextColumn(
                    "Status"
                ),
            },
        )

        csv_data = filtered_df[display_columns].to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download filtered stations as CSV",
            data=csv_data,
            file_name="bicing_stations.csv",
            mime="text/csv",
        )

# Footer 

st.divider()
st.caption(
        "Data pipeline: Barcelona Bicing API → Kafka → PostgreSQL → dbt → Streamlit. "
        "Dashboard data is cached for up to 60 seconds."
        )


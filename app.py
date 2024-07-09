from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit interface
st.set_page_config(layout="wide")  # Set the page layout to wide

# Load data (you can replace this with your actual data source)
df = pd.read_excel(
    "data/ГРАФИК_ПРОИЗВОДСТВА_РАБОТ_без_денег.xlsx",
    sheet_name="БХ",
    index_col=0,
    header=3,
).reset_index(drop=True)

# Extract relevant columns and clean the data
df = df[["№ п/п", "Наименование работ", "Начало работ*", "Окончание работ"]]
df.columns = ["Task Number", "Task Name", "Start Date", "End Date"]

# Clean up the data
df = df.dropna(subset=["Task Number", "Task Name", "Start Date", "End Date"])
df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
df = df.dropna(subset=["Start Date", "End Date"])

# Determine if the task is a main task or a sub-task
df["Status"] = df["Task Number"].apply(
    lambda x: "Main Task" if float(x) - int(x) == 0 else "Sub-Task"
)

# Determine task status
current_date = pd.Timestamp.now()
map_not_main_task = df["Status"] != "Main Task"
df.loc[map_not_main_task, "Status"] = df.loc[map_not_main_task, "End Date"].apply(
    lambda x: "On Time" if x >= current_date else "Delayed"
)


# Function to truncate task names
def truncate_task_name(name, length=30):
    if len(name) > length:
        return name[:length] + "..."
    else:
        return name


df["Task Name"] = (
    df["Task Number"].apply(str)
    + ") "
    + df["Task Name"].apply(lambda x: truncate_task_name(x))
)

st.write(df)

# Streamlit interface
st.title("Project Schedule Gantt Chart")

# Select access level
access_level = st.selectbox("Select Access Level:", ["Viewer", "Editor"])

# Select time scale
time_scale = st.selectbox("Select Time Scale:", ["Month", "Quarter", "Year"])

color_discrete_map = {
    "On Time": "green",
    "Delayed": "red",
    "Main Task": "blue",
    "Sub-Task": "orange",
}


def update_xaxis(fig, scale):
    if scale == "Month":
        fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    elif scale == "Quarter":
        fig.update_xaxes(dtick="M3", tickformat="%b %Y")
    elif scale == "Year":
        fig.update_xaxes(dtick="M12", tickformat="%Y")
    return fig


def add_vertical_lines(fig, scale, start_date, end_date):
    if scale == "Month":
        months = pd.date_range(start=start_date, end=end_date, freq="MS")
        for date in months:
            fig.add_shape(
                type="line",
                x0=date,
                y0=0,
                x1=date,
                y1=1,
                xref="x",
                yref="paper",
            )
    elif scale == "Quarter":
        quarters = pd.date_range(start=start_date, end=end_date, freq="QS")
        for date in quarters:
            fig.add_shape(
                type="line",
                x0=date,
                y0=0,
                x1=date,
                y1=1,
                xref="x",
                yref="paper",
            )
    elif scale == "Year":
        years = pd.date_range(start=start_date, end=end_date, freq="YS")
        for date in years:
            fig.add_shape(
                type="line",
                x0=date,
                y0=0,
                x1=date,
                y1=1,
                xref="x",
                yref="paper",
            )

    # Add current date vertical line
    current_date = pd.Timestamp.now()
    fig.add_shape(
        type="line",
        x0=current_date,
        y0=0,
        x1=current_date,
        y1=1,
        line=dict(color="red", width=2),
        xref="x",
        yref="paper",
    )

    # Add current date label
    fig.add_annotation(
        x=current_date,
        y=-0.1,  # Position it below the plot
        text=current_date.strftime("%Y-%m-%d"),
        showarrow=False,
        xref="x",
        yref="paper",
        font=dict(color="red", size=10),
    )

    return fig


# Define the order of tasks based on the Task Number
task_order = df.sort_values(by="Task Number")["Task Name"].tolist()

# Calculate the height of the chart
chart_height = 50 + len(df) * 20  # Adjust multiplier as needed for better spacing

if access_level == "Viewer":
    st.write("You are in viewer mode. Here is the project schedule:")
    fig = px.timeline(
        df,
        x_start="Start Date",
        x_end="End Date",
        y="Task Name",
        color="Status",
        title="Gantt Chart",
        color_discrete_map=color_discrete_map,
        category_orders={"Task Name": task_order},
    )
    fig.update_layout(height=chart_height)

    # Determine the min and max dates from the data
    min_date = df["Start Date"].min()
    max_date = df["End Date"].max()

    fig = update_xaxis(fig, time_scale)
    fig = add_vertical_lines(fig, time_scale, min_date, max_date)

    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("You are in editor mode. You can update the project schedule:")

    # Editable data table
    edited_df = st.experimental_data_editor(df, num_rows="dynamic")

    # Save updated data (you can modify this to save to a file or database)
    if st.button("Save Changes"):
        edited_df.to_csv("updated_project_schedule.csv", index=False)
        st.success("Changes saved successfully!")

    fig = px.timeline(
        edited_df,
        x_start="Start Date",
        x_end="End Date",
        y="Task Name",
        color="Status",
        title="Gantt Chart",
        color_discrete_map=color_discrete_map,
        category_orders={"Task Name": task_order},
    )
    fig.update_layout(height=chart_height)

    # Determine the min and max dates from the data
    min_date = edited_df["Start Date"].min()
    max_date = edited_df["End Date"].max()

    fig = update_xaxis(fig, time_scale)
    fig = add_vertical_lines(fig, time_scale, min_date, max_date)

    st.plotly_chart(fig, use_container_width=True)

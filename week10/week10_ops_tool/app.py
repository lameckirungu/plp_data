"""PumpGuard Ops Streamlit application."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from pumpguard.config import SETTINGS
from pumpguard.data import TelemetryValidationError, load_csv, validate_telemetry
from pumpguard.features import engineer_features
from pumpguard.model import ModelBundle, score_latest_assets, train_model

st.set_page_config(page_title=SETTINGS.app_title, page_icon="⚙️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1400px;}
    [data-testid="stMetric"] {background: white; border: 1px solid #e5e9ef;
      padding: 14px; border-radius: 12px;}
    .pg-note {padding: 12px 16px; background: #fff4eb; border-left: 4px solid #e36b2c;
      border-radius: 6px; margin-bottom: 14px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Training the grouped XGBoost risk model…")
def get_model() -> ModelBundle:
    history = pd.read_csv(SETTINGS.training_data, parse_dates=["timestamp"])
    return train_model(history, SETTINGS.random_seed, SETTINGS.cv_folds)


@st.cache_data
def get_demo() -> pd.DataFrame:
    return validate_telemetry(load_csv(SETTINGS.demo_data)).data


def read_source() -> tuple[pd.DataFrame, tuple[str, ...], str]:
    st.sidebar.header("Telemetry source")
    mode = st.sidebar.radio("Choose data", ["Bundled 24-pump demo", "Upload CSV"])
    if mode == "Bundled 24-pump demo":
        return get_demo(), (), "Bundled synthetic demo"

    upload = st.sidebar.file_uploader("Upload telemetry CSV", type=["csv"])
    st.sidebar.download_button(
        "Download CSV template",
        data=pd.DataFrame(columns=get_demo().columns).to_csv(index=False),
        file_name="pumpguard_upload_template.csv",
        mime="text/csv",
    )
    if upload is None:
        st.info("Upload a telemetry CSV or switch to the bundled demo.")
        st.stop()
    result = validate_telemetry(load_csv(upload))
    return result.data, result.warnings, upload.name


st.title(f"⚙️ {SETTINGS.app_title}")
st.caption("AI-assisted predictive maintenance triage for operational pump fleets")
st.markdown(
    "<div class='pg-note'><b>Demonstration only.</b> Data and model performance are "
    "synthetic and are not validated KPC production results. A maintenance professional "
    "must review every recommendation.</div>",
    unsafe_allow_html=True,
)

try:
    telemetry, warnings, source_name = read_source()
    model = get_model()
    scored = score_latest_assets(model, telemetry)
except TelemetryValidationError as exc:
    st.error("The telemetry could not be scored.")
    for message in exc.messages:
        st.write(f"- {message}")
    st.stop()
except Exception as exc:
    st.error(f"PumpGuard could not initialize: {exc}")
    st.stop()

for warning in warnings:
    st.warning(warning)

st.sidebar.divider()
st.sidebar.header("Queue filters")
selected_depots = st.sidebar.multiselect(
    "Depot", sorted(scored.depot.unique()), default=sorted(scored.depot.unique())
)
band_order = ["Critical", "Watch", "Normal"]
selected_bands = st.sidebar.multiselect("Risk band", band_order, default=band_order)
filtered = scored[
    scored.depot.isin(selected_depots) & scored.risk_band.isin(selected_bands)
].copy()

operations_tab, asset_tab, model_tab = st.tabs(
    ["Operations queue", "Asset detail", "Model card"]
)

with operations_tab:
    st.caption(f"Source: {source_name} · latest reading scored for each asset")
    critical = int((filtered.risk_band == "Critical").sum())
    watch = int((filtered.risk_band == "Watch").sum())
    highest_depot = (
        filtered.groupby("depot").risk_probability.mean().idxmax() if not filtered.empty else "—"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pumps in queue", len(filtered))
    c2.metric("Critical", critical)
    c3.metric("Watch", watch)
    c4.metric("Highest average-risk depot", highest_depot)

    if filtered.empty:
        st.warning("No pumps match the selected filters.")
    else:
        chart_col, depot_col = st.columns(2)
        with chart_col:
            risk_chart = (
                alt.Chart(filtered)
                .mark_bar()
                .encode(
                    x=alt.X("risk_probability:Q", title="7-day risk", axis=alt.Axis(format="%")),
                    y=alt.Y("asset_id:N", title=None, sort="-x"),
                    color=alt.Color(
                        "risk_band:N",
                        title="Risk",
                        scale=alt.Scale(
                            domain=band_order,
                            range=["#c83e32", "#e6a23c", "#4a8f62"],
                        ),
                    ),
                    tooltip=["asset_id", "depot", alt.Tooltip("risk_probability:Q", format=".1%")],
                )
                .properties(title="Latest 7-day failure risk by pump", height=420)
            )
            threshold_rule = (
                alt.Chart(pd.DataFrame({"threshold": [model.threshold]}))
                .mark_rule(color="#c83e32", strokeDash=[6, 4])
                .encode(x="threshold:Q")
            )
            st.altair_chart(risk_chart + threshold_rule, width="stretch")
        with depot_col:
            depot_risk = filtered.groupby("depot", as_index=False).agg(
                average_risk=("risk_probability", "mean"), pumps=("asset_id", "count")
            )
            depot_chart = (
                alt.Chart(depot_risk)
                .mark_bar()
                .encode(
                    x=alt.X("depot:N", title=None, sort="-y"),
                    y=alt.Y("average_risk:Q", title="Average risk", axis=alt.Axis(format="%")),
                    color=alt.Color("average_risk:Q", scale=alt.Scale(scheme="oranges"), legend=None),
                    tooltip=["depot", "pumps", alt.Tooltip("average_risk:Q", format=".1%")],
                )
                .properties(title="Average risk by depot", height=420)
            )
            st.altair_chart(depot_chart, width="stretch")

        st.subheader("Prioritized maintenance queue")
        display_queue = filtered.copy()
        display_queue["risk_probability"] = display_queue["risk_probability"].map(
            lambda value: f"{value:.1%}"
        )
        st.dataframe(display_queue, width="stretch", hide_index=True)
        st.download_button(
            "Download filtered action queue",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="pumpguard_maintenance_queue.csv",
            mime="text/csv",
        )

    st.info(
        "Illustrative workflow estimate: prioritize this 24-pump demo in under 2 minutes "
        "versus approximately 30 minutes of manual spreadsheet review. Validate the baseline "
        "with a real maintenance team before using it as an organizational claim."
    )

with asset_tab:
    asset = st.selectbox("Select a pump", scored.asset_id.tolist())
    asset_score = scored.loc[scored.asset_id == asset].iloc[0]
    asset_history = engineer_features(telemetry)
    asset_history = asset_history[asset_history.asset_id == asset].sort_values("timestamp")
    a1, a2, a3 = st.columns(3)
    a1.metric("7-day failure risk", f"{asset_score.risk_probability:.1%}")
    a2.metric("Risk band", asset_score.risk_band)
    a3.metric("Action", asset_score.recommended_action)
    st.write(f"**Main model contributions:** {asset_score.top_risk_drivers}")
    trend = asset_history.melt(
        id_vars=["timestamp"],
        value_vars=["vibration_g", "vibration_roll_mean_6", "temperature_c", "temp_roll_mean_6"],
        var_name="signal",
        value_name="value",
    )
    telemetry_chart = (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("timestamp:T", title="Reading time"),
            y=alt.Y("value:Q", title="Sensor value"),
            color=alt.Color("signal:N", title="Signal"),
            tooltip=[alt.Tooltip("timestamp:T"), "signal", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(title="Recent telemetry", height=380)
    )
    st.altair_chart(telemetry_chart, width="stretch")
    st.dataframe(asset_history.tail(6), width="stretch", hide_index=True)

with model_tab:
    st.subheader("Model governance card")
    st.write(
        "XGBoost with SMOTE, evaluated using stratified grouped cross-validation. Grouping "
        "keeps each pump in one fold and prevents its time-series rows leaking across evaluation."
    )
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("ROC-AUC", f"{model.metrics['roc_auc']:.3f}")
    m2.metric("Precision", f"{model.metrics['precision']:.1%}")
    m3.metric("Recall", f"{model.metrics['recall']:.1%}")
    m4.metric("False-positive rate", f"{model.metrics['false_positive_rate']:.1%}")
    m5.metric("Threshold", f"{model.threshold:.2f}")
    st.write(model.threshold_note)
    st.markdown(
        """
        **Controls and limitations**

        - Outcome proxies (`health_status`, `fault_type`, and time-to-failure) are excluded.
        - Risk contributions describe this model's reasoning; they do not prove physical causality.
        - The data is physics-informed and synthetic. Production use requires real maintenance logs,
          drift monitoring, calibration, access controls, and engineering approval.
        - Critical means “review first,” not “automatically shut down equipment.”
        """
    )

"""Public, read-only model comparison for the BSAD 6153 student project."""
from datetime import datetime, timedelta, timezone

import streamlit as st

import catalogue

CACHE_SECONDS = 300


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def last_check():
    return catalogue.latest_sync()


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def ranked_entries(minimum, sampled):
    return catalogue.shortlist(minimum, sampled)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def sampled_routes(model):
    return catalogue.routes(model)


def rate(value):
    if value is None:
        return "Not listed"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def show_shortlist():
    st.header("Which tool models cost least?")
    st.write("Ranked by the listed base cost for 1 million input tokens plus 250,000 output "
             "tokens across requests, not a single prompt. Entries with unknown rates are excluded.")
    minimum = st.selectbox("Minimum advertised context (tokens)", (128000, 256000, 1000000),
                           format_func=lambda n: f"{n:,}", key="minimum")
    sampled = st.checkbox("Only entries with a sampled route that advertises tools", key="sampled")
    rows = ranked_entries(minimum, sampled)
    if not rows:
        st.info("No entries match these filters. Try a lower context minimum or uncheck the route filter.")
        return []
    st.caption("Up to 20 lowest-cost entries; ties are ordered by catalogue ID. All prices in USD.")
    st.dataframe([{"Catalogue ID": model, "Context (tokens)": f"{context:,}",
                   "Input / 1M": rate(prompt), "Output / 1M": rate(completion), "Example cost": rate(cost)}
                  for model, context, prompt, completion, cost in rows], hide_index=True)
    return [row[0] for row in rows]


def show_routes(models):
    st.header("Which provider routes advertise tools?")
    st.caption("These limits and base prices describe sampled routes, not the model's catalogue listing. "
               "Unknown rates are not zero. Prices are USD per million tokens.")
    if not models:
        st.info("A matching shortlist entry is needed before comparing routes.")
        return
    model = st.selectbox("Model from the shortlist", models, key="model")
    rows = sampled_routes(model)
    if not rows:
        st.info("No matching route in our sample. This does not mean the model has no providers. "
                "Try the sampled-route filter above.")
        return
    st.dataframe([{"Provider": provider, "Tag": tag or "Not listed", "Route name": name or "Not listed",
                   "Tier": tier or "Not listed", "Context (tokens)": f"{ctx:,}" if ctx is not None else "Not listed",
                   "Max output (tokens)": f"{cap:,}" if cap is not None else "Not listed",
                   "Input / 1M": rate(prompt), "Output / 1M": rate(completion)}
                  for provider, tag, name, tier, ctx, cap, prompt, completion in rows], hide_index=True)


def freshness_banner(checked):
    if checked is None:
        st.warning("No successful sync has been recorded. Catalogue freshness is unknown.")
        return
    checked = checked.astimezone(timezone.utc)
    age = datetime.now(timezone.utc) - checked
    stamp = checked.strftime("%Y-%m-%d %H:%M:%S UTC")
    if age < timedelta(0):
        st.warning(f"Last successful check: {stamp}. That time is in the future; freshness is uncertain.")
        return
    hours, minutes = divmod(int(age.total_seconds() // 60), 60)
    message = f"Last successful check: {stamp} ({hours}h {minutes}m ago)."
    if age > timedelta(hours=24):
        st.warning(message + " Over 24 hours old: listings may be out of date.")
    else:
        st.success(message)


st.set_page_config(page_title="Model catalogue", layout="wide")
st.title("Model catalogue")
st.caption("Compare advertised costs and limits for text models that support tools.")
try:
    freshness_banner(last_check())
    show_routes(show_shortlist())
except catalogue.CatalogueUnavailable:
    st.warning("The catalogue is unavailable right now. Please try again in a few minutes.")

with st.expander("About this catalogue"):
    st.markdown(
        "This student project uses public [OpenRouter model and provider metadata](https://openrouter.ai/models). "
        "The catalogue is checked daily; a new check does not mean every model changed. "
        "Provider coverage is a selected, recent sample. Listings are not coding benchmarks, "
        "final bills or guarantees of availability. No prompts are sent. On Render's free tier "
        "the first visit after an idle period can take about a minute."
    )

import json
from dataclasses import dataclass
from datetime import date, datetime

import streamlit as st

from urbanflow.config import (
    DATA_DIR,
    AnalysisPeriod,
)

METADATA_PATH = (
    DATA_DIR
    / "analytics"
    / "refresh_metadata.json"
)

@dataclass(
    frozen=True,
)
class RefreshContext:
    period: AnalysisPeriod
    last_refresh: datetime | None
    data_version: str

    @property
    def start_date(
        self,
    ) -> date:
        return self.period.start_date

    @property
    def end_date(
        self,
    ) -> date:
        return self.period.end_date

    @property
    def period_label(
        self,
    ) -> str:
        return self.start_date.strftime(
            "%B %Y"
        )

    @property
    def last_refresh_label(
        self,
    ) -> str:
        if self.last_refresh is None:
            return "Unknown"

        return self.last_refresh.strftime(
            "%b %d, %Y %H:%M"
        )

def load_refresh_context() -> RefreshContext:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Refresh metadata was not found. "
            "Run scripts/update_pipeline.py first."
        )

    payload = json.loads(
        METADATA_PATH.read_text(
            encoding="utf-8"
        )
    )

    active_period = payload.get(
        "active_period"
    )

    if not active_period:
        raise ValueError(
            "refresh_metadata.json does not "
            "contain active_period."
        )

    period = AnalysisPeriod.from_yyyymm(
        active_period.replace(
            "-",
            "",
        )
    )

    last_refresh_value = payload.get(
        "last_refresh"
    )

    last_refresh = None

    if last_refresh_value:
        last_refresh = (
            datetime.fromisoformat(
                last_refresh_value
            )
        )

    data_version = (
        last_refresh_value
        or str(
            METADATA_PATH
            .stat()
            .st_mtime_ns
        )
    )

    return RefreshContext(
        period=period,
        last_refresh=last_refresh,
        data_version=data_version,
    )

def sync_refresh_cache(
    context: RefreshContext,
) -> None:
    session_key = (
        "_urbanflow_data_version"
    )

    previous_version = (
        st.session_state.get(
            session_key
        )
    )

    if (
        previous_version
        != context.data_version
    ):
        st.cache_data.clear()
        st.cache_resource.clear()

        st.session_state[
            session_key
        ] = context.data_version
from datetime import timedelta
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.graph_objects as go  # type: ignore
import streamlit as st
from numpy.typing import NDArray

from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.core.plugins.input.base import InputPluginRuntimeError
from eventum.core.plugins.input.time_pattern import TimePatternInputPlugin
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from eventum.utils.numpy_time import timedelta_to_seconds
from eventum.utils.relative_time import parse_relative_time


def _hash_config(config: TimePatternConfig) -> int:
    return hash(
        (
            config.oscillator,
            config.multiplier,
            config.randomizer,
            config.spreader
        )
    )


@st.cache_data(
    max_entries=1024,
    show_spinner='Calculating distribution',
    persist=True,
    hash_funcs={TimePatternConfig: _hash_config}
)
def _calculate_sample(config: TimePatternConfig) -> NDArray[np.datetime64]:
    """Calculate sample for specified `config`. If finite sample cannot
    be calculated then empty list is returned and corresponding
    notification is displayed."""
    pattern = TimePatternInputPlugin(config)
    data = []
    try:
        pattern.sample(lambda ts: data.append(ts))
    except InputPluginRuntimeError as e:
        default_notifier(
            message=(
                'Skip distribution calculation '
                f'for pattern "{config.label}": {e}'
            ),
            level=NotificationLevel.WARNING
        )
    return np.array(data)


class DistributionHistogram(BaseComponent):
    """Component for visualizing time patterns distribution."""
    _AUTO_SPAN_SAMPLE_SIZE = 100

    _SHOW_PROPS = {
        'configs': Iterable[TimePatternConfig],
        'colors': Iterable[str],
        'use_custom_span': bool,
        'span_expression': str
    }

    def _resample_series(self, series: pd.Series) -> pd.Series:
        """Resample series corresponding to specified span options. If
        auto span is used, then sample is resampled according to
        `_AUTO_SPAN_SAMPLE_SIZE`, otherwise `span_expression` prop is
        used.
        """
        use_custom_span: bool = self._props['use_custom_span']
        span_expression: str = self._props['span_expression']

        if use_custom_span:
            custom_span = parse_relative_time(span_expression)
            return series.resample(rule=custom_span).sum()
        else:
            auto_span = timedelta(
                seconds=timedelta_to_seconds(
                    (series[-1] - series[0]) / self._AUTO_SPAN_SAMPLE_SIZE
                )
            )
            return series.resample(rule=auto_span).sum()

    def _calculate_bins_count(self, timedelta: np.timedelta64) -> int:
        """Calculate count of bins in histogram for sample with
        specified `timedelta` range (from start to end) according to
        span configuration.
        """
        use_custom_span: bool = self._props['use_custom_span']
        span_expression: str = self._props['span_expression']

        if use_custom_span:
            return int(
                np.ceil(timedelta / parse_relative_time(span_expression))
            )
        else:
            return self._AUTO_SPAN_SAMPLE_SIZE

    def _show(self) -> None:
        configs: Iterable[TimePatternConfig] = self._props['configs']
        colors: Iterable[str] = self._props['colors']

        series_list: list[pd.Series] = []
        labels: list[str] = []
        total_events = 0

        min_timestamp = np.datetime64('9999-12-31')
        max_timestamp = np.datetime64('0000-01-01')

        for config in configs:
            series = pd.Series(1, index=_calculate_sample(config))
            total_events += series.size

            series = self._resample_series(series)

            min_timestamp = min(min_timestamp, series[0])
            max_timestamp = max(max_timestamp, series[-1])

            series_list.append(series)
            labels.append(config.label)

        bins_count = self._calculate_bins_count(
            timedelta=(max_timestamp - min_timestamp)
        )

        fig = go.Figure()

        for series, label, color in zip(series_list, labels, colors):
            fig.add_trace(
                go.Histogram(
                    x=series.index,
                    y=series.values,
                    histfunc='sum',
                    name=label,
                    nbinsx=bins_count,
                    marker_color=color
                )
            )

        fig.update_layout(barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns([8, 2])
        col1.text(f'Total events: {total_events}')
        col2.button(
            'Recalculate',
            use_container_width=True,
            key=self._wk.get_ephemeral(),
            on_click=_calculate_sample.clear    # type: ignore
        )
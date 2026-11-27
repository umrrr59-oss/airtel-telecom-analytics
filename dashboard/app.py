            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
        """, (selected_month,) + params)
        m = month_stats.iloc[0] if not month_stats.empty else {}
        k1,k2,k3 = st.columns(3, gap="medium")
        with k1:
            st.metric("Active Subscribers", f"{int(m.get('active_subscribers') or 0):,}")
            st.markdown('<div class="card-note">Distinct subscribers with at least one usage record in the selected month.</div>', unsafe_allow_html=True)
        with k2:
            st.metric("Data Carried", f"{float(m.get('total_mb') or 0)/1_000_000:,.3f} TB")
            st.markdown('<div class="card-note">Decimal conversion: 1 TB = 1,000,000 MB.</div>', unsafe_allow_html=True)
        with k3:
            st.metric("Data per Usage-Day", fmt_gb(float(m.get("mb_per_usage_day") or 0)))
            st.markdown(f'<div class="card-note">{int(m.get("usage_days") or 0):,} validated usage-days in this month and filter selection.</div>', unsafe_allow_html=True)

        daily = q(f"""
            SELECT u.usage_date, SUM(u.data_mb)/1024.0 AS data_gb,
                   COUNT(DISTINCT u.customer_id) AS subscribers,
                   COUNT(*) AS usage_days
            FROM usage_daily u
            JOIN customer_features cf ON cf.customer_id=u.customer_id
            WHERE strftime('%Y-%m',u.usage_date)=? {where}
            GROUP BY u.usage_date ORDER BY u.usage_date
        """, (selected_month,) + params)
        ab = q(f"""
            SELECT cf.ab_group, COUNT(DISTINCT um.customer_id) AS subscribers,
                   SUM(um.total_mb)/1024.0 AS data_gb,
                   SUM(um.usage_days) AS usage_days,
                   SUM(um.total_mb)/NULLIF(SUM(um.usage_days),0) AS mb_per_usage_day
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
            GROUP BY cf.ab_group ORDER BY cf.ab_group
        """, (selected_month,) + params)
        device = q(f"""
            SELECT cf.device_type, COUNT(DISTINCT um.customer_id) AS subscribers,
                   SUM(um.total_mb)/1024.0 AS data_gb,
                   SUM(um.usage_days) AS usage_days
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
            GROUP BY cf.device_type ORDER BY data_gb DESC
        """, (selected_month,) + params)

        top_left, top_right = st.columns([1.25, 1], gap="medium")
        with top_left:
            st.subheader(f"Daily data load — {selected_month}")
            if not daily.empty:
                daily["usage_date"] = pd.to_datetime(daily["usage_date"])
                min_day, max_day = daily["usage_date"].min().date(), daily["usage_date"].max().date()
                date_selection = st.date_input("Daily load · Date range", value=(min_day, max_day),
                                               min_value=min_day, max_value=max_day, key="daily_date_filter")
                if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
                    daily = daily[(daily["usage_date"].dt.date >= date_selection[0]) &
                                  (daily["usage_date"].dt.date <= date_selection[1])]
                fig4 = px.area(daily, x="usage_date", y="data_gb",
                               labels={"usage_date":"Date","data_gb":"Data carried (GB)"},
                               color_discrete_sequence=[BLUE],
                               hover_data={"subscribers":":,","usage_days":":,"})
                fig4.update_traces(line=dict(color=BLUE, width=2), fillcolor="rgba(22,119,232,.18)")
                fig4.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white",
                                   plot_bgcolor="white", font=dict(color=INK))
                fig4.update_yaxes(gridcolor="#E8EBF2")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No daily usage records for this selection.")
        with top_right:
            st.subheader("A/B group comparison")
            if not ab.empty:
                ab_metric = st.selectbox("A/B comparison · Metric",
                    options=["data_gb", "subscribers", "usage_days", "mb_per_usage_day"],
                    format_func=lambda x: {"data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                                           "usage_days":"Usage-days", "mb_per_usage_day":"MB per usage-day"}[x],
                    key="ab_metric_filter")
                ab_groups = st.multiselect("A/B comparison · Groups",
                    sorted(ab["ab_group"].dropna().unique().tolist()),
                    default=sorted(ab["ab_group"].dropna().unique().tolist()), key="ab_group_filter")
                ab = ab[ab["ab_group"].isin(ab_groups)]
                fig5 = px.bar(ab, x="ab_group", y=ab_metric, color="ab_group",
                              color_discrete_map={"A":BLUE,"B":RED},
                              labels={"ab_group":"Experiment group", ab_metric: {
                                  "data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                                  "usage_days":"Usage-days", "mb_per_usage_day":"MB per usage-day"}[ab_metric]},
                              hover_data={"subscribers":":,","usage_days":":,","mb_per_usage_day":":.1f"})
                fig5.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white",
                                   plot_bgcolor="white", showlegend=False, font=dict(color=INK))
                fig5.update_yaxes(gridcolor="#E8EBF2")
                st.plotly_chart(fig5, use_container_width=True)
                st.dataframe(ab.rename(columns={"ab_group":"Group","subscribers":"Subscribers",
                    "data_gb":"Data (GB)","usage_days":"Usage-days","mb_per_usage_day":"MB / usage-day"}),
                    hide_index=True, use_container_width=True)
            else:
                st.info("No A/B comparison data for this selection.")

        st.subheader("Device usage comparison")
        if not device.empty:
            dv1, dv2 = st.columns(2)
            device_types = dv1.multiselect("Device usage · Device types",
                sorted(device["device_type"].dropna().unique().tolist()),
                default=sorted(device["device_type"].dropna().unique().tolist()), key="device_type_filter")
            device_metric = dv2.selectbox("Device usage · Metric",
                options=["data_gb", "subscribers", "usage_days"],
                format_func=lambda x: {"data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                                       "usage_days":"Usage-days"}[x], key="device_metric_filter")
            device = device[device["device_type"].isin(device_types)]
        if not device.empty:
            fig6 = px.bar(device, x="device_type", y=device_metric, color="device_type",
                          color_discrete_sequence=[BLUE, ORANGE],
                          labels={"device_type":"Device category", device_metric: {
                              "data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                              "usage_days":"Usage-days"}[device_metric]},
                          hover_data={"subscribers":":,","usage_days":":,"})
            fig6.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white",
                               plot_bgcolor="white", showlegend=False, font=dict(color=INK))
            fig6.update_yaxes(gridcolor="#E8EBF2")
            st.plotly_chart(fig6, use_container_width=True)
            st.caption("Device categories are taken from customer_features.device_type.")
        else:
            st.info("No device comparison data for this selection.")

st.divider()
st.caption("Airtel Telecom Analytics · Group 3 · Domain C — Network Usage | Metrics are queried from the supplied SQLite database.")

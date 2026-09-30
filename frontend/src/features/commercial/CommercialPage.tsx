import React from 'react';
import { useRevenue } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { inrFromLakhs, meters, pct, signed } from '../../lib/format';
import type { RevenueLossModuleData, StockCategoryItem } from '../../types/revenueLoss';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, Meter, StatusPill, toneOf } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { SplitBar, TrendChart } from '../../design/charts/Charts';
import { AttentionList } from '../quality/QualityPage';

export const CommercialPage: React.FC = () => {
  const [period] = usePeriod();
  const query = useRevenue(period);
  return (
    <>
      <PageHeader title="Sales & Finance" description="Revenue, order fulfilment, receivables and inventory value" showPeriod />
      <QueryView query={query}>{(d) => <CommercialBody data={d} />}</QueryView>
    </>
  );
};

const CommercialBody: React.FC<{ data: RevenueLossModuleData }> = ({ data }) => {
  const r = data.revenue_summary;
  const d = data.dispatch_orders;
  const m = data.money_position;
  return (
    <div className="space-y-4">
      <KpiGrid>
        <Kpi
          label="Revenue"
          value={inrFromLakhs(r.revenue_amount_lakhs)}
          delta={{
            text: signed(r.change_pct, (v) => `${v.toFixed(1)}%`),
            direction: r.change_pct > 0 ? 'up' : r.change_pct < 0 ? 'down' : 'flat',
            good: r.change_pct >= 0,
          }}
        />
        <Kpi label="Orders booked" value={meters(d.orders_meters)} />
        <Kpi
          label="Dispatched"
          value={meters(d.dispatched_meters)}
          hint={`${pct(d.fulfillment_pct)} fulfilled`}
          status={d.fulfillment_pct < 80 ? 'warn' : 'ok'}
        />
        <Kpi label="Pending dispatch" value={meters(d.pending_meters)} />
        <Kpi label="Receivables" value={inrFromLakhs(m.outstanding_lakhs)} hint="outstanding" />
        <Kpi label="Collected" value={inrFromLakhs(m.collected_lakhs)} hint={`${pct(m.collection_rate_pct)} collection rate`} />
      </KpiGrid>

      <ChartPanel
        title="Revenue trend"
        subtitle="Daily revenue against the same days of the previous period"
        rows={data.revenue_trend}
        rowKey={(x) => x.date_label}
        exportName="revenue-trend"
        chart={
          <TrendChart
            data={data.revenue_trend}
            xKey="date_label"
            format={inrFromLakhs}
            series={[
              { key: 'revenue_lakhs', label: 'This period', color: 0 },
              { key: 'previous_lakhs', label: 'Previous period', color: 'muted' },
            ]}
            height={260}
          />
        }
        columns={[
          { key: 'd', header: 'Date', value: (x) => x.date_label, render: (x) => x.date_label },
          { key: 'r', header: 'Revenue', align: 'right', value: (x) => x.revenue_lakhs, render: (x) => inrFromLakhs(x.revenue_lakhs) },
          { key: 'p', header: 'Previous', align: 'right', value: (x) => x.previous_lakhs, render: (x) => inrFromLakhs(x.previous_lakhs) },
          {
            key: 'c',
            header: 'Change',
            align: 'right',
            value: (x) => x.change_pct,
            render: (x) => signed(x.change_pct, (v) => `${v.toFixed(1)}%`),
          },
        ]}
      />

      <div className="grid items-start gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Order fulfilment" subtitle={`${meters(d.orders_meters)} ordered`} />
          <CardBody>
            <SplitBar
              format={meters}
              parts={[
                { label: 'Dispatched', value: d.dispatched_meters, color: 0 },
                { label: 'Pending', value: d.pending_meters, color: 'muted' },
              ]}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Cash position" subtitle={`${pct(m.collection_rate_pct)} of billed amount collected`} />
          <CardBody>
            <SplitBar
              format={inrFromLakhs}
              parts={[
                { label: 'Collected', value: m.collected_lakhs, color: 0 },
                { label: 'Outstanding', value: m.outstanding_lakhs, color: 1 },
              ]}
            />
          </CardBody>
        </Card>
        <AttentionList title="Needs attention" items={data.needs_attention} className="" />
      </div>

      <Card>
        <CardHeader title="Inventory value vs limit" subtitle="Working capital locked in stock" />
        <DataTable<StockCategoryItem>
          rows={data.stock_position}
          rowKey={(x) => x.category}
          exportName="stock-position"
          columns={[
            { key: 'c', header: 'Category', value: (x) => x.category, render: (x) => <span className="font-medium">{x.category}</span> },
            {
              key: 'v',
              header: 'Value',
              align: 'right',
              value: (x) => x.current_value_lakhs,
              render: (x) => inrFromLakhs(x.current_value_lakhs),
            },
            {
              key: 'l',
              header: 'Limit',
              align: 'right',
              value: (x) => x.limit_value_lakhs,
              render: (x) => inrFromLakhs(x.limit_value_lakhs),
            },
            {
              key: 'u',
              header: 'Utilisation',
              value: (x) => (x.limit_value_lakhs ? x.current_value_lakhs / x.limit_value_lakhs : 0),
              render: (x) => (
                <div className="flex w-40 items-center gap-2">
                  <Meter
                    value={x.current_value_lakhs}
                    max={Math.max(x.current_value_lakhs, x.limit_value_lakhs) * 1.1}
                    marker={x.limit_value_lakhs}
                    tone={toneOf(x.status)}
                  />
                  <span className="num w-12 shrink-0 text-right text-xs">
                    {x.limit_value_lakhs ? `${Math.round((x.current_value_lakhs / x.limit_value_lakhs) * 100)}%` : '—'}
                  </span>
                </div>
              ),
            },
            { key: 's', header: 'Status', value: (x) => x.status, render: (x) => <StatusPill status={x.status} /> },
          ]}
        />
      </Card>
    </div>
  );
};

import React from 'react';
import { Gauge, Wind, Zap } from 'lucide-react';
import { useEnergy } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { DataTable } from '../../design/DataTable';
import { Card, CardBody, CardHeader, EmptyState, Notice, StatusPill } from '../../design/ui';
import { FilterBar, useFilters } from '../common/filters';
import { PageTitle, fmt, periodText } from '../common/parts';

/** Air and energy: measured values only. Without measurements the page says exactly what is needed, and shows no estimate. */
export const EnergyPage: React.FC = () => {
  const filters = useFilters();
  const q = useEnergy(filters);
  return (
    <>
      <PageTitle title="Air and energy" subtitle="Compressed air and electricity per meter, from measured data only. Nothing here is estimated from RPM or efficiency."
        actions={<FilterBar show={['category']} />} />
      <QueryView query={q}>
        {(d) => (
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader title={<span className="inline-flex items-center gap-1.5"><Wind className="size-4" /> Compressed air</span>} subtitle={periodText(d.period)} />
                <CardBody className="space-y-2 text-sm">
                  {d.air.status === 'MEASURED' ? <StatusPill tone="ok" label="Measured data available" /> : <StatusPill tone="neutral" label="Not measured" />}
                  <p className="text-ink-2">{fmt.n(d.air.records_with_measured_air)} loom-shifts with measured air consumption.</p>
                  {d.air.reported_zero_records > 0 && (
                    <Notice tone="warn">The Tsudakoma export has an air-consumption column but reports 0 Nm³ for every loom ({fmt.n(d.air.reported_zero_records)} loom-shifts). That means it is not being measured, so it is stored as unavailable.</Notice>
                  )}
                </CardBody>
              </Card>
              <Card>
                <CardHeader title={<span className="inline-flex items-center gap-1.5"><Zap className="size-4" /> Electricity</span>} subtitle={periodText(d.period)} />
                <CardBody className="space-y-2 text-sm">
                  {d.energy.status === 'AVAILABLE' ? <StatusPill tone="ok" label={`${d.energy.readings} readings`} /> : <StatusPill tone="neutral" label="No meter readings" />}
                  {d.energy.kwh != null && <p className="num text-ink">{fmt.n(d.energy.kwh)} kWh ({d.energy.basis.join(', ')})</p>}
                </CardBody>
              </Card>
            </div>
            {d.air.per_loom.length > 0 ? (
              <Card>
                <CardHeader title="Air per meter by loom" subtitle="Measured Nm³ / meters woven over the same loom-shifts" />
                <CardBody>
                  <DataTable dense rows={d.air.per_loom} rowKey={(r: any) => r.loom_code} exportName="air-per-meter"
                    columns={[
                      { key: 'l', header: 'Loom', render: (r: any) => r.loom_code, value: (r: any) => r.loom_code },
                      { key: 'a', header: 'Air Nm³', align: 'right', render: (r: any) => fmt.n(r.air_nm3, 1), value: (r: any) => r.air_nm3 },
                      { key: 'm', header: 'Meters', align: 'right', render: (r: any) => fmt.n(r.meters), value: (r: any) => r.meters },
                      { key: 'r', header: 'Nm³ / m', align: 'right', render: (r: any) => fmt.n(r.nm3_per_meter, 3), value: (r: any) => r.nm3_per_meter },
                    ]} />
                </CardBody>
              </Card>
            ) : (
              <Card>
                <CardHeader title={<span className="inline-flex items-center gap-1.5"><Gauge className="size-4" /> What is needed for air and energy analysis</span>}
                  subtitle="These analyses (cost per meter, outlier looms, savings) switch on automatically once measured data is imported or connected." />
                <CardBody>
                  <ul className="list-disc space-y-1.5 pl-5 text-sm text-ink-2">{d.requirements.map((r: string) => <li key={r}>{r}</li>)}</ul>
                  <EmptyState className="mt-4" title="No savings figures are shown" description="A savings or cost number needs measured consumption and a tariff. None is invented here." />
                </CardBody>
              </Card>
            )}
          </div>
        )}
      </QueryView>
    </>
  );
};

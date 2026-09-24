export type DataFrequency = 'SHIFT' | 'DAILY' | 'WEEKLY' | 'MONTHLY';

export interface StandardIdentifiers {
  date?: string;
  timestamp?: string;
  shift?: string;
  unit_id?: string;
  department_id?: string;
  section_id?: string;
  process_id?: string;
  machine_type_id?: string;
  machine_id?: string;
  product_id?: string;
  batch_id?: string;
  order_id?: string;
  employee_id?: string;
}

export interface RawVsDerived {
  raw_target: number;
  raw_actual: number;
  derived_production_loss: number;
  derived_achievement_percentage: number;
}

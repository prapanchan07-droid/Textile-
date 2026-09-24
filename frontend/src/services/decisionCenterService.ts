import { DecisionCenterData } from '../types/decisionCenter';
import { TimePeriod, ComparisonPeriod } from '../types/overview';

export const decisionCenterService = {
  async getDecisionCenter(
    period: TimePeriod = 'TODAY',
    comparison: ComparisonPeriod = 'PREVIOUS_DAY',
    unit: string = 'All Units',
    userRole: string = 'SUPER_ADMIN',
    sectionAccess: string = 'ALL'
  ): Promise<DecisionCenterData> {
    const params = new URLSearchParams({
      period,
      comparison,
      unit,
      user_role: userRole,
      section_access: sectionAccess,
    });

    try {
      const response = await fetch(`/api/v1/decision-center?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const json = await response.json();
      if (!json.success || !json.data) {
        throw new Error(json.error?.message || 'Failed to fetch Decision Center data');
      }
      return json.data;
    } catch (err) {
      console.warn('Backend API unavailable, using fallback Decision Center data:', err);
      return this.getFallbackData(period, unit);
    }
  },

  getFallbackData(period: TimePeriod, unit: string): DecisionCenterData {
    let multiplier = 1.0;
    let subHighlight = 'Short by 2,380 kg';
    let targetKg = 37000;
    let actualKg = 34620;
    let gapKg = -2380;

    if (period === 'THIS_WEEK') {
      multiplier = 7.0;
      subHighlight = 'Short by 16,660 kg (Week)';
      targetKg = 259000;
      actualKg = 242340;
      gapKg = -16660;
    } else if (period === 'THIS_MONTH') {
      multiplier = 30.0;
      subHighlight = 'Short by 71,400 kg (Month)';
      targetKg = 1110000;
      actualKg = 1038600;
      gapKg = -71400;
    } else if (period === 'SHIFT') {
      multiplier = 0.33;
      subHighlight = 'Short by 793 kg (Shift)';
      targetKg = 12333;
      actualKg = 11540;
      gapKg = -793;
    }

    return {
      company_name: 'Ashok Textiles',
      selected_unit: unit,
      selected_period: period,
      user_role: 'SUPER_ADMIN',
      top_priority: {
        priority_level: 'HIGH',
        badge_label: '🔴 HIGH PRIORITY',
        title: 'Production is below target',
        sub_highlight: subHighlight,
        main_contributor: 'Machine downtime',
        most_affected_machine_type: 'Vortex',
        most_affected_machine_id: 'V-09',
        actual_kg: actualKg,
        target_kg: targetKg,
        gap_kg: gapKg,
        target_tab: 'production',
      },
      why_contributors: [
        { category: 'Machine Downtime', percentage: 47.0, status_color: 'RED', detail_text: '47% of total production gap attributable to unscheduled stops' },
        { category: 'Efficiency Loss', percentage: 30.0, status_color: 'ORANGE', detail_text: '30% due to speed drops and yarn breakage delays' },
        { category: 'Power Events', percentage: 12.0, status_color: 'YELLOW', detail_text: '12% linked to brief voltage fluctuations during shift 2' },
      ],
      where_location: {
        primary_machine_id: 'V-09',
        primary_machine_type: 'Vortex Spinning',
        primary_section: 'Spinning Unit 1',
        production_loss_kg: -680.0 * (multiplier < 5 ? multiplier : 1.0),
        efficiency_pct: 84.2,
        downtime_minutes: 240,
        status: '🔴 Critical',
        secondary_machines: [
          { machine_id: 'V-05', machine_type: 'Vortex', loss_kg: -420.0, status_color: 'ORANGE' },
          { machine_id: 'SMX-03', machine_type: 'Airjet Spinning', loss_kg: -290.0, status_color: 'ORANGE' },
        ],
      },
      recommended_actions: [
        { id: 'rec-1', step_number: 1, action_text: 'Investigate repeated downtime on V-09', button_label: 'View Machine', target_tab: 'machines', target_id: 'V-09' },
        { id: 'rec-2', step_number: 2, action_text: 'Check power fluctuation events during affected shifts', button_label: 'View Power', target_tab: 'overview', target_id: 'power-events' },
        { id: 'rec-3', step_number: 3, action_text: 'Review recent maintenance history of V-09', button_label: 'View Maintenance', target_tab: 'machines', target_id: 'maintenance-v09' },
      ],
      if_continues: {
        current_daily_gap_kg: -2380,
        projected_7d_gap_kg: -16660,
        projected_30d_gap_kg: -71400,
        label: 'Estimated production impact',
        disclaimer_note: 'Projection assumes the current daily gap continues.',
      },
      other_issues: [
        { id: 'issue-1', status_icon: '🟠', category: 'Manpower shortage', location_or_area: 'Spinning Department', impact_detail: '-30 workers', target_tab: 'manpower' },
        { id: 'issue-2', status_icon: '🟠', category: 'Energy consumption', location_or_area: 'Factory Power Grid', impact_detail: 'Higher than normal (+8%)', target_tab: 'overview' },
        { id: 'issue-3', status_icon: '🟡', category: 'Quality', location_or_area: 'Yarn Quality Lab', impact_detail: 'Thick places increasing', target_tab: 'manpower' },
        { id: 'issue-4', status_icon: '🟠', category: 'Accounts Receivable', location_or_area: 'Finance & Sales', impact_detail: '2 Accounts Overdue >60 days (₹14.5 Lakh)', target_tab: 'revenue' },
      ],
      action_tracker: [
        { id: 'act-101', issue: 'V-09 downtime', action: 'Check motor + power events', owner: 'Maintenance Manager', status: 'OPEN', status_badge: '🔴 OPEN', created_date: '2026-09-23' },
        { id: 'act-102', issue: 'Power fluctuation', action: 'Inspect affected machines', owner: 'Electrical Team', status: 'IN_PROGRESS', status_badge: '🟠 IN PROGRESS', created_date: '2026-09-22' },
        { id: 'act-103', issue: 'Spinning shift 2 absenteeism', action: 'Deploy pool contract workers', owner: 'HR & Manpower Head', status: 'COMPLETED', status_badge: '🟢 COMPLETED', created_date: '2026-09-21' },
      ],
      ai_insight: {
        summary_paragraph: "Today's production is 2,380 kg below target. The largest observed contributor is machine downtime, with V-09 showing the highest individual loss and downtime. Repeated power events coincided with the affected operational period.",
        recommended_focus: "Recommended focus: investigate V-09 downtime and related power events.",
        evidence_confidence: "HIGH",
        facts: [
          "Actual production achieved: 34,620 kg vs 37,000 kg target (-6.4%).",
          "Machine V-09 logged 240 minutes of unscheduled downtime (-680 kg loss).",
          "Voltage trip events registered at 14:15 and 16:40 during Shift 2.",
        ],
        projections: [
          "Unmitigated daily gap of 2,380 kg leads to an estimated 16,660 kg gap over 7 days.",
        ],
      },
    };
  },
};

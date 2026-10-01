/** Maps the backend's legacy `target_tab` ids (and optional machine id) onto routes. */
export function routeFor(targetTab?: string, targetId?: string, hint = ''): string {
  const machine = targetId && /^[A-Z]+-\d+/i.test(targetId) ? targetId : undefined;
  switch (targetTab) {
    case 'production':
      return '/production';
    case 'machines':
    case 'machine_comparison':
      return machine ? `/assets?machine=${encodeURIComponent(machine)}` : '/assets';
    case 'manpower':
      // The old page mixed people and quality; route by what the issue is about.
      return /quality|thick|neps|yarn|lab/i.test(hint) ? '/quality' : '/workforce';
    case 'revenue':
      return '/commercial';
    case 'decision':
      return '/actions';
    default:
      return '/';
  }
}

export type Role = 'OWNER' | 'WEAVING_MANAGER' | 'SHIFT_SUPERVISOR' | 'MAINTENANCE' | 'QUALITY';

export type WeavingSection =
  | 'owner' | 'command' | 'cockpit' | 'maintenance' | 'quality' | 'production' | 'stoppages' | 'machines' | 'workforce' | 'handover' | 'orders' | 'scheduler' | 'insights' | 'compare' | 'actions';

export interface AuthUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  role_label: string;
  /** Sections this user may open; the first is their landing page. */
  sections: WeavingSection[];
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface DemoAccount {
  username: string;
  role: Role;
  role_label: string;
  full_name: string;
}

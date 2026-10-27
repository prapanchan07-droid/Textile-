/** Only one role for now; more are added later. */
export type Role = 'ADMIN';

export interface AuthUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  role_label: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

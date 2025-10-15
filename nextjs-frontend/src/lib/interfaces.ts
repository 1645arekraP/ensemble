export interface User {
  id: string;
  username: string;
  email: string;
}

export interface LoginResponse {
  access: string; // The backend now ONLY sends the access token in the body
  user: User;
}

// Define the shape of the login error response
export interface LoginError {
  detail: string;
}

export interface NewUserData {
  username: string;
  email: string;
  password?: string; // Password might be optional if set on the backend
  first_name: string;
  last_name: string;
  role: 'student' | 'teacher' | 'school_admin';
  school: string;
}
import { supabase } from "./supabase";

// Send OTP to email
export async function sendOtp(email) {
  const { error } = await supabase.auth.signInWithOtp({
    email: email.trim(),
    options: {
      shouldCreateUser: true,
    },
  });

  if (error) {
    throw error;
  }

  return true;
}

// Verify OTP
export async function verifyOtp(email, token) {
  const { data, error } = await supabase.auth.verifyOtp({
    email: email.trim(),
    token: token.trim(),
    type: "email",
  });

  if (error) {
    throw error;
  }

  return data;
}

// Logout
export async function logout() {
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}
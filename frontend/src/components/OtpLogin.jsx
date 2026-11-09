
import { useState } from "react";
import { supabase } from "../services/supabase";

export default function OtpLogin({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleLogin(event) {
    event.preventDefault();

    try {
      setLoading(true);
      setMessage("");

      const { data, error } =
        await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

      if (error) {
        throw error;
      }

      if (!data.session) {
        throw new Error("Login session could not be created.");
      }

      await onLogin(data.session);

    } catch (error) {
      setMessage(error.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-container">
      <form className="login-card" onSubmit={handleLogin}>
        <h2>Accountant Login</h2>

        <p>Sign in using your authorised account.</p>

        <label>Username (email address)</label>
        <input
          type="email"
          placeholder="Enter your username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="username"
          required
        />

        <label>Password</label>
        <input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        {message && (
          <p className="role-login-error">{message}</p>
        )}

        <button
          type="submit"
          disabled={loading || !email.trim() || !password}
        >
          {loading ? "Signing in..." : "Login"}
        </button>
      </form>
    </main>
  );
}

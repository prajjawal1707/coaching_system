import { useState } from "react";
import { sendOtp, verifyOtp } from "../services/auth";

export default function OtpLogin({ onLogin }) {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSendOtp() {
    try {
      setLoading(true);
      setMessage("");

      await sendOtp(email);

      setOtpSent(true);
      setMessage("OTP sent. Check your email.");
    } catch (error) {
      setMessage(error.message || "Could not send OTP.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp() {
    try {
      setLoading(true);
      setMessage("");

      const data = await verifyOtp(email, otp);

      onLogin(data.session);
    } catch (error) {
      setMessage(error.message || "Invalid OTP.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>FeeFlow</h2>
        <p>Sign in to view your fee details</p>

        <label>Email address</label>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={otpSent}
        />

        {!otpSent ? (
          <button
            onClick={handleSendOtp}
            disabled={loading || !email.trim()}
          >
            {loading ? "Sending..." : "Send OTP"}
          </button>
        ) : (
          <>
            <label>Enter OTP</label>
            <input
              type="text"
              inputMode="numeric"
              placeholder="Enter the OTP from your email"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />

            <button
              onClick={handleVerifyOtp}
              disabled={loading || !otp.trim()}
            >
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
          </>
        )}

        {message && <p>{message}</p>}
      </div>
    </div>
  );
}
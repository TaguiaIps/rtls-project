import { useState, type InputHTMLAttributes, type ReactNode } from "react";
import {
  IconAlertCircle,
  IconCheckCircle,
  IconEye,
  IconEyeOff,
  IconInfo
} from "./Icons";

export type FeedbackTone = "info" | "success" | "warning" | "error";

export function FormMessage({
  children,
  tone = "info"
}: {
  children: ReactNode;
  tone?: FeedbackTone;
}) {
  const Icon = {
    info: IconInfo,
    success: IconCheckCircle,
    warning: IconAlertCircle,
    error: IconAlertCircle
  }[tone];

  return (
    <div className={`form-feedback form-feedback--${tone}`}>
      <Icon className="form-feedback__icon" />
      <span className="form-feedback__text">{children}</span>
    </div>
  );
}

export function CommandInput({
  label,
  error,
  ...props
}: {
  label: string;
  error?: string | null;
} & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="command-field">
      <label className="command-field__label">
        <span>{label}</span>
        <input className="command-field__input" {...props} />
      </label>
      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
    </div>
  );
}

export function PasswordInput({
  label,
  error,
  ...props
}: {
  label: string;
  error?: string | null;
} & InputHTMLAttributes<HTMLInputElement>) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="command-field">
      <label className="command-field__label">
        <span>{label}</span>
        <div className="command-field__wrapper">
          <input
            className="command-field__input command-field__input--password"
            {...props}
            type={visible ? "text" : "password"}
          />
          <button
            className="command-field__toggle"
            onClick={() => setVisible(!visible)}
            type="button"
            title={visible ? "Hide password" : "Show password"}
          >
            {visible ? <IconEyeOff /> : <IconEye />}
          </button>
        </div>
      </label>
      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
    </div>
  );
}

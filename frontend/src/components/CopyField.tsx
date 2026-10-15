import { useId, useRef, useState } from 'react';

interface CopyFieldProps {
  label: string;
  value: string;
  hint?: string;
}

export default function CopyField({ label, value, hint }: CopyFieldProps) {
  const [copied, setCopied] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const id = useId();

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      input.current?.select();
    }
  }

  return (
    <div className="copy-field">
      <label htmlFor={id}>{label}</label>
      <div className="copy-row">
        <input id={id} ref={input} readOnly value={value} onFocus={(e) => e.target.select()} />
        <button type="button" className="button secondary" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}

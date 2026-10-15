import { useState } from 'react';

export default function CopyField({ label, value, hint }) {
  const [copied, setCopied] = useState(false);
  const id = `copy-${label.toLowerCase().replace(/\W+/g, '-')}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      document.getElementById(id)?.select();
    }
  }

  return (
    <div className="copy-field">
      <label htmlFor={id}>{label}</label>
      <div className="copy-row">
        <input id={id} readOnly value={value} onFocus={(e) => e.target.select()} />
        <button type="button" className="button secondary" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}

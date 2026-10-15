import { useState } from 'react';
import { Link } from 'react-router-dom';
import CopyField from '../components/CopyField';
import ErrorMessage from '../components/ErrorMessage';
import { api } from '../lib/api';
import { formatDateTime } from '../lib/time';

const MIN_OPTIONS = 2;
const MAX_OPTIONS = 6;
const MIN_MINUTES = 15;
const MAX_MINUTES = 15 * 24 * 60;

const EXPIRY_PRESETS = [
  { value: '60', label: '1 hour' },
  { value: '1440', label: '1 day' },
  { value: '10080', label: '1 week' },
  { value: 'custom', label: 'Custom' },
];
const CUSTOM_UNITS = { minutes: 1, hours: 60, days: 1440 };

const VOTE_CONTROLS = [
  { value: 'one_per_browser', label: 'One per browser', hint: 'Light limit. A new browser can vote again.' },
  { value: 'one_per_ip', label: 'One per network', hint: 'Stricter. People sharing Wi-Fi get one vote.' },
  { value: 'open', label: 'Unlimited', hint: 'Anyone can vote as often as they like.' },
];
const VISIBILITIES = [
  { value: 'live', label: 'Live', hint: 'Everyone sees results as votes come in.' },
  { value: 'after_voting', label: 'After voting', hint: 'Voters see results once they vote.' },
  { value: 'private', label: 'Private', hint: 'Only you, with the admin link.' },
];

function expiryMinutes({ expiry, customAmount, customUnit }) {
  if (expiry !== 'custom') return Number(expiry);
  return Math.round(Number(customAmount) * CUSTOM_UNITS[customUnit]);
}

function validate(form) {
  const options = form.options.map((o) => o.trim());
  if (!form.question.trim()) return 'Enter a question.';
  if (options.some((o) => !o)) return 'Fill in every option, or remove the empty ones.';
  if (new Set(options.map((o) => o.toLowerCase())).size !== options.length) {
    return 'Each option must be different.';
  }
  const minutes = expiryMinutes(form);
  if (!Number.isFinite(minutes) || minutes < MIN_MINUTES || minutes > MAX_MINUTES) {
    return 'Polls can run from 15 minutes to 15 days.';
  }
  return null;
}

const INITIAL_FORM = {
  question: '',
  options: ['', ''],
  expiry: '1440',
  customAmount: '2',
  customUnit: 'hours',
  voteControl: 'one_per_browser',
  visibility: 'live',
};

export default function CreatePollPage() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState(null);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const setOption = (index, value) =>
    setForm((f) => ({ ...f, options: f.options.map((o, i) => (i === index ? value : o)) }));
  const addOption = () => setForm((f) => ({ ...f, options: [...f.options, ''] }));
  const removeOption = (index) =>
    setForm((f) => ({ ...f, options: f.options.filter((_, i) => i !== index) }));

  async function submit(e) {
    e.preventDefault();
    const problem = validate(form);
    if (problem) {
      setError(new Error(problem));
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const poll = await api.createPoll({
        question: form.question.trim(),
        options: form.options.map((o) => o.trim()),
        expires_in_minutes: expiryMinutes(form),
        vote_control: form.voteControl,
        results_visibility: form.visibility,
      });
      setCreated(poll);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  if (created) {
    return (
      <div className="created">
        <h1>Your poll is live</h1>
        <p className="muted">Voting closes {formatDateTime(created.expires_at)}.</p>
        <CopyField label="Share link" value={created.share_url} hint="Send this to voters." />
        <CopyField
          label="Admin link"
          value={created.admin_url}
          hint="Keep this private. It's the only way to manage the poll, and it can't be recovered."
        />
        <div className="actions">
          <Link to={`/p/${created.poll_id}`} className="button">
            Open poll
          </Link>
          <button
            type="button"
            className="button secondary"
            onClick={() => {
              setCreated(null);
              setForm(INITIAL_FORM);
            }}
          >
            Create another
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate>
      <h1>Create a poll</h1>

      <div className="field">
        <label htmlFor="question">Question</label>
        <input
          id="question"
          value={form.question}
          onChange={update('question')}
          maxLength={200}
          placeholder="What should we have for lunch?"
          autoFocus
        />
      </div>

      <fieldset className="field">
        <legend>Options</legend>
        {form.options.map((option, i) => (
          <div className="option-row" key={i}>
            <input
              aria-label={`Option ${i + 1}`}
              value={option}
              onChange={(e) => setOption(i, e.target.value)}
              maxLength={100}
              placeholder={`Option ${i + 1}`}
            />
            {form.options.length > MIN_OPTIONS && (
              <button
                type="button"
                className="icon-button"
                aria-label={`Remove option ${i + 1}`}
                onClick={() => removeOption(i)}
              >
                ×
              </button>
            )}
          </div>
        ))}
        {form.options.length < MAX_OPTIONS && (
          <button type="button" className="link-button" onClick={addOption}>
            + Add option
          </button>
        )}
      </fieldset>

      <fieldset className="field">
        <legend>Closes after</legend>
        <div className="segmented">
          {EXPIRY_PRESETS.map((preset) => (
            <label key={preset.value} className={form.expiry === preset.value ? 'selected' : ''}>
              <input
                type="radio"
                name="expiry"
                value={preset.value}
                checked={form.expiry === preset.value}
                onChange={update('expiry')}
              />
              {preset.label}
            </label>
          ))}
        </div>
        {form.expiry === 'custom' && (
          <div className="custom-expiry">
            <input
              type="number"
              aria-label="Custom duration"
              min="1"
              value={form.customAmount}
              onChange={update('customAmount')}
            />
            <select aria-label="Custom duration unit" value={form.customUnit} onChange={update('customUnit')}>
              {Object.keys(CUSTOM_UNITS).map((unit) => (
                <option key={unit} value={unit}>
                  {unit}
                </option>
              ))}
            </select>
            <span className="hint">15 minutes to 15 days</span>
          </div>
        )}
      </fieldset>

      <ChoiceGroup
        legend="Who can vote"
        name="voteControl"
        choices={VOTE_CONTROLS}
        value={form.voteControl}
        onChange={update('voteControl')}
      />
      <ChoiceGroup
        legend="Who sees results"
        name="visibility"
        choices={VISIBILITIES}
        value={form.visibility}
        onChange={update('visibility')}
      />

      <ErrorMessage error={error} />
      <button type="submit" className="button primary wide" disabled={submitting}>
        {submitting ? 'Creating…' : 'Create poll'}
      </button>
    </form>
  );
}

function ChoiceGroup({ legend, name, choices, value, onChange }) {
  return (
    <fieldset className="field">
      <legend>{legend}</legend>
      <div className="choices">
        {choices.map((choice) => (
          <label key={choice.value} className={`choice ${value === choice.value ? 'selected' : ''}`}>
            <input
              type="radio"
              name={name}
              value={choice.value}
              checked={value === choice.value}
              onChange={onChange}
            />
            <span>
              <strong>{choice.label}</strong>
              <span className="hint">{choice.hint}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

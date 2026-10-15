export default function Results({ options, results }) {
  const { total_votes: total, counts } = results;
  const top = Math.max(...counts);

  return (
    <div className="results" aria-live="polite">
      <ul>
        {options.map((option, i) => {
          const count = counts[i] ?? 0;
          const percent = total ? Math.round((count / total) * 100) : 0;
          const leading = total > 0 && count === top;
          return (
            <li key={option} className={leading ? 'leading' : undefined}>
              <div className="result-label">
                <span>{option}</span>
                <span className="result-figure">
                  {percent}% <span className="muted">({count})</span>
                </span>
              </div>
              <div
                className="bar"
                role="meter"
                aria-label={option}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percent}
              >
                <div className="bar-fill" style={{ width: `${percent}%` }} />
              </div>
            </li>
          );
        })}
      </ul>
      <p className="muted total">
        {total} {total === 1 ? 'vote' : 'votes'}
      </p>
    </div>
  );
}

export default function ErrorMessage({ error }: { error: Error | null }) {
  if (!error) return null;
  return (
    <p className="error" role="alert">
      {error.message}
    </p>
  );
}

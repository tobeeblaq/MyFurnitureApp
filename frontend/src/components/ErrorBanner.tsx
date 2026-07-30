export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <ul className="flash">
      <li>{message}</li>
    </ul>
  );
}

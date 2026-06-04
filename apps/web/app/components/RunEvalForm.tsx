import { runEvalAction } from "../actions";

export function RunEvalForm() {
  return (
    <form action={runEvalAction}>
      <button type="submit">Run eval in mock mode</button>
    </form>
  );
}

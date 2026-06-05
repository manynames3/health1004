import { DocumentBrowser } from "../components/DocumentBrowser";
import { QueryWorkspace } from "../components/QueryWorkspace";

export default function Home() {
  return (
    <main className="app-shell">
      <QueryWorkspace />
      <DocumentBrowser />
    </main>
  );
}

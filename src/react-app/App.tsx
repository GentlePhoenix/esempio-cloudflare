import { useState } from "react";
import "./App.css";

function App() {
  const [questionCount, setQuestionCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkDatabase = async () => {
    try {
      const res = await fetch("/api/questions/count");
      if (!res.ok) throw new Error("Errore nella risposta del server");
      const data = (await res.json()) as { count?: number; error?: string };
      if (data.error) {
        setError(data.error);
      } else {
        setQuestionCount(data.count ?? 0);
        setError(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore sconosciuto");
    }
  };

  return (
    <div className="app">
      <h1>Quiz Tecnico Sicurezza</h1>
      <p>Applicazione in fase di sviluppo.</p>
      <div className="card">
        <button onClick={checkDatabase}>Verifica connessione database</button>
        {questionCount !== null && (
          <p>Domande nel database: {questionCount}</p>
        )}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}

export default App;

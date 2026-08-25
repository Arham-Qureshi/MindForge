import { useState } from "react";
import MainLayout from "./components/layout/MainLayout";
import Dropzone from "./components/common/Dropzone";
import ViewSwitcher from "./components/common/ViewSwitcher";
import type { EngineResponse } from "./types/api.types";

function App() {
  const [sessionData, setSessionData] = useState<EngineResponse | null>(null);

  const handleReset = () => {
    setSessionData(null);
  };

  return (
    <MainLayout>
      {!sessionData ? (
        <Dropzone onProcessed={setSessionData} onReset={handleReset} />
      ) : (
        <ViewSwitcher data={sessionData} onReset={handleReset} />
      )}
    </MainLayout>
  );
}

export default App;

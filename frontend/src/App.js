import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Chatbot from "./components/chatbot";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <div
          style={{
            width: "calc(100vw - 32px)",
            height: "calc(100vh - 32px)",
            position: "fixed",
            top: 0,
            padding: 16,
            paddingTop: 0,
          }}
        >
          <Routes>
            <Route exact path="/" element={<Chatbot />} />
            <Route path="/" element={<Navigate to="/chatbot" />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;

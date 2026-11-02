import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import "./index.css";
import { loadConfig } from "./lib/config";
import { loadIdentity } from "./lib/api";
import { useStore } from "./lib/store";
import { GameRoute } from "./features/game/GameRoute";
import { Lobby } from "./features/lobby/Lobby";

const router = createBrowserRouter([
  { path: "/", element: <Lobby /> },
  { path: "/g/:gameId", element: <GameRoute /> },
]);

void loadConfig().then(() => {
  useStore.getState().setIdentity(loadIdentity());
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  );
});

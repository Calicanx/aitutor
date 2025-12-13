/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
// @ts-ignore
import "./package/perseus/testing/perseus-init.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import ComingSoonGuard from "./components/coming-soon/ComingSoonGuard";

const LoginPage = lazy(() => import("./components/auth/LoginPage"));
const LandingPageWrapper = lazy(() => import("./components/landing/LandingPageWrapper"));

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement,
);

const queryClient = new QueryClient();

// Suppress Perseus library warnings (known issues in the library)
if (import.meta.env.DEV) {
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    // Filter out known Perseus warnings
    const message = args[0]?.toString() || '';
    if (
      message.includes('findDOMNode is deprecated') ||
      message.includes('Multiple versions of @khanacademy') ||
      message.includes('Blocked aria-hidden')
    ) {
      return; // Suppress these warnings
    }
    originalWarn.apply(console, args);
  };
}

// Component to decide between landing page and app
const LandingPageOrApp: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#FFFDF5'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPageWrapper />;
  }

  return <App />;
};

root.render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <AuthProvider>
        <ComingSoonGuard>
          <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
            <Switch>
              <Route path="/app/auth/setup" component={LoginPage} />
              <Route path="/app/login" component={LoginPage} />
              <Route path="/app" exact component={LandingPageOrApp} />
              <Route path="/app" component={App} />
            </Switch>
          </Suspense>
        </ComingSoonGuard>
      </AuthProvider>
    </BrowserRouter>
  </QueryClientProvider>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(console.log);

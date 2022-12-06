import React from 'react';
import {
  Router,
  Route,
  Routes,
} from '@reach/router';
import ProtectedRoute from "./ProtectedRoute";
import Login from "./Login"
import Dashboard from "./Dashboard"

export default function App() {
  return (
    <Router>
      <Routes>
        <ProtectedRoute exact path="/admin">
          <Dashboard />
        </ProtectedRoute>
        <Route exact path="/login" component={Login} />
      </Routes>
    </Router>
	)
}